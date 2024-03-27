# gve_devnet_meraki_psk_change_dashboard
This application utilizes the Meraki API to efficiently manage and update Cisco Meraki network SSID PSKs across multiple networks simultaneously. 
It employs Typer, offering an intuitive command-line interface for various options and functionalities. 
Specifically, it targets networks tagged with specific identifiers, allowing selective updates to wireless SSIDs, including password changes. 
It includes the ability to list organizations, networks, and SSIDs, as well as update SSID PSKs for a specific SSID within a single network.
It provides the capability to update PSKs for MR and MX wireless networks through separate API calls.
Additionally, it provides the option to set up Webex notifications for script executions, allowing for real-time updates on the script's progress and results.
This capability is vital for maintaining secure and efficient network operations, particularly in environments requiring frequent updates to wireless access credentials.

## Contacts
* Mark Orszycki


## Solution Components
* [Meraki API](https://developer.cisco.com/meraki/api-v1/)
* [Typer](https://typer.tiangolo.com/)
* Meraki MR Wireless
* Meraki MX Wireless


## Prerequisites
#### Meraki API Keys
In order to use the Meraki API, you need to enable the API for your organization first. After enabling API access, you can generate an API key. Follow these instructions to enable API access and generate an API key:
1. Login to the Meraki dashboard
2. In the left-hand menu, navigate to `Organization > Settings > Dashboard API access`
3. Click on `Enable access to the Cisco Meraki Dashboard API`
4. Go to `My Profile > API access`
5. Under API access, click on `Generate API key`
6. Save the API key in a safe place. The API key will only be shown once for security purposes, so it is very important to take note of the key then. In case you lose the key, then you have to revoke the key and a generate a new key. Moreover, there is a limit of only two API keys per profile.

> For more information on how to generate an API key, please click [here](https://developer.cisco.com/meraki/api-v1/#!authorization/authorization).
> Note: You can add your account as Full Organization Admin to your organizations by following the instructions [here](https://documentation.meraki.com/General_Administration/Managing_Dashboard_Access/Managing_Dashboard_Administrators_and_Permissions).

#### Optional: Create Cisco Webex Bot
Create a Webex Chatbot from [here](https://developer.webex.com/my-apps/new/bot) and save the bot token somewhere safe.
Retrieve your Webex Personal Access Token, so the bot can add you to the Webex Room it creates: [here.](https://developer.webex.com/docs/getting-your-personal-access-token.)


## Installation/Configuration
1. Clone this repository with `git clone https://github.com/gve-sw/gve_devnet_meraki_update_wireless_psk`. To find the repository name, click the green `Code` button above the repository files. Then, the dropdown menu will show the https domain name.
2. Retrieve your Meraki API key.
3. (Optional) If using Webex for notification, retrieve your Webex Bot Token and Webex PAT.
4. Set up a Python virtual environment. Make sure Python 3 is installed in your environment, and if not, you may download Python [here](https://www.python.org/downloads/). Once Python 3 is installed in your environment, you can activate the virtual environment with the instructions found [here](https://docs.python.org/3/tutorial/venv.html).
5. Install the requirements with `pip install -r requirements.txt`
6. Proceed to 'Usage' section.


## Usage
Simply run the script. You will be prompted to enter the necessary environment variables to proceed.
I encourage the use of the --help flag:
```
python main.py --help
python main.py update_psk-tagged-networks --help
```

### Update SSID PSKs Across Tagged Networks
To update the PSKs for networks tagged with specific identifiers, use the following command:
```
python main.py update_psk-tagged-networks
```
*Note: This targets SSID number 3 accross all networks in the Meraki Organization. You can change this by using the --psk_number flag.*

### List Organizations
To list all Meraki organizations accessible with your API key, use the following command:
```
python main.py list-orgs
```
### List Networks in an Organization
To list all networks within a specified Meraki organization, you will need the organization ID:
```
python main.py list-networks <organization_id>"
```
### List SSIDs for a Network
To list all SSIDs for a given network, you will need the network ID and specify the network type (mrw for wireless, mxw for appliance):
```
python main.py list_ssids <network_id> <mrw | mx>
```
### Update SSID PSK for a Specific SSID
This command allows you to update the PSK for a specific SSID by its name or number within a single network. 
If both name and number are provided, the update defaults to using the SSID number.
```
python main.py update_ssid_psk<network_id><ssid_name>" --psk "<new_psk>"
```
### Setup with Webex Notifications
For setup that includes Webex notifications, use:
```
python main.py run-with-webex \
  --psk <YOUR_PSK> \
  --meraki_api_key <YOUR_API_KEY> \
  --webex_bot_token <YOUR_BOT_TOKEN> \
  --webex_pat <YOUR_PAT> \
  --room_name <YOUR_ROOM_NAME>
```
For future script executions, use: python main.py run-with-webex


# Screenshots
![/images/help.png](/images/help.png)<br>
![/images/list_orgs.png](/images/list_orgs.png)<br>
![/images/run-with-webex-help.png](/images/run-with-webex-help.png)<br>
![/images/list_networks.png](/images/list_networks.png)<br>
![/images/update-psk-tagged-networks.png](/images/update-psk-tagged-networks.png)<br>


### LICENSE
Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.md)

### CODE_OF_CONDUCT
Our code of conduct is available [here](CODE_OF_CONDUCT.md)

### CONTRIBUTING
See our contributing guidelines [here](CONTRIBUTING.md)

#### DISCLAIMER:
<b>Please note:</b> This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.