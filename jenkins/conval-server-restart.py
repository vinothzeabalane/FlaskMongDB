import configparser
import paramiko
import argparse
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

def read_config(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    
    commands = {}
    for section in config.sections():
        if section == 'RESTART':
            commands[section] = [config.get(section, 'command{}'.format(i)) for i in range(1, len(config.options(section)) + 1)]
    
    return commands

def execute_commands_on_all_hosts(hosts, commands):
    for host in hosts:
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

        except Exception as e:
            print("An error occurred: {}. Skipping this item.".format(e))

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
            print("Connected to {}".format(self.hostname))

        except Exception as e:
            print("Failed to connect to {}: {}".format(self.hostname, e))

            raise
    
    def execute_command(self, command):
        try:
            print("Command executed: '{}'".format(command))
            stdin, stdout, stderr = self.client.exec_command(command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            if output:
                print("Output from '{}' on {}:\n{}".format(command, self.hostname, output))
            if error:
                print("Error from '{}' on {}:\n{}".format(command, self.hostname, error))
            return output
        except Exception as e:
            print("Error executing command '{}' on {}: {}".format(command, self.hostname, e))
            return None
    

if __name__ == "__main__":
    ini_file = '/home/remlab/ps-bpt/FlaskMongDB/conval_host.ini'
    
    hosts = read_hosts_config(ini_file)
    commands = read_config(ini_file)

    execute_commands_on_all_hosts(hosts, commands)

