import yaml
from napalm import get_network_driver
from netmiko import ConnectHandler
from ciscoconfparse import CiscoConfParse
from ntc_templates.parse import parse_output
from jinja2 import Environment, FileSystemLoader


class CiscoSwitchConfig:

    def __init__(self, username, password, enable_pwd, filename):
        self.username = username
        self.password = password
        self.enable_pwd = enable_pwd
        self.filename = filename

    def load_file_info(self):
        try:
            with open(self.filename) as f_obj:
                switch_data = yaml.load(f_obj, Loader=yaml.FullLoader)
                return switch_data
        except Exception as err:
            print(f'Error loading yaml file: {err}')

    def print_connecting(self, hostname):
        print(f'Connecting to {hostname}...')

    def print_connection_err(self, err, hostname):
        print(f'Issue connecting to {hostname}: {err}')

    def set_switch_params(self, switch_data):
        try:
            parent_cfg = switch_data['config']['parent']
            current_child_cfg = switch_data['config']['current_child']
            desired_child_cfg = switch_data['config']['desired_child']
            return parent_cfg, current_child_cfg, desired_child_cfg
        except Exception as err:
            print(f'Error reading yaml data: {err}')

    def set_switch_dict(self, switch_data):
        try:
            switch_dict = switch_data['switches']
            return switch_dict
        except Exception as err:
            print(f'Error reading yaml data: {err}')

    def get_switch_config(self, mgmt_ip, hostname):
        print(f'Connecting to {hostname}...')
        try:
            with get_network_driver('ios')(
                mgmt_ip,
                self.username,
                self.password,
                optional_args={
                    'secret': self.enable_pwd,
                    'inline_transfer': True,
                    'global_delay_factor': 1,
                    }
                    ) as device:
                sw_config = device.get_config()
                return sw_config['running']
        except Exception as err:
            print(f'Issue connecting to {hostname}: {err}')
            raise err

    def save_config_text(self, sw_config, hostname):
        with open(f'{hostname}_currentconfig.txt', 'w') as f_obj:
            f_obj.write(sw_config)

    def identify_parent_cnfgs(self, sw_config, parent_cfg, current_child_cfg):
        config_obj = CiscoConfParse(config=sw_config.split('\n'))
        parent_cnfgs = config_obj.find_objects(f'^{parent_cfg}')
        configs_to_change = []
        for config_line in parent_cnfgs:
            if config_line.re_search_children(f'{current_child_cfg}$'):
                configs_to_change.append(config_line.text)
        return configs_to_change

    def build_config_cmnds(self,
                           template_file,
                           configs_to_change,
                           current_child_cfg,
                           desired_child_cfg):
        env = Environment(
            loader=FileSystemLoader('.'),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
            )
        config = env.get_template(template_file)
        config_commands = config.render(config_lines=configs_to_change,
                                        current_child_config=current_child_cfg,
                                        desired_child_config=desired_child_cfg)
        return config_commands

    def push_config_change(self, mgmt_ip, hostname, config_commands):
        print(f'Connecting to {hostname}...')
        try:
            with get_network_driver('ios')(
                mgmt_ip,
                self.username,
                self.password,
                optional_args={
                    'secret': self.enable_pwd,
                    'inline_transfer': True,
                    'global_delay_factor': 1,
                    }
                ) as device:
                print('The following commands will be sent to device:')
                print(config_commands)
                print('Loading net changes (this may take a few minutes)...')
                device.load_merge_candidate(config=config_commands)
                print(device.compare_config())

                # Ask for confirmation to commit changes.
                response = ''
                while response not in ('y', 'n'):
                    response = input("Commit the above changes? (y/n): ")
                    if response == 'n':
                        device.discard_config()
                        print("Changes discarded.")
                    if response == 'y':
                        device.commit_config()
                        print("Changes committed.")
        except Exception as err:
            print(f'Issue connecting to {hostname}: {err}')

    def get_lldp_neighbors_detail(self, mgmt_ip, hostname):
        self.print_connecting(hostname)
        try:
            with get_network_driver('ios')(
                    mgmt_ip,
                    self.username,
                    self.password,
                    optional_args={
                        'secret': self.enable_pwd,
                        'inline_transfer': True,
                        'global_delay_factor': 1,
                        }
                    ) as device:
                return device.get_lldp_neighbors_detail()
        except Exception as err:
            self.print_connection_err(err, hostname)

    def get_cdp_neighbors(self, mgmt_ip, hostname):
        self.print_connecting(hostname)
        try:
            cmd = "show cdp neighbors detail"
            with ConnectHandler(device_type='cisco_ios',
                                host=mgmt_ip,
                                username=self.username,
                                password=self.password,
                                secret=self.enabled_pwd,
                                global_delay_factor=3
                                ) as device:
                device.enable()
                output = device.send_command(cmd)
                cdp_neighbors = parse_output("cisco_ios", cmd, output)
                return cdp_neighbors
        except Exception as err:
            self.print_connection_err(err, hostname)
