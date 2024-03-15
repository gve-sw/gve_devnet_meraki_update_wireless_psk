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

import typer
from pathlib import Path
from typing import Optional, Tuple
from config.config import Config
from webex_api import WebexBot
from logrr import lm
from meraki_api import MerakiOps
from env_manager import EnvironmentManager
from funcs import generate_reports

ENV_PATH = Path(__file__).parent / 'config' / '.env'
env_manager = EnvironmentManager.get_instance()
c = Config.get_instance()

# Typer App
app = typer.Typer()


def common_setup():
    env_manager.create_and_load_env_if_missing()
    env_manager.ensure_meraki_api_key_set(callback=env_manager.reload_config)


@app.callback()
def main_callback():
    """
    This callback is run before any command.
    """
    common_setup()


def run_psk_change(psk: str, send_webex_message: bool):
    """
    Executes the PSK change across Meraki networks based on predefined tags.
    Optionally sends a Webex message with the outcome.
    """
    meraki_ops = MerakiOps.get_instance()
    org_id = meraki_ops.get_org_id()
    successful_updates, failed_updates = meraki_ops.update_ssid_by_num_for_tagged_networks(new_psk=psk, org_id=org_id)
    if successful_updates or failed_updates:
        success_file, failure_file = generate_reports(successful_updates, failed_updates)  # Implement this function to generate report files

        if send_webex_message:
            webex_bot = WebexBot.get_instance()
            webex_bot.send_webex_message("PSK Change Report", [success_file, failure_file])  # Ensure webex_api is properly initialized and configured


def psk_prompt(psk: Optional[str] = None, send_webex_message: bool = False):
    """
    Prompts the user for a PSK and executes the PSK change across networks.
    Optionally sends a notification to a Webex room with the results.

    Args:
        psk (Optional[str], optional): The PSK to apply. Will prompt if not provided.
        send_webex_message (bool, optional): Whether to send a Webex notification.
    """
    if not psk:
        psk = typer.prompt("Please enter a PSK to run the PSK change")
    lm.pp(f"The PSK you entered is: {psk}")
    if typer.confirm("Continue with changing across networks?"):
        run_psk_change(psk=psk, send_webex_message=send_webex_message)
    else:
        lm.tsp("PSK change aborted.", style="error")


def handle_network_id_input(meraki_ops):
    if typer.confirm("Do you have the network ID?"):
        return typer.prompt("Please enter the network ID")
    elif typer.confirm("Would you like to list available networks in your organization?"):
        org_id = meraki_ops.get_org_id()
        networks = meraki_ops.get_networks(org_id=org_id)
        for network in networks:
            typer.echo(f"Name: {network['name']}, ID: {network['id']}")
        return typer.prompt("Please enter the network ID from the list above")
    else:
        typer.echo("Operation cancelled by the user.")
        raise typer.Exit()


def handle_network_type_input() -> str:
    while True:
        network_type = typer.prompt("Please enter the network type (mrw or mxw)")
        if network_type.lower() in ['mrw', 'mxw']:
            return network_type.lower()
        lm.pp("Invalid network type. Must be 'mrw' or 'mxw'.", style="red")


def handle_ssid_choice() -> Tuple[Optional[str], Optional[int]]:
    """
    Prompts the user to decide whether to update the SSID by name or by number
    and collects the corresponding input.

    Returns:
        A tuple containing the SSID name (str) if chosen, or the SSID number (int) if chosen,
        with the other value set to None.
    """
    while True:
        ssid_choice = typer.prompt("Do you want to update by SSID name or number? Enter 'name' or 'number'")
        if ssid_choice.lower() == 'name':
            ssid_name = typer.prompt("Please enter the SSID name you'd like to change")
            return ssid_name, None
        elif ssid_choice.lower() == 'number':
            ssid_number = typer.prompt("Please enter the SSID number you'd like to change", type=int)
            return None, ssid_number
        else:
            lm.pp("Invalid input. You must enter 'name' or 'number'.", style="red")


def handle_psk_input() -> str:
    while True:
        psk = typer.prompt("Please enter the PSK (8-63 alphanumeric characters)")
        if 8 <= len(psk) <= 63 and psk.isalnum():
            return psk
        lm.pp("Invalid PSK. Must be 8-63 alphanumeric characters long.", style="error")


@app.command()
def webex_delete_room(room_id: str):
    """
    Deletes a specified Webex room by its ID.

    Args:
        room_id (str): The ID of the Webex room to delete.
    """
    env_manager.ensure_bot_token_set(callback=env_manager.reload_config)  # pass reload_config without invoking it
    webex_bot_token = c.WEBEX_BOT_TOKEN
    webex_bot = WebexBot.get_instance(webex_bot_token)
    if not webex_bot.delete_room(room_id):
        lm.tsp(f"Failed to delete room with ID: {room_id}", style="error")
    else:
        lm.tsp(f"Room with ID: {room_id} has been successfully deleted.", style="success")


@app.command()
def webex_list_rooms():
    """Lists all Webex rooms the bot is part of."""
    env_manager.ensure_bot_token_set(callback=env_manager.reload_config)  # pass reload_config without invoking it
    webex_bot_token = c.WEBEX_BOT_TOKEN

    webex_bot = WebexBot.get_instance(webex_bot_token)
    rooms = webex_bot.list_rooms()
    if rooms:
        lm.tsp("Rooms:", style="webex")
        for room in rooms:
            lm.tsp(f"- ID: {room.id} Name: {room.title}")
    else:
        lm.pp("No rooms found or unable to list rooms.", style="error")


@app.command()
def webex_run_meraki_psk_change(
        psk: Optional[str] = typer.Option(None, help="The PSK to use for the change. Will be prompted if left blank."),
        meraki_api_key: Optional[str] = typer.Option(None, help="Your Meraki API key. Will be prompted if left blank."),
        webex_bot_token: Optional[str] = typer.Option(None, help="Your Webex bot token. Will be prompted if left blank."),
        webex_pat: Optional[str] = typer.Option(None, help="Your Webex Personal Access Token. Will be prompted if left blank."),
        room_name: Optional[str] = typer.Option(None, help="The name of the Webex room for notifications. A new room will be created if this is provided.")
):
    """
    Executes the PSK (Pre-shared Key) change process for Meraki SSIDs and uses a bot to send a Webex notification about the operation's results.
    """
    if meraki_api_key:
        env_manager.set_env_var("MERAKI_API_KEY", meraki_api_key)
    if webex_bot_token:
        env_manager.set_env_var("WEBEX_BOT_TOKEN", webex_bot_token)
    if webex_pat:
        env_manager.set_env_var("WEBEX_PAT", webex_pat)

    env_manager.ensure_meraki_api_key_set()
    env_manager.ensure_bot_token_set()

    user_id = env_manager.ensure_pat_set()  # Obtain the user ID after PAT validation

    webex_bot = WebexBot(webex_bot_token)

    # Check if WEBEX_ROOM_ID is set, if not or a new room_name is provided, create/get the room
    room_id = env_manager.ensure_webex_room_id_set(webex_bot, room_name, user_id)
    if room_id:
        env_manager.set_env_var("WEBEX_ROOM_ID", room_id)

    # Now that we have the room_id and user_id, add the user to the room
    webex_bot.add_user_to_space(room_id, user_id)

    psk = psk or typer.prompt("Please enter a PSK to run the PSK change")
    # Assuming run_psk_change is a function that executes the PSK change
    run_psk_change(psk=psk, send_webex_message=True)


@app.command()
def update_psk_tagged_networks(psk: str = typer.Argument(None, help="The PSK to use for the change. Will be prompted if left blank.")):
    """
    Updates the PSK for all mrw & mxw network types with tag "GuestPSK" across all networks in a Meraki Organization. If API key or PSK left blank, the user will be prompted.
    """
    psk = psk or typer.prompt("Please enter a PSK to run the PSK change")
    run_psk_change(psk=psk, send_webex_message=False)


@app.command()
def list_orgs():
    """Lists all Meraki organizations accessible with the API key."""
    # env_manager.create_and_load_env_if_missing()
    # env_manager.ensure_meraki_api_key_set(callback=env_manager.reload_config)
    meraki_ops = MerakiOps.get_instance()
    orgs = meraki_ops.get_orgs()
    if orgs:
        typer.echo("Organizations:")
        for org in orgs:
            lm.pp(f"- Name: {org['name']}, ID: {org['id']}")
    else:
        lm.pp("No organizations found or unable to list organizations.", style="error")


@app.command()
def list_networks(org_id: str):
    """Lists all networks within a specified Meraki organization."""
    meraki_ops = MerakiOps.get_instance()
    networks = meraki_ops.get_networks(org_id=org_id)
    if networks:
        lm.pp(f"Networks in Organization ID {org_id}:")
        # lm.pp(networks)
        for network in networks:
            lm.pp(f"- Name: {network['name']}, ID: {network['id']} ")
    else:
        lm.pp(f"No networks found or unable to list networks for organization ID {org_id}.", style="error")


@app.command()
def list_ssids(network_id: str, network_type: str = "mrw"):
    """
    Lists all SSIDs for a given network and type ('mrw' for wireless, 'mxw' for appliance).
    """
    meraki_ops = MerakiOps.get_instance()
    try:
        ssids = meraki_ops.fetch_ssids(network_id, network_type)
        if ssids:
            typer.echo(f"SSIDs in Network ID {network_id}:")
            for ssid in ssids:
                typer.echo(f"- Number: {ssid['number']}, Name: {ssid['name']}")
        else:
            typer.echo(f"No SSIDs found or unable to list SSIDs for network ID {network_id}.")
    except ValueError as e:
        typer.echo(str(e))


@app.command()
def update_ssid_psk(
        network_id: Optional[str] = typer.Option(None, help="The wireless network ID. Will be prompted if left blank."),
        ssid_name: Optional[str] = typer.Option(None, help="The SSID name to change the PSK on."),
        ssid_number: Optional[int] = typer.Option(None, help="The SSID number to change the PSK on."),
        psk: Optional[str] = typer.Option(None, help="The PSK to use for the change. Will be prompted if left blank."),
        network_type: Optional[str] = typer.Option("mrw", "--type", help="Network type: 'mrw' for MR wireless, 'mxw' for MX appliance wireless.")
):
    """
    Update the PSK for a specific SSID by its name or number within a single network. If both name and number are provided,
    the update defaults to using ssid number.
    """

    meraki_ops = MerakiOps.get_instance()
    if network_id is None:
        network_id = handle_network_id_input(meraki_ops)
    if ssid_name is None and ssid_number is None:
        ssid_name, ssid_number = handle_ssid_choice()
    if psk is None:
        psk = handle_psk_input()
    if network_type is None:
        network_type = handle_network_type_input()

    try:
        if ssid_name and ssid_number is not None:
            # If both are provided, use number
            ssid_details = meraki_ops.update_ssid_psk_by_num(network_id=network_id, ssid_number=ssid_number, psk=psk, network_type=network_type)
            ssid_name = ssid_details.get("name")
            lm.pp(f"PSK updated successfully for SSID Name: {ssid_name} SSID number {ssid_number} in network ID {network_id}.", style="success")
        elif ssid_name:
            # Update by SSID name
            result = meraki_ops.update_ssid_psk_by_name_for_network(network_id=network_id, ssid_name=ssid_name, psk=psk, network_type=network_type)
            lm.pp(f"PSK updated successfully for SSID '{ssid_name}' in network ID {network_id}.", style="success")
        elif ssid_number is not None:
            # Update by SSID number
            result = meraki_ops.update_ssid_psk_by_num(network_id=network_id, ssid_number=ssid_number, psk=psk, network_type=network_type)
            ssid_name = result.get("name")
            lm.pp(f"PSK updated successfully for SSID Name: {ssid_name} SSID number {ssid_number} in network ID {network_id}.", style="success")
    except Exception as e:
        lm.pp(f"Failed to update PSK.")
        lm.print_inspect_info(e)


if __name__ == "__main__":
    app()
