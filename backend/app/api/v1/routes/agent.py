from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import get_current_user
from app.core.rate_limit import apply_rate_limit
from app.core.sanitize import ensure_present, sanitize_text
from app.models.user import User
from app.schemas.agent import AgentRunRequest, AgentRunResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/run", response_model=AgentRunResponse, summary="Run the LangGraph ReAct agent")
async def run_agent_endpoint(
    payload: AgentRunRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> AgentRunResponse:
    """Execute the LangGraph ReAct router agent with the user's query.

    The agent selects from three tools:
    - **search_documents** — semantic vector search over ChromaDB
    - **summarize_document** — summarize a document by ID
    - **answer_general_knowledge** — pass-through for LLM general knowledge

    Returns the final answer and a log of which tools were called.
    """
    await apply_rate_limit(request, scope="agent-run", limit=15, user_id=str(current_user.id))

    safe_query = ensure_present(
        sanitize_text(payload.query, max_length=4000),
        field_name="query",
    )

    try:
        # Import here to avoid circular import at module load time
        from app.agents.router_agent import run_agent

        # Run async agent call
        result = await run_agent(user_query=safe_query, user_id=str(current_user.id))
    except Exception as exc:
        logger.exception("Agent execution failed for user %s: %s", current_user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent execution failed. Check server logs for details.",
        ) from exc

    return AgentRunResponse(
        query=safe_query,
        answer=result.get("answer", ""),
        tools_called=result.get("tools_called", []),
        reasoning_steps=result.get("reasoning_steps", []),
    )
