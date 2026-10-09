ACCESS_HIERARCHY = {
    "EMPLOYEE": 1,
    "MANAGER": 2,
    "AI_ENGINEER": 3,
    "ADMIN": 4,
}


class AccessController:

    def __init__(self):
        self.access_hierarchy = ACCESS_HIERARCHY

    def validate_access_level(self, access_level):

        if access_level not in self.access_hierarchy:
            raise ValueError(
                f"Invalid access level: {access_level}"
            )

    def get_allowed_levels(self, user_access_level):

        self.validate_access_level(
            user_access_level
        )

        user_rank = self.access_hierarchy[
            user_access_level
        ]

        return [
            level
            for level, rank in self.access_hierarchy.items()
            if rank <= user_rank
        ]

    def can_access(
        self,
        user_access_level,
        document_access_level,
    ):

        self.validate_access_level(
            user_access_level
        )

        self.validate_access_level(
            document_access_level
        )

        user_rank = self.access_hierarchy[
            user_access_level
        ]

        document_rank = self.access_hierarchy[
            document_access_level
        ]

        return document_rank <= user_rank