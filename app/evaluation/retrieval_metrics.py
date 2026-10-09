def recall_at_k(retrieved_documents, relevant_documents, k):
    """
    Measures whether the relevant document appears
    in the top-k retrieved results.
    """

    if not relevant_documents:
        return 0.0

    retrieved_top_k = retrieved_documents[:k]

    retrieved_ids = {
        result.get("metadata", {}).get("document_id")
        for result in retrieved_top_k
    }

    relevant_ids = set(relevant_documents)

    intersection = retrieved_ids.intersection(relevant_ids)

    return len(intersection) / len(relevant_ids)

def precision_at_k(retrieved_documents, relevant_documents, k):
    """
    Measures the fraction of top-k retrieved results
    that are relevant.
    """

    if k <= 0:
        return 0.0

    retrieved_top_k = retrieved_documents[:k]

    relevant_ids = set(relevant_documents)

    relevant_count = 0

    for result in retrieved_top_k:
        document_id = result.get("metadata", {}).get("document_id")

        if document_id in relevant_ids:
            relevant_count += 1

    return relevant_count / k

def reciprocal_rank(retrieved_documents, relevant_documents):
    """
    Returns the reciprocal rank of the first relevant result.
    """

    relevant_ids = set(relevant_documents)

    for rank, result in enumerate(retrieved_documents, start=1):
        document_id = result.get("metadata", {}).get("document_id")

        if document_id in relevant_ids:
            return 1.0 / rank

    return 0.0

import math


def ndcg_at_k(retrieved_documents, relevant_documents, k):
    """
    Measures ranking quality of the top-k retrieved results.

    Relevant documents receive relevance = 1.
    Non-relevant documents receive relevance = 0.
    """

    if k <= 0:
        return 0.0

    relevant_ids = set(relevant_documents)

    retrieved_top_k = retrieved_documents[:k]

    relevance_scores = []

    for result in retrieved_top_k:
        document_id = result.get("metadata", {}).get("document_id")

        if document_id in relevant_ids:
            relevance_scores.append(1)
        else:
            relevance_scores.append(0)

    dcg = 0.0

    for rank, relevance in enumerate(relevance_scores, start=1):
        dcg += relevance / math.log2(rank + 1)

    ideal_relevance = sorted(
        relevance_scores,
        reverse=True
    )

    idcg = 0.0

    for rank, relevance in enumerate(ideal_relevance, start=1):
        idcg += relevance / math.log2(rank + 1)

    if idcg == 0:
        return 0.0

    return dcg / idcg