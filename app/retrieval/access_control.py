ACCESS_LEVELS = {
    "EMPLOYEE": {"EMPLOYEE"},
    "MANAGER": {"EMPLOYEE", "MANAGER"},
    "AI_ENGINEER": {"EMPLOYEE", "MANAGER", "AI_ENGINEER"},
    "DEVOPS": {"EMPLOYEE", "MANAGER", "DEVOPS"},
    "SECURITY": {"EMPLOYEE", "MANAGER", "SECURITY"},
    "ADMIN": {"EMPLOYEE", "MANAGER", "AI_ENGINEER", "DEVOPS", "SECURITY", "ADMIN"},
}


class AccessController:
    def validate_access_level(self, access_level):
        if access_level not in ACCESS_LEVELS:
            raise ValueError(f"Invalid access level: {access_level}")

    def get_allowed_levels(self, user_access_level):
        self.validate_access_level(user_access_level)
        return sorted(ACCESS_LEVELS[user_access_level])

    def can_access(self, user_access_level, document_access_level):
        self.validate_access_level(document_access_level)
        return document_access_level in self.get_allowed_levels(user_access_level)
