# IMPORTING STANDARD PACKAGES
from time import sleep
from typing import Optional, List, Tuple

# IMPORTING THIRD PARTY PACKAGES
import requests

from requests import Response

# IMPORTING LOCAL PACKAGES
from unipile_integration.data import IntegrationAccountData, MessageData, AccountData


class LinkedinUniPileIntegration:

    _auth_token: str
    _base_endpoint_path: str

    def __init__(self, auth_token: str, base_endpoint_path: str):

        self._auth_token = auth_token
        self._base_endpoint_path = base_endpoint_path

    def _base_call(self, path: str, data: dict, method_name: str = "post", body_type: str = "json") -> Response:

        if method_name == "post":
            kwargs = {
                "json": data
            } if body_type == "json" else {
                "data": data
            }
            return requests.post(f"{self._base_endpoint_path}/{path}", headers={
                "X-API-KEY": self._auth_token
            }, **kwargs)
        return requests.get(f"{self._base_endpoint_path}/{path}", headers={
                "X-API-KEY": self._auth_token
        })

    def _add_linkedin_integration(self, li_at_cookie: str, user_agent: str = None) -> Optional[str]:

        kwargs = {} if user_agent is None else {
            "user_agent": user_agent
        }
        response = self._base_call("accounts", {
            "provider": "LINKEDIN",
            "access_token": li_at_cookie
        }, **kwargs)
        if response.status_code == 201:
            data = response.json()
            return data.get("account_id")

    def _retrieve_current_user_data(self, owner_id: str) -> Optional[IntegrationAccountData]:

        response = self._base_call(f"users/me?account_id={owner_id}", {}, method_name="get")
        if response.status_code == 200:
            data = response.json()
            return IntegrationAccountData(**data, **{
                "owner_id": owner_id
            })

    def _get_user_info(self, linkedin_username: str, owner_id: str) -> Optional[AccountData]:

        response = self._base_call(f"users/{linkedin_username}?account_id={owner_id}", {}, method_name="get")
        if response.status_code == 200:
            data = response.json()
            return AccountData(**data)

    def _has_conversation_started(self, owner_id: str, provider_id: str) -> bool:

        response = self._base_call(f"chat_attendees/{provider_id}/chats?account_id={owner_id}", {}, method_name="get")
        return response.status_code == 200

    def has_accepted_connection(self, linkedin_username: str, owner_id: str) -> Tuple[bool, Optional[str]]:

        response = self._get_user_info(linkedin_username, owner_id)
        return response is not None and response.has_connection, \
            response.user_id if response is not None else None

    def send_connection(self, linkedin_username: str, owner_id: str) -> bool:

        accepted_connection, user_id = self.has_accepted_connection(linkedin_username, owner_id)
        if accepted_connection is False and user_id is not None:
            response = self._base_call(f"users/invite", {
                "provider_id": user_id,
                "account_id": owner_id
            })
            return response.status_code == 201
        return False

    def send_message(self, attendees_username: list, owner_id: str, message: str,
                     check_message_not_sent: bool = True) -> List[MessageData]:

        codes_status = []
        final_users = [self._get_user_info(
            item, owner_id
        ) for item in attendees_username]
        final_users = [item.user_id for item in final_users if item is not None]
        for attendee in final_users:
            could_send_message = self._has_conversation_started(owner_id, attendee) is False if check_message_not_sent\
                else True
            if could_send_message:
                response = self._base_call("chats", {
                    "attendees_ids": attendee,
                    "account_id": owner_id,
                    "text": message
                }, body_type="form")
                chat_id = None
                if response.status_code == 201:
                    data = response.json()
                    chat_id = data.get("chat_id")
                codes_status.append(
                    MessageData(**{
                        "chat_id": chat_id,
                        "author_id": owner_id,
                        "linkedin_id": attendee
                    })
                )
        return codes_status

    def auth_user(self, li_at_cookie: str, user_agent: str = None) -> Optional[IntegrationAccountData]:

        owner_id = self._add_linkedin_integration(li_at_cookie, user_agent=user_agent)
        if owner_id is not None:
            sleep(1)
            return self._retrieve_current_user_data(owner_id)
