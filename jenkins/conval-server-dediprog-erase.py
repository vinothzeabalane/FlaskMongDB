import configparser
import paramiko
import os
import time
import threading

def read_config(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    
    # Read hosts from the configuration file
    hosts = eval(config.get('Settings', 'HOST'))  # Use eval safely for list of dictionaries
    
    # Read commands for DEDIPROG and PICOCOM
    commands = {section: [config.get(section, f'command{i}') for i in range(1, len(config.options(section)) + 1)]
                for section in config.sections() if section == 'DEDIPROG'}
    
    picocom_commands = {}
    if 'PICOCOM' in config.sections():
        picocom_commands['start'] = config.get('PICOCOM', 'start')
        picocom_commands['stop'] = config.get('PICOCOM', 'stop')
    
    return hosts, commands, picocom_commands

def execute_commands(ssh_connection, commands, picocom_commands, host, log_dir):
    try:
        # Execute DEDIPROG commands
        if 'DEDIPROG' in commands:
            for cmd in commands['DEDIPROG']:
                if '/dev/ttyACM' in cmd:
                    cmd = cmd.replace('X', host['pita'])
                ssh_connection.execute_command(cmd)
        
        # Download logs
        remote_log_path = '/tmp/picocom.log'
        local_log_path = os.path.join(log_dir, f'{host["ip"]}_picocom.log')
        ssh_connection.download_file(remote_log_path, local_log_path)
        
        # Execute Picocom stop command
        if 'stop' in picocom_commands:
            kill_command = picocom_commands['stop'].replace('X', host['picocom'])
            ssh_connection.execute_command(kill_command)

    except Exception as e:
        print(f"Error with host {host['ip']}: {e}")
    finally:
        ssh_connection.close()

def run_picocom(hosts, picocom_commands):
    for host in hosts:
        ssh_connection = SSHConnection(host['ip'], 22, host['login'], host['password'])
        try:
            ssh_connection.connect()
            if 'start' in picocom_commands:
                picocom_command = picocom_commands['start'].replace('X', host['picocom'])
                ssh_connection.execute_command(picocom_command)
            time.sleep(2)
        except Exception as e:
            print(f"Error starting picocom on {host['ip']}: {e}")
        finally:
            ssh_connection.close()

def execute_commands_on_all_hosts(hosts, commands, picocom_commands, log_dir):
    for host in hosts:
        ssh_connection = SSHConnection(host['ip'], 22, host['login'], host['password'])
        try:
            ssh_connection.connect()
            execute_commands(ssh_connection, commands, picocom_commands, host, log_dir)
        except Exception as e:
            print(f"Error executing commands on {host['ip']}: {e}")

class SSHConnection:
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
            print(f"Executing command: '{command}'")
            stdin, stdout, stderr = self.client.exec_command(command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            if output:
                print(f"Output from {self.hostname}: {output}")
            if error:
                print(f"Error from {self.hostname}: {error}")
            return output
        except Exception as e:
            print(f"Error executing command '{command}' on {self.hostname}: {e}")
            return None
    
    def close(self):
        self.client.close()
        print(f"Connection to {self.hostname} closed")
    
    def download_file(self, remote_path, local_path):
        try:
            sftp = self.client.open_sftp()
            sftp.get(remote_path, local_path)
            print(f"Downloaded {remote_path} to {local_path}")
        except Exception as e:
            print(f"Error downloading file {remote_path}: {e}")
        finally:
            sftp.close()

if __name__ == "__main__":
    ini_file = '/home/remlab/ps-bpt/FlaskMongDB/conval_host.ini'
    log_dir = 'logs'
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    hosts, commands, picocom_commands = read_config(ini_file)
    
    # Start threads for picocom and command execution
    picocom_thread = threading.Thread(target=run_picocom, args=(hosts, picocom_commands))
    command_thread = threading.Thread(target=execute_commands_on_all_hosts, args=(hosts, commands, picocom_commands, log_dir))

    picocom_thread.start()
    command_thread.start()

    picocom_thread.join()
    command_thread.join()
