import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.orchestration import build_workflow, transient_failure
from app.agents import Agents
from app.schemas import Review

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('API_KEY', 'test-key')
    monkeypatch.setenv('LLM_PROVIDER', 'demo')
    with TestClient(create_app('sqlite:///' + str(tmp_path / 'test.db'))) as test:
        test.headers['X-API-Key'] = 'test-key'
        yield test

def campaign(client):
    response = client.post('/campaigns', json={'title': 'Business card', 'audience': 'Small businesses', 'objective': 'Explain expense tracking benefits'})
    assert response.status_code == 201
    return response.json()['id']

def test_complete_flow_and_duplicate_launch(client):
    cid = campaign(client)
    assert client.post(f'/campaigns/{cid}/launch').status_code == 409
    draft = client.post(f'/campaigns/{cid}/run').json()
    assert draft['status'] == 'awaiting_approval'
    assert client.post(f'/campaigns/{cid}/decision', json={'version': 99, 'decision': 'approve'}).status_code == 409
    assert client.post(f'/campaigns/{cid}/decision', json={'version': draft['version'], 'decision': 'approve'}).status_code == 200
    first = client.post(f'/campaigns/{cid}/launch').json()
    assert first == client.post(f'/campaigns/{cid}/launch').json()
    assert client.get(f'/campaigns/{cid}').json()['status'] == 'launched'
    assert client.post(f'/campaigns/{cid}/run').status_code == 409

def test_rejection_and_stale_approval(client):
    cid = campaign(client)
    client.post(f'/campaigns/{cid}/run')
    client.post(f'/campaigns/{cid}/decision', json={'version': 1, 'decision': 'reject'})
    assert client.post(f'/campaigns/{cid}/launch').status_code == 409
    assert client.post(f'/campaigns/{cid}/run').json()['version'] == 2
    assert client.post(f'/campaigns/{cid}/decision', json={'version': 1, 'decision': 'approve'}).status_code == 409

def test_auth_validation_and_missing_campaign(client):
    assert client.get('/campaigns', headers={'X-API-Key': 'wrong'}).status_code == 401
    assert client.post('/campaigns', json={'title': 'x'}).status_code == 422
    assert client.get('/campaigns/missing').status_code == 404

def test_persistence_across_restart(tmp_path, monkeypatch):
    monkeypatch.setenv('API_KEY', 'test-key')
    monkeypatch.setenv('LLM_PROVIDER', 'demo')
    url = 'sqlite:///' + str(tmp_path / 'restart.db')
    with TestClient(create_app(url)) as c:
        c.headers['X-API-Key'] = 'test-key'
        cid = campaign(c)
        c.post(f'/campaigns/{cid}/run')
    with TestClient(create_app(url)) as c:
        assert c.get(f'/campaigns/{cid}', headers={'X-API-Key': 'test-key'}).json()['status'] == 'awaiting_approval'

def test_bounded_conflicting_review():
    class RejectingAgents(Agents):
        def review(self, draft):
            return Review(passed=False, findings=['Unsupported claim'])
    result = build_workflow(RejectingAgents()).invoke({'brief': {'audience': 'Businesses'}, 'attempts': 0})
    assert result['attempts'] == 3
    assert result['status'] == 'needs_attention'

def test_transient_retry():
    class FlakyAgents(Agents):
        calls = 0
        def plan(self, brief):
            self.calls += 1
            if self.calls < 2:
                raise TimeoutError('simulated timeout')
            return super().plan(brief)
    agents = FlakyAgents()
    assert build_workflow(agents).invoke({'brief': {'audience': 'Businesses'}, 'attempts': 0})['status'] == 'awaiting_approval'
    assert agents.calls == 2
    assert not transient_failure(ValueError('bad output'))

def test_failed_run_can_be_retried(tmp_path, monkeypatch):
    monkeypatch.setenv('API_KEY', 'test-key')
    class BrokenGraph:
        def invoke(self, *args):
            raise RuntimeError('sensitive internal details')
    with TestClient(create_app('sqlite:///' + str(tmp_path / 'fail.db'), workflow=BrokenGraph())) as c:
        c.headers['X-API-Key'] = 'test-key'
        cid = campaign(c)
        result = c.post(f'/campaigns/{cid}/run').json()
        assert result['status'] == 'failed'
        assert 'sensitive' not in str(result)
