from typing import Any, Dict, List, Optional, TypedDict


class RAGState(TypedDict, total=False):

    # User input
    original_query: str
    user_access_level: str

    # Query processing
    route: str
    retrieval_query: str
    correction_query: str

    # Retrieval
    hybrid_results: List[Dict[str, Any]]
    reranked_results: List[Dict[str, Any]]
    expanded_results: List[Dict[str, Any]]
    contexts: List[Dict[str, Any]]

    # Generation
    answer: str
    sources: List[Dict[str, Any]]

    # Verification
    grounded: bool
    claims: List[Dict[str, Any]]
    verification_reason: Optional[str]

    # Control
    retry_count: int
    error: Optional[str]

    # Observability
    trace: Dict[str, Any]