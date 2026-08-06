from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import get_current_user
from app.core.rate_limit import apply_rate_limit
from app.core.sanitize import ensure_present, sanitize_text
from app.models.user import User
from app.schemas.agent import AgentChatRequest, AgentChatResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=AgentChatResponse, summary="Agent chat — ReAct reasoning with tools")
async def agent_chat(
    payload: AgentChatRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> AgentChatResponse:
    """Run a user query through the LangGraph ReAct agent and return the answer.

    The agent autonomously chooses among:
    - **search_documents** — semantic ChromaDB retrieval
    - **summarize_document** — document summarization
    - **answer_general_knowledge** — direct LLM response

    ``tool_used`` reports the **first** (primary) tool the agent invoked.
    If no tool was called, ``tool_used`` is an empty string.
    """
    await apply_rate_limit(request, scope="agent-chat", limit=15, user_id=str(current_user.id))

    safe_query = ensure_present(
        sanitize_text(payload.query, max_length=4000),
        field_name="query",
    )

    try:
        # Late import avoids circular dependency at module-load time
        from app.agents.router_agent import run_agent

        # Run async agent call
        result = await run_agent(user_query=safe_query)
    except Exception as exc:
        logger.exception("Agent chat failed for user %s: %s", current_user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent chat execution failed. Check server logs for details.",
        ) from exc

    tools_called: list[str] = result.get("tools_called", [])

    return AgentChatResponse(
        answer=result.get("answer", ""),
        tool_used=tools_called[0] if tools_called else "",
    )
