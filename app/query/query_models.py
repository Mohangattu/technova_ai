from typing import Literal

from pydantic import BaseModel, Field


class QueryRoute(BaseModel):
    route: Literal["DIRECT", "REWRITE"] = Field(
        description="Whether the original query should be used directly or rewritten."
    )

    retrieval_query: str = Field(
        description="The query that should be sent to the retrieval pipeline."
    )