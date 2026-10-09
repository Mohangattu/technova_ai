class RRFFusion:
    def __init__(self, k=60):
        self.k = k

    def fuse(self, ranked_lists, top_k=5):
        """
        ranked_lists:
            Dictionary containing ranked retrieval results.

            Example:
            {
                "dense": [...],
                "bm25": [...]
            }

        Each result must contain:
            {
                "id": ...,
                ...
            }
        """

        rrf_scores = {}
        result_data = {}

        for results in ranked_lists.values():

            for rank, result in enumerate(results, start=1):

                doc_id = result["id"]

                # RRF formula
                score = 1 / (self.k + rank)

                rrf_scores[doc_id] = (
                    rrf_scores.get(doc_id, 0) + score
                )

                # Preserve the result information
                if doc_id not in result_data:
                    result_data[doc_id] = result

        # Sort by highest RRF score
        ranked_ids = sorted(
            rrf_scores,
            key=rrf_scores.get,
            reverse=True
        )

        fused_results = []

        for doc_id in ranked_ids[:top_k]:

            result = result_data[doc_id].copy()

            result["rrf_score"] = rrf_scores[doc_id]

            fused_results.append(result)

        return fused_results