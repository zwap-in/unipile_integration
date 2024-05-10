from datetime import datetime


class ChatItem:
    chat_id: str
    attendee_provider_id: str
    timestamp: datetime
    folder: list
    provider_id: str

    def __init__(self, **kwargs):
        self.chat_id = kwargs.get("id")
        self.attendee_provider_id = kwargs.get("attendee_provider_id")
        self.timestamp = datetime.strptime(kwargs.get('timestamp').split('.')[0], "%Y-%m-%dT%H:%M:%S")
        self.folder = kwargs.get("folder", [])
        self.provider_id = kwargs.get("provider_id")
