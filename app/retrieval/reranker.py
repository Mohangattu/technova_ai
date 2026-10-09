from sentence_transformers import CrossEncoder


class CrossEncoderReranker:

    def __init__(
        self,
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
    ):
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query,
        results,
        top_k=5,
    ):
        if not results:
            return []

        pairs = [
            (query, result["text"])
            for result in results
        ]

        scores = self.model.predict(pairs)

        reranked = []

        for result, score in zip(results, scores):

            item = result.copy()
            item["rerank_score"] = float(score)

            reranked.append(item)

        reranked.sort(
            key=lambda x: x["rerank_score"],
            reverse=True,
        )

        return reranked[:top_k]