from getpass import getpass

from netmiko import ConnectHandler
from ntc_templates.parse import parse_output

from SwitchConfig import CiscoSwitchConfig


# Switch login credentials
username = input('AD username: ')
password = getpass('Password: ')
enabled_pwd = getpass('Enable pwd: ')

# File containing list of switches to search
filename = 'switches.yml'

# Create configuration instance, load switch list from yml file. Object is
# strictly just used to read yml, this would be changed to use a service
# account in a web framework and list of switches would be read from
# database. Netmiko send_command and send_config_set in script below could be
# added as methods to the SwitchConfig module.
config_objs = CiscoSwitchConfig(username, password, enabled_pwd, filename)
switch_data = config_objs.load_file_info()
switches = config_objs.set_switch_dict(switch_data)


matching_switch = {}

# Set MAC to be searched and command to send to switches. In production,
# this would be gathered via a POST method on a web form.
mac_address = 'aaaa.bbbb.cccc'
cmd = f'show mac address-table address {mac_address}'

# Loop through switches and find interface connected to device with matching MAC
for switch in switches:
    try:
        # Connect to device using netmiko
        with ConnectHandler(device_type='cisco_ios',
                            host=switch,
                            username=username,
                            password=password,
                            secret=enabled_pwd,
                            global_delay_factor=3
                            ) as device:
            device.enable()
            output = device.send_command(cmd)
    except Exception as err:
        print(f'Issue connecting to device: {err}')
    else:
        # Strip last line of output
        modified_output = output[:output.rfind('\n')]
        # Parse output through ntc-templates for structured data
        mac_address_output = parse_output("cisco_ios", cmd, modified_output)
        mac_address_dict = mac_address_output[0]
        print(mac_address_dict)
        # Determine whether there is a match in MAC address table. If so,
        # ensure it is an edge interface. This logic assumes switches connect
        # to each other via PortChannels and thus would not match this criteria.
        if mac_address_dict.get('destination_port').startswith('Gi'):
            matching_switch['switch'] = switch
            matching_switch['interface'] = mac_address_dict.get(
                'destination_port')
print(matching_switch)

# Set config commands to send to switch. VLAN could be set via user input on
# web form if static VLAN not sufficient.
config_commands = [f"interface {matching_switch['interface']}",
                   'switchport access vlan 10']
try:
    with ConnectHandler(device_type='cisco_ios',
                        host=switch,
                        username=username,
                        password=password,
                        secret=enabled_pwd,
                        global_delay_factor=3
                        ) as device:
        device.enable()
        device.send_config_set(config_commands)
except Exception as err:
    print(f'Issue connecting to device {err}')

# TODO: verification to go back to switch and confirm changes.
