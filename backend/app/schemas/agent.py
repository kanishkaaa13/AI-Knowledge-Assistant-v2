from __future__ import annotations

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
