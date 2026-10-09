import sys
from pathlib import Path

_APP_DIR = Path(__file__).parent.parent
_INGESTION_DIR = _APP_DIR / "query"

sys.path.insert(0, str(_APP_DIR))
sys.path.insert(0, str(_INGESTION_DIR))
from query_pipeline import QueryPipeline


pipeline = QueryPipeline()


queries = [
    "What is the default production API timeout?",
    "What about authentication?",
    "How long can an API request run?",
]


for query in queries:

    result = pipeline.process(query)

    print("\n" + "=" * 60)

    print("Original Query:")
    print(result["original_query"])

    print("Route:")
    print(result["route"])

    print("Retrieval Query:")
    print(result["retrieval_query"])