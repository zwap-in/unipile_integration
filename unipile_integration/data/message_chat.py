from datetime import datetime


class MessageChat:
    id: str
    attachments: list
    timestamp: datetime
    sender_id: str
    chat_id: str
    chat_provider_id: str
    message_text: str
    seen: bool
    deleted: bool
    delivered: bool
    edited: bool
    hidden: bool

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.attachments = kwargs.get("attachments")
        self.timestamp = datetime.strptime(kwargs.get('timestamp').split('.')[0], "%Y-%m-%dT%H:%M:%S")
        self.chat_id = kwargs.get("chat_id")
        self.chat_provider_id = kwargs.get("chat_provider_id")
        self.sender_id = kwargs.get("sender_id")
        self.message_text = kwargs.get("text")
        self.seen = kwargs.get("seen") == 1
        self.deleted = kwargs.get("deleted") == 1
        self.delivered = kwargs.get("delivered") == 1
        self.edited = kwargs.get("edited") == 1
        self.hidden = kwargs.get("hidden") == 1
