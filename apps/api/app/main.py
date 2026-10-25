import hmac
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import Depends, FastAPI, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .agents import Agents
from .db import Base, Campaign, Launch, database
from .orchestration import build_workflow
from .schemas import CampaignBrief, Decision

logger = logging.getLogger(__name__)

def create_app(database_url=None, workflow=None):
    engine, sessions = database(database_url)
    api_key = os.getenv('API_KEY')
    if not api_key:
        raise ValueError('Set API_KEY before starting the API')
    graph = workflow if workflow is not None else build_workflow(Agents())

    @asynccontextmanager
    async def lifespan(app):
        Base.metadata.create_all(engine)
        yield
        engine.dispose()

    app = FastAPI(title='Agentic Marketing Orchestrator', version='0.1.0', lifespan=lifespan)

    def authorize(x_api_key: str = Header(default='')):
        if not hmac.compare_digest(x_api_key, api_key):
            raise HTTPException(401, 'Invalid API key')

    def session():
        with sessions() as db:
            yield db

    def get_campaign(db, campaign_id):
        campaign = db.get(Campaign, campaign_id)
        if campaign is None:
            raise HTTPException(404, 'Campaign not found')
        return campaign

    def event(campaign, action):
        campaign.events = [*campaign.events, {'action': action, 'at': datetime.now(timezone.utc).isoformat(), 'version': campaign.version}]

    def serialize(campaign):
        return {key: getattr(campaign, key) for key in ('id', 'title', 'audience', 'objective', 'status', 'version', 'approved_version', 'result', 'events', 'created_at')}

    protected = [Depends(authorize)]

    @app.get('/health')
    def health():
        return {'status': 'ok'}

    @app.get('/campaigns', dependencies=protected)
    def list_campaigns(db=Depends(session)):
        return [serialize(c) for c in db.scalars(select(Campaign).order_by(Campaign.created_at.desc()).limit(100))]

    @app.post('/campaigns', status_code=201, dependencies=protected)
    def create_campaign(brief: CampaignBrief, db=Depends(session)):
        campaign = Campaign(**brief.model_dump())
        db.add(campaign)
        db.flush()
        event(campaign, 'created')
        db.commit()
        return serialize(campaign)

    @app.get('/campaigns/{campaign_id}', dependencies=protected)
    def read_campaign(campaign_id: str, db=Depends(session)):
        return serialize(get_campaign(db, campaign_id))

    @app.post('/campaigns/{campaign_id}/run', dependencies=protected)
    def run_campaign(campaign_id: str, db=Depends(session)):
        # Lock a campaign for the duration of this synchronous workflow.
        # PostgreSQL serializes concurrent mutations; SQLite is local-dev only.
        campaign = db.scalar(select(Campaign).where(Campaign.id == campaign_id).with_for_update())
        if campaign is None:
            raise HTTPException(404, 'Campaign not found')
        if campaign.status in ('approved', 'launched'):
            raise HTTPException(409, 'Approved or launched campaigns cannot be regenerated')
        campaign.version += 1
        campaign.approved_version = None
        try:
            campaign.result = graph.invoke({'brief': {'title': campaign.title, 'audience': campaign.audience, 'objective': campaign.objective}, 'attempts': 0}, {'recursion_limit': 20})
            campaign.status = campaign.result['status']
            event(campaign, 'workflow_completed')
        except Exception:
            logger.exception('Workflow failed for campaign %s', campaign_id)
            campaign.status = 'failed'
            campaign.result = {'error': 'Workflow failed. Check server logs, then retry.'}
            event(campaign, 'workflow_failed')
        db.commit()
        return serialize(campaign)

    @app.post('/campaigns/{campaign_id}/decision', dependencies=protected)
    def decide(campaign_id: str, decision: Decision, db=Depends(session)):
        campaign = db.scalar(select(Campaign).where(Campaign.id == campaign_id).with_for_update())
        if campaign is None:
            raise HTTPException(404, 'Campaign not found')
        if campaign.status != 'awaiting_approval' or campaign.version != decision.version:
            raise HTTPException(409, 'Decision must match the current draft awaiting approval')
        campaign.status = 'approved' if decision.decision == 'approve' else 'rejected'
        campaign.approved_version = campaign.version if decision.decision == 'approve' else None
        event(campaign, campaign.status)
        db.commit()
        return serialize(campaign)

    @app.post('/campaigns/{campaign_id}/launch', dependencies=protected)
    def launch(campaign_id: str, db=Depends(session)):
        campaign = db.scalar(select(Campaign).where(Campaign.id == campaign_id).with_for_update())
        if campaign is None:
            raise HTTPException(404, 'Campaign not found')
        existing = db.get(Launch, campaign_id)
        if existing:
            return {'mode': 'mock', 'receipt': existing.receipt, 'version': existing.content_version}
        if campaign.status != 'approved' or campaign.approved_version != campaign.version:
            raise HTTPException(409, 'Current content requires approval before launch')
        receipt = 'mock-' + str(uuid4())
        db.add(Launch(campaign_id=campaign.id, content_version=campaign.version, receipt=receipt))
        campaign.status = 'launched'
        event(campaign, 'mock_launched')
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = db.get(Launch, campaign_id)
            if existing is None:
                raise
            receipt = existing.receipt
        return {'mode': 'mock', 'receipt': receipt, 'version': campaign.version}

    return app
