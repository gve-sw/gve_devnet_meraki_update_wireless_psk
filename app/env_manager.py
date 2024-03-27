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

from dotenv import load_dotenv, set_key
import os
from pathlib import Path
import typer
from validator import v
from logrr import lm
from config.config import Config
from pydantic import ValidationError
from typing import ClassVar, Optional
from webex_api import WebexBot

ENV_PATH = Path(__file__).parent / 'config' / '.env'


class EnvironmentManager:
    _instance: ClassVar[Optional['EnvironmentManager']] = None

    def __init__(self, env_path: Path):
        self.env_path = env_path

    @staticmethod
    def reload_config():
        Config._instance = None  # Reset the singleton instance
        try:
            global c
            c = Config.get_instance()  # Attempt to reload the config
            # print("Configuration reloaded successfully.")
            # lm.print_inspect_info(c)
        except ValidationError as e:
            lm.pp(f"Failed to reload config: {e}")
            typer.Exit(code=1)

    @classmethod
    def get_instance(cls) -> 'EnvironmentManager':
        """Returns a singleton instance of MerakiOps."""
        if cls._instance is None:
            cls._instance = cls(env_path=ENV_PATH)
        return cls._instance

    def create_and_load_env_if_missing(self):
        if not self.env_path.exists():
            self.env_path.touch()
        load_dotenv(dotenv_path=self.env_path)
        self.reload_config()

    def ensure_env_set(self, var_name: str, prompt_message: str, validation_func=lambda x: True, callback=None):
        while True:
            var_value = os.getenv(var_name)
            if not var_value or not validation_func(var_value):
                var_value = typer.prompt(prompt_message)
                if validation_func(var_value):
                    os.environ[var_name] = var_value
                    set_key(self.env_path.as_posix(), var_name, var_value, quote_mode="never")
                    load_dotenv(dotenv_path=self.env_path)
                    self.reload_config()
                    if callback:
                        callback()  # Reload configuration after setting
                    lm.lnp(f"{var_name} is set and valid.", style="success")
                    break
                else:
                    lm.lnp(f"Invalid value for {var_name}. Please try again.", style="error")
            else:
                if callback:
                    callback()  # Optionally reload configuration if needed
                lm.lnp(f"{var_name} is already set and valid.", style="success")
                break

    def set_env_var(self, var_name: str, var_value: str, callback=None):
        """Set an environment variable and update the .env file."""
        os.environ[var_name] = var_value
        set_key(self.env_path.as_posix(), var_name, var_value, quote_mode="never")
        self.reload_config()
        if callback:
            callback()  # Reload configuration after setting
        lm.pp(f"{var_name} is set and valid.", style="success")

    def ensure_meraki_api_key_set(self, callback=None):
        self.ensure_env_set(
            var_name="MERAKI_API_KEY",
            prompt_message="MERAKI_API_KEY is not set. Please enter it",
            validation_func=v.validate_meraki_api_key,
            callback=callback
        )
        # lm.tsp("MERAKI_API_KEY is valid.", style="bright_green")

    def ensure_bot_token_set(self, callback=None):
        self.ensure_env_set(
            var_name="WEBEX_BOT_TOKEN",
            prompt_message="WEBEX_BOT_TOKEN is not set. Enter Webex BOT Token",
            validation_func=v.validate_webex_bot_token,
            callback=callback
        )
        # lm.tsp("WEBEX_BOT_TOKEN is valid.", style="webex")

    def ensure_pat_set(self, callback=None) -> Optional[str]:
        """Ensure the Webex PAT is set and valid, and obtain the user ID.

        Returns:
            Optional[str]: The user ID if the PAT is valid, None otherwise.
        """
        while True:
            pat = os.getenv("WEBEX_PAT")
            if not pat:
                pat = typer.prompt("WEBEX_PAT is not set. Enter Webex PAT")
            valid, user_id = v.validate_webex_pat(pat)
            if valid:
                os.environ["WEBEX_PAT"] = pat
                set_key(self.env_path.as_posix(), "WEBEX_PAT", pat, quote_mode="never")
                load_dotenv(dotenv_path=self.env_path)  # Ensure the environment is reloaded with the new PAT
                if user_id:
                    os.environ["WEBEX_USER_ID"] = user_id
                    set_key(self.env_path.as_posix(), "WEBEX_USER_ID", user_id, quote_mode="never")
                self.reload_config()
                if callback:
                    callback()  # Reload configuration after setting
                lm.pp("WEBEX_PAT is valid and user ID obtained.", style="success")
                return user_id  # Return the user ID upon successful validation
            else:
                lm.pp("Invalid WEBEX_PAT. Please try again.", style="error")
                os.environ.pop("WEBEX_PAT", None)  # Remove the invalid PAT from the environment
                # Don't return from the function here; instead, continue the loop for another attempt

    def ensure_webex_room_id_set(self, webex_bot: WebexBot, room_name: Optional[str], user_id: str) -> str:
        room_id = os.getenv("WEBEX_ROOM_ID")
        if not room_id or room_name:
            if not room_name:
                room_name = typer.prompt("Enter a Webex room name to create for notifications")
            room = webex_bot.create_room(room_name)
            room_id = room.id
            self.set_env_var("WEBEX_ROOM_ID", room_id)
            self.reload_config()
            if not webex_bot.is_user_in_room(room_id, user_id):
                webex_bot.add_user_to_space(room_id, user_id)
        return room_id
