# IMPORTING STANDARD PACKAGES
from time import sleep
from typing import Optional, List, Tuple

# IMPORTING THIRD PARTY PACKAGES
import requests

from requests import Response

# IMPORTING LOCAL PACKAGES
from unipile_integration.data import IntegrationAccountData, MessageData,\
    AccountData, MessageCheck, ConnectionCheck


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
        elif method_name == "delete":
            return requests.delete(
                f"{self._base_endpoint_path}/{path}", headers={
                    "X-API-KEY": self._auth_token
                }
            )
        return requests.get(f"{self._base_endpoint_path}/{path}", headers={
                "X-API-KEY": self._auth_token
        })

    def _add_linkedin_integration(self, li_at_cookie: str, user_agent: str, li_a_cookie: str = None,
                                  recruiter_contract_id: str = None) -> Optional[str]:

        payload = {
            "provider": "LINKEDIN",
            "access_token": li_at_cookie,
            "user_agent": user_agent,
            "premium_token": li_a_cookie,
            "recruiter_contract_id": recruiter_contract_id
        }
        response = self._base_call("accounts", self._parse_payload(payload))
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

    def _get_reply_to_message_id(self, chat_id: str, owner_id: str, message_text: str, receiver_id: str) -> Optional[str]:

        response = self._base_call(f"chats/{chat_id}/messages?sender_id={owner_id}", {}, method_name="get")
        reply_text = None
        if response.status_code == 200:
            items = response.json()
            message_items = items.get("items", [])
            for index, item in enumerate(message_items):
                if index + 1 < len(message_items) and \
                        message_items[index + 1]["text"].strip() == message_text.strip() \
                        and item["sender_id"] == receiver_id:
                    reply_text = item["text"]
                    break
        return reply_text

    def _get_chat_by_username(self, linkedin_username: str, owner_id: str, message_text: str) -> Optional[str]:

        account_data = self._get_user_info(linkedin_username, owner_id)
        has_connection, user_id = account_data.has_connection, account_data.user_id
        if has_connection and user_id is not None:
            response = self._base_call(f"chat_attendees/{user_id}/chats?account_id={owner_id}", {},
                                       method_name="get")
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                if len(items) > 0:
                    chat_id = items[0].get("id")
                    return self._get_reply_to_message_id(
                        chat_id=chat_id,
                        owner_id=owner_id,
                        message_text=message_text,
                        receiver_id=user_id
                    )

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

    def auth_user(self, li_at_cookie: str, user_agent: str, li_a_cookie: str = None,
                  recruiter_contract_id: str = None) -> Optional[IntegrationAccountData]:

        owner_id = self._add_linkedin_integration(li_at_cookie, user_agent, li_a_cookie=li_a_cookie,
                                                  recruiter_contract_id=recruiter_contract_id)
        if owner_id is not None:
            sleep(1)
            return self._retrieve_current_user_data(owner_id)

    def delete_linkedin_connection(self, owner_id: str) -> bool:

        response = self._base_call(f"accounts/{owner_id}", {}, method_name="delete")
        return response.status_code == 200

    def check_replies(self, owner_id: str, messages_data: List[MessageCheck]) -> List[MessageCheck]:

        finals = []
        for message in messages_data:
            reply_text = self._get_chat_by_username(message.username, owner_id, message.message_text)
            finals.append(
                MessageCheck(
                    **{
                        "username": message.username,
                        "message_text": message.message_text,
                        "reply_text": reply_text
                    }
                )
            )
        return finals

    def check_connections(self, owner_id: str, usernames: list) -> List[ConnectionCheck]:

        finals = []
        for username in usernames:
            check, _ = self.has_accepted_connection(username, owner_id)
            finals.append(
                ConnectionCheck(
                    **{
                        "username": username,
                        "has_accepted": check
                    }
                )
            )
        return finals

    def auth_user_with_credentials(self, username: str, password) -> None:
        pass

    def solve_code_checkpoint(self, code: str, account_id: str) -> None:
        pass

    @staticmethod
    def _parse_payload(data: dict) -> dict:

        finals = {}
        for item in data:
            if data[item] is not None:
                finals[item] = data[item]
        return finals
