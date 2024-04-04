from typing import Optional


class IntegrationAccountData:

    account_id: str
    full_name: str
    first_name: str
    last_name: str
    linkedin_username: str
    avatar_pic: str
    owner_id: str
    is_recruiter: bool
    is_sales_navigator: bool
    contract_id: Optional[str]
    seats_id: Optional[str]
    private_premium_id: Optional[str]

    def __init__(self, **kwargs):

        self.account_id = kwargs.get("provider_id")
        self.first_name = kwargs.get("first_name")
        self.last_name = kwargs.get("last_name")
        self.full_name = f"{self.first_name} {self.last_name}"
        self.linkedin_username = kwargs.get("public_identifier")
        self.avatar_pic = kwargs.get("profile_picture_url")
        self.owner_id = kwargs.get("owner_id")
        sales_navigator = kwargs.get("sales_navigator") if kwargs.get("sales_navigator") is not None else {}
        recruiter = kwargs.get("recruiter") if kwargs.get("recruiter") is not None else {}
        self.is_recruiter, self.is_sales_navigator = len(recruiter) > 0, len(sales_navigator) > 0
        final_premium_data = recruiter if len(recruiter) else (sales_navigator if len(sales_navigator) else {})
        self.contract_id, self.seats_id = final_premium_data.get("contract_id"), final_premium_data.get("owner_seat_id")
        self.private_premium_id = None
