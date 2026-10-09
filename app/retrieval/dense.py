import chromadb
from sentence_transformers import SentenceTransformer

from model import ChildChunk
from access_control import AccessController


class DenseRetriever:

    def __init__(
        self,
        persist_directory="vectorstore/chroma",
        collection_name="technova_children",
        model_name="all-MiniLM-L6-v2",
    ):
        self.model = SentenceTransformer(model_name)

        self.client = chromadb.PersistentClient(
            path=persist_directory
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        self.access_controller = AccessController()

    def add_chunks(self, chunks):

        if not chunks:
            return

        documents = [
            chunk.content
            for chunk in chunks
        ]

        embeddings = self.model.encode(
            documents,
            normalize_embeddings=True,
        ).tolist()

        ids = [
            chunk.child_id
            for chunk in chunks
        ]

        metadatas = [
            {
                "parent_id": chunk.parent_id,
                "document_id": chunk.metadata.document_id,
                "title": chunk.metadata.title,
                "department": chunk.metadata.department,
                "section": chunk.metadata.section,
                "document_type": chunk.metadata.document_type,
                "version": chunk.metadata.version,
                "access_level": chunk.metadata.access_level,
            }
            for chunk in chunks
        ]

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def retrieve(
        self,
        query,
        top_k=5,
        user_access_level=None,
    ):

        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True,
        ).tolist()

        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": [
                "documents",
                "metadatas",
                "distances",
            ],
        }

        if user_access_level is not None:

            allowed_levels = (
                self.access_controller.get_allowed_levels(
                    user_access_level
                )
            )

            query_kwargs["where"] = {
                "access_level": {
                    "$in": allowed_levels
                }
            }

        results = self.collection.query(
            **query_kwargs
        )

        retrieved = []

        for i in range(
            len(results["ids"][0])
        ):

            retrieved.append(
                {
                    "child_id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                }
            )

        return retrieved