import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


class QueryRewriter:

    def __init__(
        self,
        model_name="openai/gpt-oss-120b",
        max_retries=2,
    ):
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url=os.getenv("GROQ_BASE_URL") or None,
            timeout=30.0,
            max_retries=0,
        )

        self.model_name = model_name
        self.max_retries = max_retries

    SYSTEM_PROMPT = """
You are a query rewriting component for an enterprise RAG system.

Your task is to rewrite the user's query into a clear,
specific, retrieval-friendly query.

Rules:

1. Preserve the original meaning of the query.
2. Do not answer the query.
3. Do not add facts that are not present in the query.
4. Remove unnecessary conversational wording.
5. Make implicit retrieval intent explicit when possible.
6. Preserve important technical terminology.
7. Resolve vague wording only when the intended meaning is
   clear from the query itself.
8. If the query is already sufficiently clear, return it
   with minimal or no changes.
9. Return ONLY the rewritten query.
10. Do not use markdown.
11. Do not provide explanations.
"""

    RETRY_SUFFIX = """
Rewrite the query again.

Return ONLY the rewritten query.
Do not provide explanations or markdown.
"""

    def rewrite(self, query: str) -> str:

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
                )

                rewritten_query = (
                    response.choices[0]
                    .message
                    .content
                    .strip()
                )

                if not rewritten_query:
                    raise ValueError(
                        "Rewriter returned an empty query"
                    )

                return rewritten_query

            except Exception as error:

                if attempt >= self.max_retries:
                    raise RuntimeError(
                        "Query rewriting failed after "
                        f"{self.max_retries + 1} attempts"
                    ) from error

                messages.append(
                    {
                        "role": "user",
                        "content": self.RETRY_SUFFIX,
                    }
                )
