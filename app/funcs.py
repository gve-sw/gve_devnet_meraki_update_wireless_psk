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

from datetime import datetime
import json
from logrr import lm
from config.config import Config
import os


c = Config.get_instance()

def safe_fetch(default_return_value=None):
    if default_return_value is None:
        default_return_value = []

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                lm.tsp(f"Failed to fetch data: {e}")
                return default_return_value

        return wrapper

    return decorator


def format_response(response):
    # Since we are now saving to JSON, the response formatting can be left as is (dictionary format)
    return response


def generate_reports(successful_updates, failed_updates, base_data_path="/mnt/data"):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    success_file_path = os.path.join(c.DATA_FILE_PATH, f"successful_psk_changes_{timestamp}.json")
    failure_file_path = os.path.join(c.DATA_FILE_PATH, f"unsuccessful_psk_changes_{timestamp}.json")

    if successful_updates:
        with open(success_file_path, 'w') as sfile:
            json.dump(successful_updates, sfile, indent=4)

    if failed_updates:
        with open(failure_file_path, 'w') as ffile:
            json.dump(failed_updates, ffile, indent=4)

    return success_file_path, failure_file_path


