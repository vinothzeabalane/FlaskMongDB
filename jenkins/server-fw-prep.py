import configparser
import paramiko
import threading
import ast
import os
import time

def read_hosts_config(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    
    # Parse the JSON-like list from the `HOST` section
    hosts_str = config.get('Settings', 'HOST')
    hosts = ast.literal_eval(hosts_str)  # Safely evaluate the string as a list of dictionaries
    
    return hosts

def read_fwcommands_config(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    
    commands = {}
    for section in config.sections():
        if section == 'FW-PREP':
            commands[section] = [config.get(section, f'command{i}') for i in range(1, len(config.options(section)) + 1)]
    
    return commands

def read_picocom_config(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    
    picocom_commands = {}
    for section in config.sections():
        if section == 'PICOCOM':
            picocom_commands['stop'] = config.get(section, 'stop')
            picocom_commands['start'] = config.get(section, 'start')
    
    return picocom_commands


def run_picocom(hosts, picocom_commands):
    for host in hosts:
        ssh_connection = SSHConnection(
            hostname=host['ip'],
            port=22,  # Adjust port if necessary
            username=host['login'],
            password=host['password']
        )
        
        try:
            ssh_connection.connect()

            if 'start' in picocom_commands:
                # Execute picocom and save its output to a log file
                picocom_command = picocom_commands['start'].replace('X', host['picocom'])
                ssh_connection.execute_command(picocom_command)
            time.sleep(2)
        except Exception as e:
            print(f"An error occurred: {e}. Skipping this item.")
        

def execute_commands_on_all_hosts(hosts, commands, picocom_commands, log_dir):
    for host in hosts:
        count = 0
        required_reboot = True
        max_attempts = 5
        ssh_connection = SSHConnection(
            hostname=host['ip'],
            port=22,  # Adjust port if necessary
            username=host['login'],
            password=host['password']
        )
        
        try:
            ssh_connection.connect()

            # Execute commands from `RESTART` section
            if 'RESTART' in commands:
                for cmd in commands['RESTART']:
                    ssh_connection.execute_command(cmd)
            
            # Execute commands from `FW-PREP` section
            if 'FW-PREP' in commands:
                for cmd in commands['FW-PREP']:
                    if 'eeprom-XXXXXXXXX.bin' in cmd:
                        cmd = cmd.replace('eeprom-XXXXXXXXX.bin', host['eeprom'])

                    if '/dev/ttyACM' in cmd:
                        cmd = cmd.replace('X', host['pita'])
                    
                    ssh_connection.execute_command(cmd)

            # Download the log file from the remote host
            remote_log_path = '/tmp/picocom.log'
            local_log_path = os.path.join(log_dir, f'{host["ip"]}_picocom.log')
            ssh_connection.download_file(remote_log_path, local_log_path)

        except Exception as e:
            print(f"An error occurred: {e}. Skipping this item.")
        
        finally:
            # Execute picocom commands
            if 'stop' in picocom_commands:
                kill_command = picocom_commands['stop'].replace('X', host['picocom'])
                ssh_connection.execute_command(kill_command)
            res = ssh_connection.execute_command("sudo nvme list")
            while count < max_attempts and res:
                time.sleep(2)
                if "/dev/nvme" in res:
                    required_reboot = False
                    break
                count += 1
            if required_reboot:
                print("System reboot")
                ssh_connection.execute_command("sudo reboot")
            ssh_connection.close()

class SSHConnection(object):
    def __init__(self, hostname, port, username, password):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    def connect(self):
        try:
            self.client.connect(self.hostname, port=self.port, username=self.username, password=self.password)
            print(f"Connected to {self.hostname}")
        except Exception as e:
            print(f"Failed to connect to {self.hostname}: {e}")
            raise
    
    def execute_command(self, command):
        try:
            print(f"Command executed: '{command}' ")
            stdin, stdout, stderr = self.client.exec_command(command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            if output:
                print(f"Output from '{command}' on {self.hostname}:\n{output}")
            if error:
                print(f"Error from '{command}' on {self.hostname}:\n{error}")
            return output
        except Exception as e:
            print(f"Error executing command '{command}' on {self.hostname}: {e}")
            return None
    
    def close(self):
        self.client.close()
        print(f"Connection to {self.hostname} closed.")

    def download_file(self, remote_path, local_path):
        sftp = self.client.open_sftp()
        try:
            sftp.get(remote_path, local_path)
            print(f"Downloaded {remote_path} to {local_path}")
        except Exception as e:
            print(f"Error downloading file {remote_path}: {e}")
        finally:
            sftp.close()

if __name__ == "__main__":
    ini_file = 'C:/eclipse-workspace/FlaskMongDB/host.ini'
    log_dir = 'logs'  # Directory to store downloaded log files
    
    # Ensure the log directory exists
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    hosts = read_hosts_config(ini_file)
    commands = read_fwcommands_config(ini_file)
    picocom_commands = read_picocom_config(ini_file)
    
    # execute_commands_on_all_hosts(hosts, commands, picocom_commands, log_dir)
    picocom_thread = threading.Thread(target=run_picocom, args=(hosts, picocom_commands))
    other_command_thread = threading.Thread(target=execute_commands_on_all_hosts, args=(hosts, commands, picocom_commands, log_dir))

    # Start threads
    picocom_thread.start()
    other_command_thread.start()

    # Wait for threads to finish
    picocom_thread.join()
    other_command_thread.join()
