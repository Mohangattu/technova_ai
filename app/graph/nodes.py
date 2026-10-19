from app.query.query_pipeline import QueryPipeline
from app.query.rewriter import QueryRewriter
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.reranker import CrossEncoderReranker
from app.retrieval.parent_expansion import ParentExpander
from app.retrieval.context_process import ContextProcessor
from app.services.observability import RAGTracer
from app.evaluation.grounded_rag import GroundedRAG
from app.generation.generator import RAGGenerator
from app.evaluation.grounding_verifier import GroundingVerifier

class RAGNodes:

    def __init__(
        self,
        dense_retriever,
        bm25_retriever,
        parent_chunks,
        top_k=5,
        candidate_k=10,
        max_contexts=5,
    ):

        # -----------------------------------------------------
        # Existing RAG components
        # -----------------------------------------------------

        self.query_pipeline = QueryPipeline()

        self.hybrid_retriever = HybridRetriever(
            dense_retriever=dense_retriever,
            bm25_retriever=bm25_retriever,
        )

        self.reranker = CrossEncoderReranker()

        self.parent_expander = ParentExpander(parent_chunks)

        self.context_processor = ContextProcessor(
            max_contexts=max_contexts
        )

        self.generator = RAGGenerator()

        self.verifier = GroundingVerifier()

        self.grounded_rag = GroundedRAG(
            generator=self.generator,
            verifier=self.verifier,
        )

        self.query_rewriter = QueryRewriter()
        self.tracer = RAGTracer()

        # -----------------------------------------------------
        # Retrieval configuration
        # -----------------------------------------------------

        self.top_k = top_k
        self.candidate_k = candidate_k

    # =========================================================
    # 1. QUERY NODE
    # =========================================================

    def query_node(self, state):
        if state.get("trace") is None:
            self.tracer = RAGTracer()
            self.tracer.start_trace(state["original_query"])

        self.tracer.start("query")

        query = state["original_query"]

        result = self.query_pipeline.process(query)

        self.tracer.end("query")

        self.tracer.set_route(
            route=result["route"],
            retrieval_query=result["retrieval_query"],
        )

        return {
            "route": result["route"],
            "retrieval_query": result["retrieval_query"],
            "trace": self.tracer.get_trace(),
        }

    # =========================================================
    # 2. RETRIEVAL NODE
    # =========================================================

    def retrieval_node(self, state):
        

        self.tracer.start("retrieval")

        results = self.hybrid_retriever.retrieve(
            query=state["retrieval_query"],
            top_k=self.top_k,
            candidate_k=self.candidate_k,
            user_access_level=state.get("user_access_level"),
        )

        self.tracer.end("retrieval")

        self.tracer.set_metric(
            "hybrid_result_count",
            len(results),
        )

        return {
            "hybrid_results": results,
            "trace": self.tracer.get_trace(),
        }

    # =========================================================
    # 3. RERANKING NODE
    # =========================================================

    def reranking_node(self, state):
        self.tracer.start("reranking")

        results = self.reranker.rerank(
            query=state["retrieval_query"],
            results=state.get("hybrid_results", []),
            top_k=self.top_k,
        )

        self.tracer.end("reranking")

        self.tracer.set_metric(
            "reranked_result_count",
            len(results),
        )

        return {
            "reranked_results": results,
            "trace": self.tracer.get_trace(),
        }

    # =========================================================
    # 4. PARENT EXPANSION NODE
    # =========================================================

    def parent_expansion_node(self, state):
        self.tracer.start("parent_expansion")

        results = self.parent_expander.expand(
            results=state.get("reranked_results", []),
            user_access_level=state.get("user_access_level"),
        )

        self.tracer.end("parent_expansion")

        return {
            "expanded_results": results,
            "trace": self.tracer.get_trace(),
        }

    # =========================================================
    # 5. CONTEXT PROCESSING NODE
    # =========================================================

    def context_node(self, state):
        self.tracer.start("context")

        contexts = self.context_processor.process(
            state.get("expanded_results", [])
        )

        self.tracer.end("context")

        self.tracer.set_metric(
            "context_count",
            len(contexts),
        )

        return {
            "contexts": contexts,
            "trace": self.tracer.get_trace(),
        }

    # =========================================================
    # 6. GENERATION + VERIFICATION NODE
    # =========================================================

    def generation_node(self, state):
        self.tracer.start("generation")

        result = self.grounded_rag.generate(
            query=state["original_query"],
            contexts=state.get("contexts", []),
        )

        self.tracer.end("generation")

        self.tracer.set_grounded(result["grounded"])

        self.tracer.set_retry_count(
            state.get("retry_count", 0)
        )

        return {
            "answer": result["answer"],
            "sources": result["sources"],
            "grounded": result["grounded"],
            "claims": result["claims"],
            "verification_reason": result["verification_reason"],
            "trace": self.tracer.get_trace(),
        }

    # =========================================================
    # 7. CORRECTION NODE
    # =========================================================

    def correction_node(self, state):
        retry_count = state.get("retry_count", 0)

        if retry_count >= 1:
            self.tracer.set_error("Maximum retry limit reached.")
            return {
                "error": "Maximum retry limit reached.",
                "trace": self.tracer.get_trace(),
            }

        self.tracer.start("correction")

        original_query = state["original_query"]

        verification_reason = state.get("verification_reason", "")

        correction_prompt = f"""
Original user question:

{original_query}

The previous RAG answer could not be sufficiently
grounded in the retrieved TechNova knowledge base.

Verification feedback:

{verification_reason}

Create a better retrieval query that will retrieve
the information necessary to answer the original
question.

Rules:

1. Preserve the original meaning.
2. Do not invent facts.
3. Make the query more specific if possible.
4. Return only the retrieval query.
"""

        corrected_query = self.query_rewriter.rewrite(correction_prompt)

        self.tracer.end("correction")

        new_retry_count = retry_count + 1

        self.tracer.set_retry_count(new_retry_count)

        return {
            "correction_query": corrected_query,
            "retrieval_query": corrected_query,
            "retry_count": new_retry_count,
            "trace": self.tracer.get_trace(),
        }
