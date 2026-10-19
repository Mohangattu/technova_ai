from app.retrieval.access_control import AccessController


class ParentExpander:

    def __init__(self, parent_chunks):

        self.parent_chunks = {
            parent.parent_id: parent
            for parent in parent_chunks
        }

        self.access_controller = AccessController()

    def expand(
        self,
        results,
        user_access_level=None,
    ):

        expanded_results = []

        for result in results:

            parent_id = result.get(
                "metadata", {}
            ).get("parent_id")

            # No parent information
            if not parent_id:
                expanded_results.append(result)
                continue

            parent = self.parent_chunks.get(
                parent_id
            )

            # Parent not found
            if not parent:
                expanded_results.append(result)
                continue

            # --------------------------------
            # Parent Authorization
            # --------------------------------

            if user_access_level is not None:

                parent_access_level = (
                    parent.metadata.access_level
                )

                if not self.access_controller.can_access(
                    user_access_level,
                    parent_access_level,
                ):
                    # Do not expose unauthorized parent
                    continue

            # --------------------------------
            # Expand Parent
            # --------------------------------

            expanded_result = result.copy()

            expanded_result["parent_id"] = (
                parent.parent_id
            )

            expanded_result["parent_text"] = (
                parent.content
            )

            expanded_result["parent_metadata"] = {
                "document_id": (
                    parent.metadata.document_id
                ),
                "title": (
                    parent.metadata.title
                ),
                "department": (
                    parent.metadata.department
                ),
                "section": (
                    parent.metadata.section
                ),
                "document_type": (
                    parent.metadata.document_type
                ),
                "version": (
                    parent.metadata.version
                ),
                "access_level": (
                    parent.metadata.access_level
                ),
            }

            expanded_results.append(
                expanded_result
            )

        return expanded_results
