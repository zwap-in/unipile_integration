from typing import Optional


class MessageCheck:

    username: str
    message_text: str
    reply_text: Optional[str]

    def __init__(self, **kwargs):
        self.username = kwargs.get("username")
        self.message_text = kwargs.get("message_text")
        self.reply_text = kwargs.get("reply_text")
