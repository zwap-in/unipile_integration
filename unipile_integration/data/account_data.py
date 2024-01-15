class AccountData:

    user_id: str
    username: str
    has_connection: bool

    def __init__(self, **kwargs):
        self.user_id, self.username, self.has_connection = kwargs.get("provider_id"), kwargs.get(
            "public_identifier"), kwargs.get("is_relationship")
