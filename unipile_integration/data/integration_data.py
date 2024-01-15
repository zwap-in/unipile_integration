class IntegrationAccountData:

    account_id: str
    full_name: str
    first_name: str
    last_name: str
    linkedin_username: str
    avatar_pic: str
    owner_id: str

    def __init__(self, **kwargs):

        self.account_id = kwargs.get("provider_id")
        self.first_name = kwargs.get("first_name")
        self.last_name = kwargs.get("last_name")
        self.full_name = f"{self.first_name} {self.last_name}"
        self.linkedin_username = kwargs.get("public_identifier")
        self.avatar_pic = kwargs.get("profile_picture_url")
        self.owner_id = kwargs.get("owner_id")
