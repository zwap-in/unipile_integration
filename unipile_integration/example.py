from unipile_integration.linkedin import LinkedinUniPileIntegration


class ExampleIntegration:

    _integration: LinkedinUniPileIntegration

    def __init__(self, auth_token: str, base_endpoint_path: str):
        self._integration = LinkedinUniPileIntegration(auth_token=auth_token,
                                                       base_endpoint_path=base_endpoint_path)

    def run(self, example_type: str, example_data: dict):
        if example_type == "auth_user":
            li_at_cookie = example_data.get("li_at_cookie")
            user_agent = example_data.get("user_agent")
            return self._integration.auth_user(li_at_cookie, user_agent)
        if example_type == "send_message":
            owner_id = example_data.get("owner_id")
            usernames = example_data.get("usernames")
            message = example_data.get("message")
            check_message_not_sent = example_data.get("check_message_not_sent")
            return self._integration.send_message(usernames, owner_id, message, check_message_not_sent=check_message_not_sent)
        elif example_type == "send_connection":
            owner_id = example_data.get("owner_id")
            final_username = example_data.get("final_username")
            return self._integration.send_connection(final_username, owner_id)
        elif example_type == "check_connection":
            owner_id = example_data.get("owner_id")
            final_username = example_data.get("final_username")
            return self._integration.has_accepted_connection(final_username, owner_id)
