import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
class LLMJudge:

    def __init__(
        self,
        model_name="openai/gpt-oss-120b",
    ):
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url=os.getenv("GROQ_BASE_URL") or None,
            timeout=30.0,
            max_retries=0,
        )

        self.model_name = model_name

    def evaluate(
        self,
        question,
        expected_answer,
        generated_answer,
        contexts,
    ):

        context_text = "\n\n".join(
            context.get("content", "")
            for context in contexts
        )

        prompt = f"""
You are evaluating an enterprise RAG system.

Evaluate the generated answer using ONLY the provided
question, expected answer, and retrieved context.

QUESTION:
{question}

EXPECTED ANSWER:
{expected_answer}

GENERATED ANSWER:
{generated_answer}

RETRIEVED CONTEXT:
{context_text}

Evaluate the answer on three dimensions.

1. CORRECTNESS
Does the generated answer contain the correct information
required to answer the question?

2. RELEVANCE
Does the answer directly address the question without
unnecessary information?

3. FAITHFULNESS
Are the claims in the generated answer supported by the
retrieved context?

Use a score from 1 to 5:

1 = Very poor
2 = Poor
3 = Acceptable
4 = Good
5 = Excellent

Return ONLY valid JSON in this exact format:

{{
    "correctness": 1,
    "relevance": 1,
    "faithfulness": 1,
    "reason": "Brief explanation"
}}
"""

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict and objective "
                        "RAG evaluation judge. "
                        "Return only valid JSON."
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
            evaluation = json.loads(content)
        except json.JSONDecodeError:
            evaluation = {
                "correctness": 0,
                "relevance": 0,
                "faithfulness": 0,
                "reason": "Judge returned invalid JSON.",
            }

        return evaluation
