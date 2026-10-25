import os
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import JSON, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

class Base(DeclarativeBase):
    pass

class Campaign(Base):
    __tablename__ = 'campaigns'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(120))
    audience: Mapped[str] = mapped_column(String(300))
    objective: Mapped[str] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(String(40), default='created')
    version: Mapped[int] = mapped_column(Integer, default=0)
    approved_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    events: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[str] = mapped_column(String(40), default=lambda: datetime.now(timezone.utc).isoformat())

class Launch(Base):
    __tablename__ = 'mock_launches'
    # A unique campaign ID guarantees one mock launch per campaign.
    campaign_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    content_version: Mapped[int] = mapped_column(Integer)
    receipt: Mapped[str] = mapped_column(String(100))

def database(url=None):
    url = url or os.getenv('DATABASE_URL', 'sqlite:///./campaigns.db')
    engine = create_engine(url, connect_args={'check_same_thread': False} if url.startswith('sqlite') else {}, pool_pre_ping=True)
    return engine, sessionmaker(engine, expire_on_commit=False)
