from pathlib import Path
import sys
import os
import time
from datetime import datetime, timezone

# Force UTF-8 output on Windows
if sys.platform == "win32":
    os.system("chcp 65001 > nul 2>&1")

sys.stdout.reconfigure(
    encoding="utf-8",
    errors="replace",
)

sys.stderr.reconfigure(
    encoding="utf-8",
    errors="replace",
)

# PATH SETUP
_APP_DIR = Path(__file__).parent.parent

sys.path.insert(0, str(_APP_DIR))
sys.path.insert(0, str(_APP_DIR / "graph"))
sys.path.insert(0, str(_APP_DIR / "query"))
sys.path.insert(0, str(_APP_DIR / "retrieval"))
sys.path.insert(0, str(_APP_DIR / "generation"))
sys.path.insert(0, str(_APP_DIR / "evaluation"))
sys.path.insert(0, str(_APP_DIR / "services"))
sys.path.insert(0, str(_APP_DIR / "ingestion"))


from langgraph.graph import StateGraph, START, END
from state import RAGState
from nodes import RAGNodes
from trace_logger import TraceLogger

class RAGGraph:

    def __init__(
        self,
        dense_retriever,
        bm25_retriever,
        parent_chunks,
        top_k=5,
        candidate_k=10,
        max_contexts=5,
    ):

        # Initialize all RAG nodes
        self.nodes = RAGNodes(
            dense_retriever=dense_retriever,
            bm25_retriever=bm25_retriever,
            parent_chunks=parent_chunks,
            top_k=top_k,
            candidate_k=candidate_k,
            max_contexts=max_contexts,
        )
        self.trace_logger = TraceLogger()

        # Create LangGraph workflow
        workflow = StateGraph(RAGState)

        # Register nodes
        workflow.add_node(
            "query",
            self.nodes.query_node,
        )

        workflow.add_node(
            "retrieval",
            self.nodes.retrieval_node,
        )

        workflow.add_node(
            "reranking",
            self.nodes.reranking_node,
        )

        workflow.add_node(
            "parent_expansion",
            self.nodes.parent_expansion_node,
        )

        workflow.add_node(
            "context",
            self.nodes.context_node,
        )

        workflow.add_node(
            "generation",
            self.nodes.generation_node,
        )

        workflow.add_node(
            "correction",
            self.nodes.correction_node,
        )

        # Linear workflow
        workflow.add_edge(START, "query")
        workflow.add_edge("query", "retrieval")
        workflow.add_edge("retrieval", "reranking")
        workflow.add_edge("reranking", "parent_expansion")
        workflow.add_edge("parent_expansion", "context")
        workflow.add_edge("context", "generation")

        workflow.add_conditional_edges(
            "generation",
            self._route_after_generation,
            {
                "end": END,
                "retry": "correction",
            },
        )

        workflow.add_edge("correction", "retrieval")

        # Compile graph
        self.graph = workflow.compile()

    def _route_after_generation(self, state):
        if state.get("grounded", False):
            return "end"
        if state.get("retry_count", 0) >= 1:
            return "end"
        return "retry"

    def run(
        self,
        query,
        user_access_level=None,
    ):
        start_perf = time.perf_counter()

        started_at = datetime.now(timezone.utc).isoformat()

        initial_state = {
            "original_query": query,
            "user_access_level": user_access_level,
            "retry_count": 0,
            "trace": None,
        }

        try:
            result = self.graph.invoke(initial_state)

            total_latency = (time.perf_counter() - start_perf) * 1000

            trace = result.get("trace", {})

            latency = trace.get("latency_ms", {})
            latency["total"] = round(total_latency, 2)
            trace["latency_ms"] = latency

            trace["started_at"] = started_at
            trace["finished_at"] = datetime.now(timezone.utc).isoformat()
            trace["grounded"] = result.get("grounded")
            trace["retry_count"] = result.get("retry_count", 0)
            trace["error"] = result.get("error")

            result["trace"] = trace
            self.trace_logger.log(trace)

            return result

        except Exception as exc:
            total_latency = (time.perf_counter() - start_perf) * 1000

            error_trace = self.trace_logger.log_error(
                query=query,
                started_at=started_at,
                error=exc,
                latency_ms={"total": round(total_latency, 2)},
                retry_count=initial_state.get("retry_count", 0),
            )

            return {
                "answer": None,
                "grounded": False,
                "retry_count": initial_state.get("retry_count", 0),
                "trace": error_trace,
                "error": error_trace["error"],
            }
