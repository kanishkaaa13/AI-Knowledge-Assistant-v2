from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    """Request body for POST /api/v1/agent/run."""

    query: str = Field(min_length=1, max_length=4000, description="User query to run through the agent.")


class AgentRunResponse(BaseModel):
    """Response body for POST /api/v1/agent/run."""

    query: str
    answer: str
    tools_called: list[str] = Field(
        default_factory=list,
        description="Names of LangChain tools invoked by the agent during this run.",
    )
    reasoning_steps: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Detailed ReAct reasoning steps including tool calls and outputs.",
    )


class AgentChatRequest(BaseModel):
    """Request body for POST /api/v1/agent/chat."""

    query: str = Field(min_length=1, max_length=4000, description="User query for the agent chat endpoint.")


class AgentChatResponse(BaseModel):
    """Response body for POST /api/v1/agent/chat."""

    answer: str
    tool_used: str = Field(
        default="",
        description="Primary tool invoked by the agent (first tool called, or empty string if none).",
    )
