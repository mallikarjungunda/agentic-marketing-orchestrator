from typing import TypedDict
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy
from .agents import Agents

class WorkflowState(TypedDict, total=False):
    brief: dict
    plan: dict
    draft: dict
    review: dict
    attempts: int
    status: str

def transient_failure(error: Exception) -> bool:
    # Retry transport failures, 429 and server errors; never retry auth failures.
    import httpx
    if isinstance(error, (TimeoutError, ConnectionError, httpx.TransportError)):
        return True
    code = getattr(error, 'status_code', None)
    return code == 429 or (isinstance(code, int) and code >= 500)

def build_workflow(agents: Agents):
    def plan(state):
        return {'plan': agents.plan(state['brief']).model_dump()}

    def draft(state):
        findings = state.get('review', {}).get('findings', [])
        return {'draft': agents.draft(state['brief'], findings).model_dump(), 'attempts': state.get('attempts', 0) + 1}

    def review(state):
        result = agents.review(state['draft'])
        # Deterministic minimum checks take precedence over reviewer agreement.
        text = (state['draft']['subject'] + ' ' + state['draft']['body']).lower()
        findings = list(result.findings)
        if 'terms and eligibility apply' not in text:
            findings.append('Required disclosure is missing')
        if 'guaranteed approval' in text:
            findings.append('Unsupported guarantee')
        passed = result.passed and not findings
        return {'review': {'passed': passed, 'findings': findings}, 'status': 'awaiting_approval' if passed else 'needs_attention'}

    graph = StateGraph(WorkflowState)
    retry = RetryPolicy(initial_interval=0.2, backoff_factor=2, max_attempts=3, jitter=True, retry_on=transient_failure)
    for name, node in [('plan', plan), ('draft', draft), ('review', review)]:
        graph.add_node(name, node, retry_policy=retry)
    graph.add_edge(START, 'plan')
    graph.add_edge('plan', 'draft')
    graph.add_edge('draft', 'review')
    graph.add_conditional_edges('review', lambda s: 'draft' if not s['review']['passed'] and s['attempts'] < 3 else END)
    return graph.compile()
