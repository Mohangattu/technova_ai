import json
from datetime import datetime, timezone
from pathlib import Path


class TraceLogger:

    def __init__(self, log_directory="logs"):

        self.log_directory = Path(log_directory)

        self.log_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.log_file = (
            self.log_directory / "rag_traces.jsonl"
        )

    def log(self, trace):

        record = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            **trace,
        }

        with self.log_file.open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

        return record

    def log_error(
        self,
        query,
        started_at,
        error,
        latency_ms=None,
        retry_count=0,
    ):

        finished_at = datetime.now(
            timezone.utc
        ).isoformat()

        record = {
            "timestamp": finished_at,
            "started_at": started_at,
            "finished_at": finished_at,
            "query": query,
            "route": None,
            "retrieval_query": None,
            "latency_ms": latency_ms or {},
            "metrics": {},
            "grounded": False,
            "retry_count": retry_count,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
            },
        }

        with self.log_file.open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

        return record