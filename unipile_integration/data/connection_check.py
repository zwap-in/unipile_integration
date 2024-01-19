class ConnectionCheck:

    username: str
    has_accepted: bool

    def __init__(self, **kwargs):

        self.username = kwargs.get("username")
        self.has_accepted = kwargs.get("has_accepted")
