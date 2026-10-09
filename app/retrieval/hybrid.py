from rrf import RRFFusion


class HybridRetriever:

    def __init__(
        self,
        dense_retriever,
        bm25_retriever,
        rrf_k=60,
    ):
        self.dense_retriever = dense_retriever
        self.bm25_retriever = bm25_retriever

        self.rrf = RRFFusion(
            k=rrf_k
        )

    def retrieve(
        self,
        query,
        top_k=5,
        candidate_k=10,
        user_access_level=None,
    ):

        # -------------------------
        # Dense Retrieval
        # -------------------------

        dense_results = self.dense_retriever.retrieve(
            query,
            top_k=candidate_k,
            user_access_level=user_access_level,
        )

        # Convert Dense format
        # to common Hybrid format

        dense_results = [
            {
                "id": result["child_id"],
                "text": result["content"],
                "metadata": result["metadata"],
                "distance": result["distance"],
            }
            for result in dense_results
        ]

        # -------------------------
        # BM25 Retrieval
        # -------------------------

        bm25_results = self.bm25_retriever.retrieve(
            query,
            top_k=candidate_k,
            user_access_level=user_access_level,
        )

        # -------------------------
        # RRF Fusion
        # -------------------------

        fused_results = self.rrf.fuse(
            {
                "dense": dense_results,
                "bm25": bm25_results,
            },
            top_k=top_k,
        )

        return fused_results