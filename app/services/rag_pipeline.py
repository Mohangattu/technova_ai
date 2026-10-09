from pathlib import Path
import sys


_APP_DIR = Path(__file__).parent.parent

sys.path.insert(0, str(_APP_DIR))
sys.path.insert(0, str(_APP_DIR / "query"))
sys.path.insert(0, str(_APP_DIR / "retrieval"))
sys.path.insert(0, str(_APP_DIR / "generation"))
sys.path.insert(0, str(_APP_DIR / "evaluation"))
from query_pipeline import QueryPipeline

from hybrid import HybridRetriever
from reranker import CrossEncoderReranker
from parent_expansion import ParentExpander
from context_process import ContextProcessor

from generator import RAGGenerator
from grounded_rag import GroundedRAG
from grounding_verifier import GroundingVerifier


class RAGPipeline:

    def __init__(
        self,
        dense_retriever,
        bm25_retriever,
        parent_chunks,
        top_k=5,
        candidate_k=10,
        max_contexts=5,
    ):

        # Query processing
        self.query_pipeline = QueryPipeline()

        # Retrieval
        self.hybrid_retriever = HybridRetriever(
            dense_retriever=dense_retriever,
            bm25_retriever=bm25_retriever,
        )

        # Reranking
        self.reranker = CrossEncoderReranker()

        # Parent expansion
        self.parent_expander = ParentExpander(
            parent_chunks
        )

        # Context processing
        self.context_processor = ContextProcessor(
            max_contexts=max_contexts
        )

        # Generation
        self.generator = RAGGenerator()

        # Grounding verification
        self.verifier = GroundingVerifier()

        self.grounded_rag = GroundedRAG(
            generator=self.generator,
            verifier=self.verifier,
        )

        self.top_k = top_k
        self.candidate_k = candidate_k

    def run(
        self,
        query,
        user_access_level=None,
    ):

        # ------------------------------------------------
        # 1. Query Router + Rewriter
        # ------------------------------------------------

        query_result = self.query_pipeline.process(
            query
        )

        retrieval_query = query_result[
            "retrieval_query"
        ]

        # ------------------------------------------------
        # 2. Hybrid Retrieval
        # ------------------------------------------------

        hybrid_results = self.hybrid_retriever.retrieve(
            query=retrieval_query,
            top_k=self.top_k,
            candidate_k=self.candidate_k,
            user_access_level=user_access_level,
        )

        # ------------------------------------------------
        # 3. Cross-Encoder Reranking
        # ------------------------------------------------

        reranked_results = self.reranker.rerank(
            query=retrieval_query,
            results=hybrid_results,
            top_k=self.top_k,
        )

        # ------------------------------------------------
        # 4. Parent Expansion
        # ------------------------------------------------

        expanded_results = self.parent_expander.expand(
            results=reranked_results,
            user_access_level=user_access_level,
        )

        # ------------------------------------------------
        # 5. Context Processing
        # ------------------------------------------------

        contexts = self.context_processor.process(
            expanded_results
        )

        # ------------------------------------------------
        # 6. Grounded Generation
        # ------------------------------------------------

        generation = self.grounded_rag.generate(
            query=query,
            contexts=contexts,
        )

        # ------------------------------------------------
        # 7. Final Response
        # ------------------------------------------------

        return {
            "original_query": query,
            "route": query_result["route"],
            "retrieval_query": retrieval_query,
            "answer": generation["answer"],
            "sources": generation["sources"],
            "grounded": generation["grounded"],
            "claims": generation["claims"],
            "verification_reason": generation[
                "verification_reason"
            ],
        }