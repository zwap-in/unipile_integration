from typing import Optional


class MessageData:

    chat_id: Optional[str]
    author_id: str
    linkedin_id: str

    def __init__(self, **kwargs):
        self.chat_id = kwargs.get("chat_id")
        self.author_id = kwargs.get("author_id")
        self.linkedin_id = kwargs.get("linkedin_id")
