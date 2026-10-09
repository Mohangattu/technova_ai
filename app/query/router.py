import json
import os

from dotenv import load_dotenv
from groq import Groq

from query_models import QueryRoute


load_dotenv()


class QueryRouter:

    def __init__(
        self,
        model_name="openai/gpt-oss-120b",
        max_retries=2,
    ):
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )

        self.model_name = model_name
        self.max_retries = max_retries

    SYSTEM_PROMPT = """
You are a query routing component for an enterprise RAG system.

Your job is to decide whether a user's query can be sent
directly to the retrieval system or whether it should first
be rewritten.

Choose:

DIRECT
- The query is already clear and specific.
- The query contains enough information for retrieval.
- The query uses terminology that can directly match the
  enterprise knowledge base.
- Minor conversational wording does not require rewriting.

REWRITE
- The query is vague, ambiguous, incomplete, or conversational.
- The query contains unclear references such as "it", "that",
  "this", or "the above".
- Important retrieval terms are missing.
- Rewriting can make the query more explicit and retrieval-friendly.

Rules:

1. Return only valid JSON.
2. The "route" field must be either "DIRECT" or "REWRITE".
3. "retrieval_query" must always be a non-empty string.
4. If the route is DIRECT, retrieval_query must be exactly
   the original user query.
5. If the route is REWRITE, retrieval_query should contain
   the improved retrieval-oriented query.
6. Do not answer the user's question.
7. Do not invent information that is not present in the query.

Output format:

{
    "route": "DIRECT" or "REWRITE",
    "retrieval_query": "..."
}
"""

    RETRY_SUFFIX = """
Your previous response was invalid.

Return ONLY valid JSON using exactly this structure:

{
    "route": "DIRECT" or "REWRITE",
    "retrieval_query": "..."
}

Do not include markdown.
Do not include explanations.
"""

    def route(self, query: str) -> QueryRoute:

        if not isinstance(query, str):
            raise TypeError("query must be a string")

        query = query.strip()

        if not query:
            raise ValueError("query cannot be empty")

        messages = [
            {
                "role": "system",
                "content": self.SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": query,
            },
        ]

        for attempt in range(self.max_retries + 1):

            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0,
                    response_format={
                        "type": "json_object"
                    },
                )

                raw_output = (
                    response.choices[0]
                    .message
                    .content
                )

                data = json.loads(raw_output)

                result = QueryRoute.model_validate(data)

                if result.route == "DIRECT":
                    result.retrieval_query = query

                if not result.retrieval_query.strip():
                    raise ValueError(
                        "retrieval_query cannot be empty"
                    )

                return result

            except Exception as error:

                if attempt >= self.max_retries:
                    raise RuntimeError(
                        "Query routing failed after "
                        f"{self.max_retries + 1} attempts"
                    ) from error

                messages.append(
                    {
                        "role": "assistant",
                        "content": (
                            raw_output
                            if "raw_output" in locals()
                            else ""
                        ),
                    }
                )

                messages.append(
                    {
                        "role": "user",
                        "content": self.RETRY_SUFFIX,
                    }
                )