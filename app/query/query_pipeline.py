from router import QueryRouter
from rewriter import QueryRewriter


class QueryPipeline:

    def __init__(
        self,
        router=None,
        rewriter=None,
    ):
        self.router = router or QueryRouter()
        self.rewriter = rewriter or QueryRewriter()

    def process(self, query: str):

        route_result = self.router.route(query)

        if route_result.route == "DIRECT":

            retrieval_query = query

        else:

            retrieval_query = self.rewriter.rewrite(
                query
            )

        return {
            "original_query": query,
            "route": route_result.route,
            "retrieval_query": retrieval_query,
        }