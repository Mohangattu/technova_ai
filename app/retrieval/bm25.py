from rank_bm25 import BM25Okapi

from access_control import AccessController


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
            chunk["text"].lower().split()
            for chunk in chunks
        ]

        self.bm25 = BM25Okapi(
            self.tokenized_corpus
        )

        self.access_controller = AccessController()

    def retrieve(
        self,
        query,
        top_k=5,
        user_access_level=None,
    ):

        tokenized_query = query.lower().split()

        scores = self.bm25.get_scores(
            tokenized_query
        )

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )

        results = []

        allowed_levels = None

        if user_access_level is not None:

            allowed_levels = (
                self.access_controller.get_allowed_levels(
                    user_access_level
                )
            )

        for index in ranked_indices:

            chunk = self.chunks[index]

            metadata = chunk.get(
                "metadata",
                {}
            )

            document_access_level = metadata.get(
                "access_level"
            )

            # Authorization filter
            if (
                allowed_levels is not None
                and document_access_level
                not in allowed_levels
            ):
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