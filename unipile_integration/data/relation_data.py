from datetime import datetime


class RelationData:

    created_at: int
    first_name: str
    last_name: str
    member_id: str
    public_identifier: str
    headline: str

    def __init__(self, **kwargs):

        (self.created_at, self.first_name, self.last_name,
         self.member_id, self.public_identifier, self.headline) = (kwargs.get("created_at"), kwargs.get("first_name"),
                                                    kwargs.get("last_name"), kwargs.get("member_id"),
                                                    kwargs.get("public_identifier"), kwargs.get("headline"))
