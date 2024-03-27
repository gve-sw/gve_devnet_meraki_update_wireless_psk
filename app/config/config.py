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

import pathlib
import re
from typing import Optional, ClassVar, List, Dict, Any
from dotenv import load_dotenv
from pydantic import ValidationError
from pydantic_settings import BaseSettings
import json
from datetime import datetime

# Adjust the path to load the .env file from the project root.
env_path = pathlib.Path(__file__).parents[0] / '.env'
# print(f'env path: {env_path}')  # for debugging
load_dotenv(dotenv_path=env_path)


class Config(BaseSettings):
    _instance: ClassVar[Optional['Config']] = None

    # DIR PATHS
    DIR_PATH: ClassVar[pathlib.Path] = pathlib.Path(__file__).parents[2]
    ENV_FILE_PATH: ClassVar[str] = str(DIR_PATH / 'app' / 'c' / '.env')
    DATA_FILE_PATH: ClassVar[str] = str(DIR_PATH / 'app' / 'data' )
    README_PATH: ClassVar[str] = str(DIR_PATH / 'README.md')

    # App Settings
    APP_NAME: ClassVar[str] = "Meraki PSK Change App"
    APP_VERSION: ClassVar[str] = "1.0"
    LOGGER_LEVEL: ClassVar[str] = 'DEBUG'

    # Meraki Integration settings
    MERAKI_API_KEY: Optional[str] = ""
    MERAKI_BASE_URL: str = "https://api.meraki.com/api/v1/"
    WEBEX_BOT_TOKEN: Optional[str] = ""
    WEBEX_ROOM_ID: Optional[str] = ""
    WEBEX_PAT: Optional[str] = ""

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


