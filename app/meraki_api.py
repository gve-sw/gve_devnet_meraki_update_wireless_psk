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

from rich.prompt import Prompt
from meraki.exceptions import APIError
import meraki
from config.config import Config
from logrr import lm
from funcs import safe_fetch
import time
import threading
from typing import Optional, ClassVar, List, Dict, Any

c = Config.get_instance()


class MerakiOps:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(MerakiOps, cls).__new__(cls)
        return cls._instance

    def __init__(self, api_key=None):
        self.api_key = api_key or c.MERAKI_API_KEY
        self.dashboard = None
        self._initialized = False
        self.initialize_dashboard()
        self.psk_number = 2

    def initialize_dashboard(self):
        """Initialize the Meraki Dashboard API with the provided API key."""
        try:
            self.dashboard = meraki.DashboardAPI(api_key=self.api_key, suppress_logging=True, caller=c.APP_NAME)
            self._initialized = True
        except APIError as e:
            self._initialized = False
            lm.tsp(f"[bold red]Error with Meraki API: {e}[/bold red]")
        except Exception as e:
            self._initialized = False
            lm.tsp(f"[bold red]General error initializing Meraki Dashboard: {e}[/bold red]")

    def validate_api_key(self):
        """Validate the Meraki API Key by attempting to list the organizations."""
        if not self.dashboard:
            return False, "Dashboard not initialized."
        try:
            orgs = self.dashboard.organizations.getOrganizations()
            if orgs:
                return True, "Meraki API Key is valid."
            else:
                return False, "No organizations found with the provided API key."
        except meraki.APIError as e:
            return False, f"API Error: {e}"

    @classmethod
    def get_instance(cls) -> 'MerakiOps':
        """Returns a singleton instance of MerakiOps."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_orgs(self):
        """ Get meraki orgs  with rate limiting  wrapper """
        return self.dashboard.organizations.getOrganizations()

    def get_org_detail(self, org_id: str):
        """
        Get detailed information for a specific organization.
        """
        org_details = self.dashboard.organizations.getOrganization(org_id)
        lm.print_inspect_info(org_details)
        if org_details is None:
            lm.tsp(f"Failed to get organization details for org_id: {org_id}")
        return org_details

    def get_org_id(self):
        """
        Fetch the org ID based on org name, or prompt the user to select
        an organization if the name is left blank or is invalid. If there is only one
        organization, it selects that organization automatically. Exits the script if
        the organization is not found or if there's an error fetching the organizations.
        """

        # with lm.console.status("[bold green]Fetching Meraki Organizations....", spinner="dots"):
        #     try:
        #         orgs = self.dashboard.organizations.getOrganizations()
        #     except APIError as e:
        #         lm.tsp(f"Failed to fetch organizations. Error: {e.message['errors'][0]}")
        #         sys.exit(1)
        lm.p_panel("Fetching Meraki organizations...", style="green")
        with lm.console.status("[bold green]Fetching Meraki Organizations....", spinner="dots"):
            orgs = self.get_orgs()

        # lm.tsp("[bold bright_green]Connected to Meraki dashboard!")
        lm.pp(f"Found {len(orgs)} organization(s).")

        # If one org, return early
        if len(orgs) == 1:
            lm.pp(f"Working with Org: {orgs[0]['name']}\n")
            return orgs[0]["id"]
        org_names = [org["name"] for org in orgs]
        lm.pp("Available organizations:")
        for org in orgs:
            lm.tsp(f"- {org['name']}")
        lm.tsp("[bold red]\nNote: Meraki organization names are case sensitive")
        selection = Prompt.ask(
            "Which organization should we use?", choices=org_names, show_choices=False
        )
        organization_name = selection  # Update organization_name with the user's selection

        for org in orgs:
            if org["name"] == organization_name:
                return org["id"]

        lm.tsp(f"[bold red]Organization with name '{organization_name}' not found.[/bold red]")
        exit(1)

    def get_networks(self, org_id: str):
        """
        Collect existing Meraki network names / IDs
        """
        # lm.p_panel("[bold bright_green]Retrieving Network(s) Information[/bold bright_green]", title="Step 3")
        # Fetching the networks before applying any filter.
        networks = self.dashboard.organizations.getOrganizationNetworks(organizationId=org_id)
        # lm.pp(f"Available networks {networks}")
        return networks

    def update_ssid_by_num_for_tagged_networks(self, new_psk: str, org_id: str):
        """
        Update SSID settings for networks tagged with 'GuestPSK' or 'MX-WGuestPSK'.
        """
        successful_updates = []
        failed_updates = []
        all_networks = self.get_networks(org_id=org_id)

        # Retrieve & loop through all networks within the organization
        for network in all_networks:
            network_id = network['id']
            network_tags = network.get('tags', [])

            # Handle networks tagged 'GuestPSK'
            if 'MX-GuestPSK' or 'Test' in network_tags:
                try:
                    lm.pp(f"Changing PSK for network: {network_id} with tag 'GuestPSK': {new_psk}")
                    self.dashboard.wireless.updateNetworkWirelessSsid(network_id, number=self.psk_number, psk=new_psk)
                    update_result = f"Updated Wireless SSID for '{network['name']}' with ID '{network_id}'"
                    successful_updates.append(update_result)
                except Exception as e:
                    update_result = f"Failed to update Wireless SSID for '{network['name']}': {e}"
                    failed_updates.append(update_result)

            # Handle networks tagged 'MX-WGuestPSK'
            elif 'MXW-GuestPSK' in network_tags:
                try:
                    lm.pp(f"Changing PSK for network: {network_id} with tag 'MX-WGuestPSK': {new_psk}")
                    self.dashboard.appliance.updateNetworkApplianceSsid(network_id, number=self.psk_number, psk=new_psk)
                    update_result = f"Updated Appliance SSID for '{network['name']}' with ID '{network_id}'"
                    successful_updates.append(update_result)
                except Exception as e:
                    update_result = f"Failed to update Appliance SSID for '{network['name']}': {e}"
                    failed_updates.append(update_result)
            # For saving to file & sending update summary to Webex
            message = "SSID Update Summary:\n\n"
            if successful_updates:
                message += "Successful Updates:\n" + "\n".join(successful_updates) + "\n\n"
                lm.pp(successful_updates)
            if failed_updates:
                message += "Failed Updates:\n" + "\n".join(failed_updates)
                lm.pp(failed_updates)

        return successful_updates, failed_updates

    def fetch_ssids(self, network_id: str, network_type: str):
        """Fetch SSIDs for a network, given its type ('mrw' or 'mxw')."""
        if network_type == 'mrw':
            return self.dashboard.wireless.getNetworkWirelessSsids(network_id)
        elif network_type == 'mxw':
            return self.dashboard.appliance.getApplianceWireless(network_id=network_id)
        else:
            raise ValueError("Unsupported network type")

    def get_ssid_num(self, network_id: str, ssid_name: str, network_type: str):
        """Fetches the SSID number based on the SSID name."""
        ssids = self.fetch_ssids(network_id, network_type)
        for ssid in ssids:
            if ssid['name'] == ssid_name:
                return ssid['number']
        raise ValueError("SSID not found")

    def get_ssid_details_by_num(self, network_id: str, ssid_number: int, network_type: str) -> dict:
        """
        Fetches SSID details for a given SSID number within a network.
        """
        if network_type == 'mrw':
            ssid_details = self.dashboard.wireless.getNetworkWirelessSsid(network_id, number=ssid_number)
        elif network_type == 'mxw':
            ssid_details = self.dashboard.appliance.getApplianceWireless(network_id, number=ssid_number)
        else:
            raise ValueError("Unsupported network type")
        return ssid_details

    def update_ssid_psk_by_num(self, network_id: str, ssid_number: int, psk: str, network_type: str):
        """Updates the PSK for an SSID."""
        if network_type == 'mrw':
            self.dashboard.wireless.updateNetworkWirelessSsid(network_id, number=ssid_number, psk=psk)
        elif network_type == 'mxw':
            self.dashboard.appliance.updateNetworkAppliance(network_id, number=ssid_number, psk=psk)
        else:
            raise ValueError("Unsupported network type")
        # Fetch and return the updated SSID details.
        ssid_details = self.get_ssid_details_by_num(network_id, ssid_number, network_type=network_type)
        return ssid_details

    def update_ssid_psk_by_name_for_network(self, network_id: str, ssid_name: str, psk: str, network_type: str):
        """Update a sigle SSID PSK for a specific network by SSID name."""
        try:
            if network_type == "mrw":
                ssid_number = self.get_ssid_num(network_id, ssid_name, network_type=network_type)
                self.update_ssid_psk_by_num(network_id, ssid_number, psk, network_type=network_type)
                lm.tsp(f"[bold green]PSK updated for MR wireless network '{network_id}' with SSID name: '{ssid_name}'.[/bold green]")
            elif network_type == "mxw":
                # Implement the logic for MXW if applicable
                pass
        except ValueError as e:
            # This block will execute if the SSID name is not found
            lm.tsp(f"[bold red]Error: SSID '{ssid_name}' not found in the network ID {network_id}. No PSK updates were made.[/bold red]")

    def update_ssid_psk_by_name_for_all_networks(self, ssid_name: str, psk: str, network_type: str):
        """Update SSID PSK for networks by SSID name and optional network tag."""
        org_id = self.get_org_id()
        networks = self.get_networks(org_id=org_id)
        update_successful = False
        ssid_not_found = True

        for network in networks:
            network_id = network['id']
            try:
                if network_type == "mrw":
                    ssid_number = self.get_ssid_num(network_id, ssid_name, network_type=network_type)
                    self.update_ssid_psk_by_num(network_id, ssid_number, psk, network_type=network_type)
                    lm.tsp(f"[bold green]PSK updated for MR wireless network '{network['name']}' with SSID name: '{ssid_name}'.[/bold green]")
                    update_successful = True
                    ssid_not_found = False
                elif network_type == "mxw":
                    # Similar logic for MXW if applicable
                    pass
            except ValueError as e:
                # This block will execute if SSID name is not found in the current iteration/network
                continue

        if ssid_not_found:
            lm.tsp(f"[bold yellow]Warning: SSID '{ssid_name}' not found in any network. No PSK updates were made.[/bold yellow]")
        elif update_successful:
            lm.tsp(f"[bold green]PSK update operation completed successfully for SSID: '{ssid_name}'.[/bold green]")
        else:
            lm.tsp(f"[bold red]Error: The PSK update operation failed for SSID: '{ssid_name}'. Please check the network type and SSID name.[/bold red]")

