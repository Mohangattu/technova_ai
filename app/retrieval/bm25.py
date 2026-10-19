import re

from rank_bm25 import BM25Okapi

STOP_WORDS = set(
    "a an and are as at be by can do does for from how i in is it me of on or our please should tell that the their this to us what when where which who with you your".split()
)


def tokenize(text):
    return [word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOP_WORDS]


from app.retrieval.access_control import AccessController


class BM25Retriever:
    def __init__(self, chunks):
        """
        chunks: list of dictionaries containing at least:

        {
            "id": ...,
            "text": ...,
            "metadata": ...
        }
        """

        self.chunks = chunks

        # Tokenize each child chunk
        self.tokenized_corpus = [
            tokenize(chunk["metadata"].get("title", "") + " " + chunk["text"]) for chunk in chunks
        ]

        self.bm25 = BM25Okapi(self.tokenized_corpus)

        self.access_controller = AccessController()

    def retrieve(
        self,
        query,
        top_k=5,
        user_access_level=None,
    ):

        tokenized_query = tokenize(query)

        scores = self.bm25.get_scores(tokenized_query)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )

        results = []

        allowed_levels = None

        if user_access_level is not None:
            allowed_levels = self.access_controller.get_allowed_levels(user_access_level)

        for index in ranked_indices:
            chunk = self.chunks[index]

            metadata = chunk.get("metadata", {})

            document_access_level = metadata.get("access_level")

            # Authorization filter
            if allowed_levels is not None and document_access_level not in allowed_levels:
                continue

            results.append(
                {
                    "id": chunk["id"],
                    "score": float(scores[index]),
                    "text": chunk["text"],
                    "metadata": metadata,
                }
            )

            if len(results) >= top_k:
                break

        return results
