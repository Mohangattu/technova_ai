import time
from datetime import datetime, timezone


class RAGTracer:

    def __init__(self):
        self.trace = {
            "started_at": None,
            "finished_at": None,

            "query": None,
            "route": None,
            "retrieval_query": None,

            "latency_ms": {},

            "metrics": {
                "hybrid_result_count": 0,
                "reranked_result_count": 0,
                "context_count": 0,
            },

            "grounded": None,
            "retry_count": 0,
            "error": None,
        }

        self._timers = {}

    def start_trace(self, query):

        self.trace["started_at"] = (
            datetime.now(timezone.utc).isoformat()
        )

        self.trace["query"] = query

        self._timers["total"] = time.perf_counter()

    def start(self, stage):

        self._timers[stage] = time.perf_counter()

    def end(self, stage):

        if stage not in self._timers:
            return

        elapsed = (
            time.perf_counter()
            - self._timers[stage]
        )

        self.trace["latency_ms"][stage] = round(
            elapsed * 1000,
            2,
        )

        del self._timers[stage]

    def set_route(
        self,
        route,
        retrieval_query,
    ):

        self.trace["route"] = route

        self.trace["retrieval_query"] = (
            retrieval_query
        )

    def set_metric(
        self,
        name,
        value,
    ):

        self.trace["metrics"][name] = value

    def set_grounded(self, grounded):

        self.trace["grounded"] = grounded

    def set_retry_count(self, retry_count):

        self.trace["retry_count"] = retry_count

    def set_error(self, error):

        self.trace["error"] = error

    def finish(self):

        if "total" in self._timers:

            elapsed = (
                time.perf_counter()
                - self._timers["total"]
            )

            self.trace["latency_ms"]["total"] = round(
                elapsed * 1000,
                2,
            )

            del self._timers["total"]

        self.trace["finished_at"] = (
            datetime.now(timezone.utc).isoformat()
        )

        return self.trace.copy()

    def get_trace(self):

        return self.trace.copy()
