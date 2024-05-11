# IMPORTING STANDARD PACKAGES
from time import sleep
from datetime import datetime
from typing import Optional, List, Tuple

# IMPORTING THIRD PARTY PACKAGES
import requests

from requests import Response

# IMPORTING LOCAL PACKAGES
from unipile_integration.data import IntegrationAccountData, MessageData,\
    AccountData, MessageCheck, ConnectionCheck, ChatItem, MessageChat, RelationData


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

    def _read_full_items(self, url: str, max_items: int, item_type: type) -> list:

        items = []
        check = len(items) < max_items
        while check:
            response = self._base_call(url, {}, method_name="get")
            if response.status_code == 200:
                data = response.json()
                cursor = data.get("cursor")
                items.extend([item_type(**item) for item in data.get("items", [])])
                check = cursor is not None and len(items) < max_items
            else:
                break
        return items

    def read_all_chats(self, account_id: str, max_number_of_chats: int = 100) -> List[ChatItem]:

        limit = max_number_of_chats if max_number_of_chats is not None and max_number_of_chats <= 250 else 100
        url = f"chats?limit={limit}&account_type=LINKEDIN&account_id={account_id}"
        return self._read_full_items(url, max_number_of_chats, ChatItem)

    def read_full_chat(self, chat_id: str, max_number_of_messages: int = None) -> List[MessageChat]:

        limit = max_number_of_messages if max_number_of_messages is not None and max_number_of_messages <= 250 else 100
        url = f"chats/{chat_id}/messages?limit={limit}"
        return self._read_full_items(url, max_number_of_messages, MessageChat)

    def _retrieve_current_user_data(self, owner_id: str) -> Optional[IntegrationAccountData]:

        response = self._base_call(f"users/me?account_id={owner_id}", {}, method_name="get")
        if response.status_code == 200:
            data = response.json()
            return IntegrationAccountData(**data, **{
                "owner_id": owner_id
            })

    def _get_user_info(self, linkedin_username: str, owner_id: str, custom_api: str = None) -> Optional[AccountData]:

        additional_params = ""
        if custom_api is not None and custom_api.strip() != "":
            additional_params = f"&linkedin_api={custom_api}"
        response = self._base_call(f"users/{linkedin_username}?account_id={owner_id}{additional_params}", {}, method_name="get")
        if response.status_code == 200:
            data = response.json()
            return AccountData(**data)

    def _has_conversation_started(self, owner_id: str, provider_id: str) -> bool:

        response = self._base_call(f"chat_attendees/{provider_id}/chats?account_id={owner_id}", {}, method_name="get")
        return response.status_code == 200

    def _get_reply_to_message_id(self, chat_id: str, owner_id: str, message_text: str, receiver_id: str) -> Optional[str]:

        response = self._base_call(f"chats/{chat_id}/messages?sender_id={owner_id}", {}, method_name="get")
        if response.status_code == 200:
            items = response.json()
            message_items = items.get("items", [])
            collecting = False
            replies = []
            for item in reversed(message_items):
                if item["text"].strip() == message_text.strip() and item["sender_id"] != receiver_id:
                    collecting = True
                    continue
                if collecting:
                    if item["sender_id"] == receiver_id:
                        replies.append(item["text"])
                    else:
                        break
            return "\n".join(replies)
        return None

    def _get_chat_by_username(self, linkedin_username: str, owner_id: str, message_text: str) -> Optional[Tuple[str, str]]:

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
                    ), chat_id

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

    def get_chat_url(self, chat_id: str) -> str:

        response = self._base_call(f"chats/{chat_id}", {},
                                   method_name="get")
        if response.status_code == 200:
            data = response.json()
            return f"https://www.linkedin.com/messaging/thread/{data.get('provider_id')}/"

    def send_message_to_chat(self, chat_id: str, message: str) -> bool:

        if message is not None and message.strip() != "":
            response = self._base_call(f"chats/{chat_id}/messages/", {
                "text": message,
            }, body_type="json")
            return response.status_code == 201
        return False

    def send_message(self, attendees_username: list, owner_id: str, message: str,
                     check_message_not_sent: bool = True, inmail_message: bool = False,
                     subject: str = None, is_sales: bool = False) -> List[MessageData]:

        codes_status = []
        if message is not None and message.strip() != "":
            final_users = [self._get_user_info(
                item, owner_id
            ) for item in attendees_username]
            final_users = [item.user_id for item in final_users if item is not None]
            for attendee in final_users:
                could_send_message = self._has_conversation_started(owner_id,
                                                                    attendee) is False if check_message_not_sent \
                    else True
                if could_send_message:
                    kwargs = {}
                    if inmail_message:
                        kwargs = {
                            "linkedin": {
                                "api": 'recruiter' if is_sales is False else "sales_navigator",
                                "inmail": True,
                            },
                        }
                        if subject is not None and subject.strip() != "":
                            kwargs["subject"] = subject
                    response = self._base_call("chats", {
                        "attendees_ids": attendee,
                        "account_id": owner_id,
                        "text": message,
                        **kwargs
                    }, body_type="json")
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

    def _find_personal_private_id(self, is_sales_api: bool, provider_id: str, owner_id: str) -> str:

        account_data = self._get_user_info(provider_id, owner_id, "sales_navigator" if is_sales_api else "recruiter")
        if account_data is not None:
            return account_data.user_id

    def auth_user(self, li_at_cookie: str, user_agent: str, li_a_cookie: str = None,
                  recruiter_contract_id: str = None) -> Optional[IntegrationAccountData]:

        owner_id = self._add_linkedin_integration(li_at_cookie, user_agent, li_a_cookie=li_a_cookie,
                                                  recruiter_contract_id=recruiter_contract_id)
        if owner_id is not None:
            sleep(2)
            account_data = self._retrieve_current_user_data(owner_id)
            if account_data is not None and (account_data.is_recruiter or account_data.is_sales_navigator):
                is_sales = account_data.is_sales_navigator
                sleep(1)
                provider_id = self._find_personal_private_id(is_sales, account_data.account_id, owner_id)
                account_data.private_premium_id = provider_id
            return account_data

    def delete_linkedin_connection(self, owner_id: str) -> bool:

        response = self._base_call(f"accounts/{owner_id}", {}, method_name="delete")
        return response.status_code == 200

    def check_replies(self, owner_id: str, messages_data: List[MessageCheck]) -> List[MessageCheck]:

        finals = []
        for message in messages_data:
            reply_text, chat_id = self._get_chat_by_username(message.username, owner_id, message.message_text)
            finals.append(
                MessageCheck(
                    **{
                        "username": message.username,
                        "message_text": message.message_text,
                        "reply_text": reply_text,
                        "chat_id": chat_id
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

    def scrape_job_post_skills(self, account_id: str, job_post_id: str) -> list:

        payload = {
            "query_params": {"decorationId": "com.linkedin.voyager.dash.deco.assessments.FullJobSkillMatchInsight-16"},
            "request_url": f"https://www.linkedin.com/voyager/api/voyagerAssessmentsDashJobSkillMatchInsight/urn:li:fsd_jobSkillMatchInsight:{job_post_id}/",
            "method": "GET",
            "account_id": account_id,
            "encoding": False
        }
        response = self._base_call("linkedin", data=payload, method_name="post")
        if response.status_code == 200:
            data = response.json().get("data", {})
            skills = data["skillMatchStatuses"]
            return [item["localizedSkillDisplayName"] for item in skills]
        return []

    def scrape_job_post_by_linkedin(self, account_id: str, job_post_id: str):

        payload = {
            "query_params": {"decorationId": "com.linkedin.voyager.deco.jobs.web.shared.WebFullJobPosting-65"},
            "request_url": f"https://www.linkedin.com/voyager/api/jobs/jobPostings/{job_post_id}/",
            "method": "GET",
            "account_id": account_id,
            "encoding": False
        }
        response = self._base_call("linkedin", data=payload, method_name="post")
        if response.status_code == 200:
            job_data = response.json().get("data", {})
            key_name = list(job_data.get("companyDetails").keys())[0]
            work_place_type = job_data["workplaceTypes"][0] if len(job_data["workplaceTypes"]) else None,
            work_place_type = None if work_place_type is None else (
                "hybrid" if "3" in work_place_type else (
                    "fully_remote" if "2" in work_place_type else "physical"))
            job_post_url = f"https://www.linkedin.com/jobs/search/?currentJobId={job_data['jobPostingId']}"
            timestamp_seconds = job_data["listedAt"] / 1000
            dt_object = datetime.utcfromtimestamp(timestamp_seconds)
            listed_at = dt_object.strftime('%d %B %Y, %H:%M:%S UTC')
            timing_mode = job_data.get("employmentStatusResolutionResult", {}).get("entityUrn", "")
            timing_mode = self.get_timing_mode(timing_mode)
            return {
                "job_title": job_data["title"],
                "company_id": job_data.get("companyDetails", {}).get(key_name, {})
                .get("companyResolutionResult", {}).get("entityUrn", None),
                "company_name": job_data.get("companyDetails", {}).get(key_name, {})
                .get("companyResolutionResult", {}).get("name", None),
                "company_linkedin": job_data.get("companyDetails", {}).get(key_name, {})
                .get("companyResolutionResult", {}).get("url", None),
                "description": job_data["description"]["text"],
                "work_mode_type": work_place_type,
                "location_name": job_data["formattedLocation"],
                "listed_at": listed_at,
                "job_post_url": job_post_url,
                "timing": timing_mode,
            }

    def list_all_relations(self, account_id: str) -> dict:

        cursor = None
        relations = {}
        check = True
        while check:
            additional_params = ""
            if cursor is not None:
                additional_params = f"&cursor={cursor}"
            response = self._base_call(f"users/relations?account_id={account_id}&limit=250{additional_params}", {}, method_name="get")
            sleep(1)
            if response.status_code == 200:
                data = response.json()
                cursor = data.get("cursor")
                relations = {
                    **{
                        item.member_id: item for
                        item in [RelationData(**tmp) for tmp in data.get("items", [])]
                    },
                    **relations
                }
                check = cursor is not None
                print(len(relations))
        return relations

    @staticmethod
    def get_timing_mode(timing_urn: str) -> str:

        if "CONTRACT" in timing_urn:
            return "contract"
        elif "FULL_TIME" in timing_urn:
            return "full_time"
        elif "PART_TIME" in timing_urn:
            return "part_time"
        elif "TEMPORARY" in timing_urn:
            return "temporary"
        elif "VOLUNTEER" in timing_urn:
            return "other"
        elif "INTERNSHIP" in timing_urn:
            return "other"
        else:
            return "other"

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


