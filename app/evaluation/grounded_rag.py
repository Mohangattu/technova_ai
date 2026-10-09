class GroundedRAG:

    def __init__(
        self,
        generator,
        verifier,
    ):
        self.generator = generator
        self.verifier = verifier

    def generate(
        self,
        query,
        contexts,
    ):
        generation = self.generator.generate(
            query,
            contexts,
        )

        answer = generation["answer"]

        verification = self.verifier.verify(
            question=query,
            answer=answer,
            contexts=contexts,
        )

        if not verification["grounded"]:
            return {
                "answer": (
                    "I could not verify the generated answer "
                    "against the available TechNova knowledge base."
                ),
                "sources": [],
                "grounded": False,
                "claims": verification["claims"],
                "verification_reason": verification["reason"],
            }

        return {
            "answer": answer,
            "sources": generation["sources"],
            "grounded": True,
            "claims": verification["claims"],
            "verification_reason": verification["reason"],
        }