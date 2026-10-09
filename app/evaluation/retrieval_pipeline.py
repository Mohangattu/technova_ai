class EvaluationRetriever:

    def __init__(
        self,
        hybrid_retriever,
        reranker,
        candidate_k=10,
        top_k=5,
    ):
        self.hybrid_retriever = hybrid_retriever
        self.reranker = reranker
        self.candidate_k = candidate_k
        self.top_k = top_k

    def retrieve(self, query, top_k=None):

        if top_k is None:
            top_k = self.top_k

        # Stage 1:
        # Dense + BM25 + RRF
        hybrid_results = self.hybrid_retriever.retrieve(
            query,
            top_k=self.candidate_k,
            candidate_k=self.candidate_k,
        )

        # Stage 2:
        # Cross-encoder reranking
        reranked_results = self.reranker.rerank(
            query,
            hybrid_results,
            top_k=top_k,
        )

        return reranked_results