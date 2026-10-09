import json
from pathlib import Path

from retrieval_metrics import (
    recall_at_k,
    precision_at_k,
    reciprocal_rank,
    ndcg_at_k,
)


class RetrievalEvaluator:

    def __init__(self, retriever, evaluation_file):
        self.retriever = retriever
        self.evaluation_file = Path(evaluation_file)

    def load_dataset(self):
        with open(self.evaluation_file, "r", encoding="utf-8") as file:
            return json.load(file)

    def evaluate(self, k=5):
        dataset = self.load_dataset()

        results = []

        for item in dataset:
            question = item["question"]
            relevant_documents = item["relevant_documents"]

            retrieved = self.retriever.retrieve(
                question,
                top_k=k,
            )

            recall = recall_at_k(
                retrieved,
                relevant_documents,
                k,
            )

            precision = precision_at_k(
                retrieved,
                relevant_documents,
                k,
            )

            rr = reciprocal_rank(
                retrieved,
                relevant_documents,
            )

            ndcg = ndcg_at_k(
                retrieved,
                relevant_documents,
                k,
            )

            results.append(
                {
                    "id": item["id"],
                    "question": question,
                    "recall": recall,
                    "precision": precision,
                    "rr": rr,
                    "ndcg": ndcg,
                }
            )

        return results

    def summarize(self, results):
        if not results:
            return {}

        count = len(results)

        return {
            "queries": count,
            "recall": sum(
                result["recall"]
                for result in results
            ) / count,

            "precision": sum(
                result["precision"]
                for result in results
            ) / count,

            "mrr": sum(
                result["rr"]
                for result in results
            ) / count,

            "ndcg": sum(
                result["ndcg"]
                for result in results
            ) / count,
        }