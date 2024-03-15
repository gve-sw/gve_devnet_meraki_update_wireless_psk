"""
Copyright (c) 2023 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

from webex_api import WebexBot, WebexOps
from meraki_api import MerakiOps
from logrr import lm
from typing import  Optional, Tuple


class Validators:
    @staticmethod
    def validate_meraki_api_key(api_key: str) -> bool:
        """Validate Meraki API Key."""
        meraki_ops = MerakiOps(api_key=api_key)
        meraki_ops = meraki_ops.get_instance()
        valid, message = meraki_ops.validate_api_key()
        return valid

    @staticmethod
    def validate_webex_bot_token(token: str) -> bool:
        webex_bot = WebexBot(token=token)  # Get the singleton instance
        valid, _ = webex_bot.validate_token()
        return valid

    @staticmethod
    def validate_webex_pat(pat: str) -> Tuple[bool, Optional[str]]:
        """Validate Webex PAT and return user ID if valid."""
        webex_ops = WebexOps.get_instance(token=pat)  # Ensure you're using the get_instance method
        valid, user_id = webex_ops.validate_token()
        return valid, user_id


v = Validators()
