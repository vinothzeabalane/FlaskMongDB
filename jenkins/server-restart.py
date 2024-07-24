import paramiko

_HOST = [{'ip': '10.74.134.101', 'hostname': 'vc-ps-chewyfit-15', 'login': 'remlab', 'password': '1001SMT!'}, 
         {'ip': '10.74.134.70', 'hostname': 'vc-ps-chewy-20', 'login': 'remlab', 'password': '1001SMT!'}]

def execute_ssh_command(hostname, port, username, password, command):
    try:
        # Create an SSH client instance
        client = paramiko.SSHClient()
        # Automatically add host keys from the default file
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Connect to the server
        client.connect(hostname, port=port, username=username, password=password)
        # Execute the command
        stdin, stdout, stderr = client.exec_command(command)
        # Read the output from the command
        output = stdout.read().decode('utf-8')
        # Print the output
        print("Command executed successfully on {}:\n{}".format(hostname, output))

    except Exception as e:
        print("Error executing the command on {}: {}".format(hostname, e))

    finally:
        # Disconnect from the server
        client.close()

# Example usage:
if __name__ == "__main__":
    port = 22  # Default SSH port
    command = 'hostname; sudo reboot'  # Example command to execute

    for host in _HOST:
        execute_ssh_command(hostname=host['ip'], port=port, username=host['login'], password=host['password'], command=command)
