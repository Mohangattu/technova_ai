import os
import json
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

class GroundingVerifier:

    def __init__(
        self,
        model_name="openai/gpt-oss-20b",
    ):
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url=os.getenv("GROQ_BASE_URL") or None,
            timeout=30.0,
            max_retries=0,
        )

        self.model_name = model_name

    def verify(
        self,
        question,
        answer,
        contexts,
    ):
        context_text = "\n\n".join(
            f"""
SOURCE {index}

{context.get("content", "")}
"""
            for index, context in enumerate(
                contexts,
                start=1,
            )
        )

        prompt = f"""
You are a strict grounding verifier for an
enterprise RAG system.

Your job is to determine whether every factual
claim in the generated answer is supported by
the retrieved context.

QUESTION:
{question}

GENERATED ANSWER:
{answer}

RETRIEVED CONTEXT:
{context_text}

Instructions:

1. Identify the factual claims in the answer.
2. Check each claim against the retrieved context.
3. A claim is SUPPORTED only if the context
   provides sufficient evidence for it.
4. Do not use outside knowledge.
5. If a claim is unsupported, mark it UNSUPPORTED.
6. If all factual claims are supported, the
   answer is GROUNDED.
7. Do not judge writing style.
8. Do not judge whether the answer is elegant.
9. Focus only on factual grounding.

Return ONLY valid JSON in this exact format:

{{
    "grounded": true,
    "claims": [
        {{
            "claim": "example claim",
            "supported": true,
            "source": "SOURCE 1"
        }}
    ],
    "reason": "Brief explanation"
}}
"""

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict factual grounding "
                        "verifier. Return only valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0,
        )

        content = response.choices[0].message.content

        try:
            result = json.loads(content)

        except json.JSONDecodeError:

            result = {
                "grounded": False,
                "claims": [],
                "reason": (
                    "Verifier returned invalid JSON."
                ),
            }

        return result
