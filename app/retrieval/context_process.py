class ContextProcessor:

    def __init__(self, max_contexts=5):
        self.max_contexts = max_contexts

    def process(self, results):

        if not results:
            return []

        processed = []
        seen_parents = set()

        for result in results:

            parent_id = result.get("parent_id")

            # -------------------------------------------------
            # Remove duplicate parents
            # -------------------------------------------------

            if parent_id:

                if parent_id in seen_parents:
                    continue

                seen_parents.add(parent_id)

            # -------------------------------------------------
            # Build clean context object
            # -------------------------------------------------

            processed.append(
                {
                    "parent_id": parent_id,
                    "content": result.get(
                        "parent_text",
                        result.get("text", "")
                    ),
                    "metadata": result.get(
                        "parent_metadata",
                        result.get("metadata", {})
                    ),
                    "rerank_score": result.get(
                        "rerank_score"
                    ),
                }
            )

            # -------------------------------------------------
            # Context limit
            # -------------------------------------------------

            if len(processed) >= self.max_contexts:
                break

        return processed