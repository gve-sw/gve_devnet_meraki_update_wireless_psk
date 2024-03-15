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

from webexteamssdk import WebexTeamsAPI
from config.config import Config
from logrr import lm
import os
from typing import Optional, ClassVar

c = Config.get_instance()


class WebexBot:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(WebexBot, cls).__new__(cls)
        return cls._instance

    def __init__(self, token=None):
        if not hasattr(self, '_initialized'):  # Avoid reinitialization
            self.api = None
            self.token = token or c.WEBEX_BOT_TOKEN
            self._initialized = False
            self.set_token_and_initialize(self.token)

    def set_token_and_initialize(self, token):
        self.token = token
        try:
            self.api = WebexTeamsAPI(access_token=self.token)
            self._initialized = True
            # lm.tsp("Webex API client initialized with new token.")
        except Exception as e:
            self._initialized = False
            lm.tsp(f"Error initializing Webex API with the provided token: {e}", style="bold red")

    def validate_token(self):
        if self._initialized:
            try:
                me = self.api.people.me()
                return True, me.id
            except Exception as e:
                lm.pp(f"Invalid or expired Webex Bot Token: {e}", style="error")
                return False, None
        else:
            lm.pp("API client not initialized or token not set.", style="error")
            return False, None

    @classmethod
    def get_instance(cls, token=None):
        instance = cls.__new__(cls)
        if token:
            instance.set_token_and_initialize(token)
        return instance

    def create_room(self, title):
        """Create a new room with the specified title."""
        try:
            room = self.api.rooms.create(title)
            lm.pp(f"Created new room: {title}")
            return room
        except Exception as e:
            lm.pp(f"Failed to create room {title}: {e}")
            # lm.pp(f"Please use a valid Webex Bot Token")
            # raise e

    def send_webex_message(self, message, file_paths=[]):
        """Send a message to a Webex space, optionally with file attachments."""
        room_id = os.getenv("WEBEX_ROOM_ID")  # Directly from environment to ensure freshness
        try:
            self.api.messages.create(roomId=room_id, text=message)
            # Check each file path and send only if the file exists
            for file_path in file_paths:
                if os.path.exists(file_path):
                    with open(file_path, "rb") as file:
                        self.api.messages.create(roomId=room_id, files=[file_path], text="Attached File")
                else:
                    lm.pp(f"File does not exist and cannot be sent: {file_path}")

        except Exception as e:
            lm.pp(f"Failed to send message via Webex Teams: {e}")
            # raise e

    def delete_room(self, room_id: str) -> bool:
        """Delete a Webex room by its ID."""
        try:
            self.api.rooms.delete(room_id)
            lm.pp(f"Deleted room with ID: {room_id}")
            return True
        except Exception as e:
            lm.pp(f"Failed to delete room {room_id}: {e}")
            return False

    def list_rooms(self) -> list:
        """List all rooms the bot is part of."""
        try:
            rooms = self.api.rooms.list()
            return [room for room in rooms]
        except Exception as e:
            lm.tsp(f"Failed to list rooms: {e}")
            return []

    def add_user_to_space(self, room_id: str, user_id: str):
        """Add a user to a space by user ID."""
        if not self._initialized or not self.api:
            lm.pp("Webex API client not initialized or token not set.", style="error")
            return
        try:
            lm.pp(f"Attempting to add user {user_id} to room {room_id}.", style="info")
            membership = self.api.memberships.create(roomId=room_id, personId=user_id)
            lm.pp(f"Successfully added user {user_id} to room {room_id}. Membership ID: {membership.id}", style="success")
        except Exception as e:
            lm.pp(f"Failed to add user {user_id} to room {room_id}: {e}", style="error")

    def is_user_in_room(self, room_id: str, user_id: str) -> bool:
        """Check if a user is already a member of a room.

        Args:
            room_id (str): The ID of the room.
            user_id (str): The ID of the user.

        Returns:
            bool: True if the user is a member of the room, False otherwise.
        """
        if not self._initialized or not self.api:
            lm.pp("Webex API client not initialized or token not set.", style="error")
            return False
        try:
            memberships = self.api.memberships.list(roomId=room_id)
            for membership in memberships:
                if membership.personId == user_id:
                    return True
            return False
        except Exception as e:
            lm.pp(f"Error checking user membership in room {room_id}: {e}", style="error")
            return False

class WebexOps:
    _instance: ClassVar[Optional['WebexOps']] = None

    def __init__(self, token=None):
        self.api = None
        self._initialized = None
        if not hasattr(self, '_initialized'):  # Avoid reinitialization
            self.token: str = token or c.WEBEX_PAT
            self.set_token_and_initialize(self.token)

    def set_token_and_initialize(self, token):
        self.token = token
        try:
            self.api = WebexTeamsAPI(access_token=self.token)
            self._initialized = True
            # lm.tsp("Webex API client initialized with new PAT.")
        except Exception as e:
            self._initialized = False
            lm.tsp(f"Error initializing Webex API with the provided PAT: {e}", style="bold red")

    def validate_token(self):
        if not self._initialized:
            return False, "PAT not set or API client not initialized."
        try:
            me = self.api.people.me()
            return True, me.id
        except Exception as e:
            lm.tsp(self.token)
            lm.tsp(f"Invalid or expired Webex PAT (Personal Access Token): {e}")
            return False, None

    @classmethod
    def get_instance(cls, token=None):
        instance = cls.__new__(cls)
        if token:
            instance.set_token_and_initialize(token)
        return instance

