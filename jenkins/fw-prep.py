import select
import threading
import subprocess
import time
import platform
import paramiko
import requests

from requests.auth import HTTPBasicAuth
from datetime import datetime
from queue import Queue


UARTKILL = True
HOST_REBOOT = False
headers = {'Accept': 'application/json'}
USER = 'remlab'
PASSWORD = '1001SMT!'
HOST_BUFFER = 20

def host_status(host):
    res = True
    timeout_start = time.time()
    while time.time() < timeout_start + HOST_BUFFER:
        response = requests.get('https://tidbits.elements.local/tidbits/tb_hostinfo.php?id={}'.format(host),
            auth = HTTPBasicAuth('ozeabalx', 'SeyonSiva@2022'), verify = False, headers=headers)
        time.sleep(5)
        print ("res-before condition check: {}".format(res))
        #print ("response: {}").format(response.text)
        if  ('ozeabalx' in response.text):
            res = False
            print ("res-Starting: {}".format(res))
            return res
    return res

def do_tail(lock):
    lock.release()
    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('10.74.134.70', port=22, username=USER, password=PASSWORD)
    
        remote_command = 'picocom -b 115200 /dev/ttyACM0 > out.txt | tail -f out.txt'
        print (remote_command)
    
        transport = client.get_transport()
        channel = transport.open_session()
        channel.exec_command(remote_command)

        while UARTKILL:
            time.sleep(5)
            try:
                rl, _, _ = select.select([channel], [], [], 0.0)
                if len(rl) > 0:
                    print ("ready to read ...")
                    for line in linesplit(channel):
                        print (line)
            except (KeyboardInterrupt, SystemExit):
                print ('got ctrl+c')
                break
    except Exception as e:
        print(e)
    finally:
        client.close()
        lock.release()
        print ('client closed')

def paramiko_GKG(command, timeout = None):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.load_system_host_keys()
    client.connect('10.74.134.70', port=22, username=USER, password=PASSWORD)
    print('running...')
    time.sleep(10)
    try:
        (stdin, stdout, stderr) = client.exec_command(command, timeout=timeout)
        cmd_output = stdout.read()
        print('log : ', command, cmd_output)
        while True:
            print (stdout.channel.recv_exit_status() )
            time.sleep(5)
            if stdout.channel.recv_exit_status() in [0,1,-1]:
                break
    except Exception as e:
        print(e)
    finally:
        client.close()  

def linesplit(socket):
    buffer_string = socket.recv(4048)
    done = False
    while not done:
        if "\n" in buffer_string:
            (line, buffer_string) = buffer_string.split("\n", 1)
            yield line + "\n"
        else:
            more = socket.recv(4048)
            if not more:
                done = True
            else:
                buffer_string = buffer_string + more
    if buffer_string:
        yield buffer_string

def load_check():
    print("Recovery: STARTED")
    hal_lock = threading.Lock()
    hal_lock.acquire()
    que = Queue()
    job1 = threading.Thread(target=lambda q, arg1: q.put(do_tail(arg1)), args=(que, hal_lock))
    job2 = threading.Thread(target=recovery, args=[])
    job1.start()
    hal_lock.acquire()
    job2.start()
    job1.join()
    job2.join()
    ret = False
    while not que.empty():
        ret = que.get()
        if ret is False:
            break
    return ret

def ping(ip=None):
    param = '-n' if platform.system().lower()=='windows' else '-c'
    command = ['ping', param, '1', ip]
    return subprocess.call(command) == 0

def recovery():
    global UARTKILL
    global HOST_REBOOT
    count = 0
    try:
        print('************** Recovery process started **********************************************')
        paramiko_GKG('cd /home/remlab/Desktop/Dediprog-latest/SF100Linux; sudo ./dpcmd -z /mnt/udrive/ozeabalx/ps-bootprofile/eeprom/eeprom-SBBPH28X076TGF_MC0B271.bin')
        paramiko_GKG('cd; cd bhb_tools/; sudo ./pita_cycle -a')
        paramiko_GKG(command="lspci | grep -i Non-Volatile")
        paramiko_GKG("sleep 5")
        paramiko_GKG('cd /home/jenkins/repos/ent_ssd_test; sudo ["driver-override=uio_pci_generic"] lib/spdk/scripts/setup.sh')
        paramiko_GKG('echo -e "selectdev 1\ntc-unlock\ntc-cdm\ntc-llf\nexit" > /home/remlab/cmdline.cfg')
        paramiko_GKG('cd /home/jenkins/repos/ent_ssd_test/spdktest; sudo ./spdktest -t -l /home/remlab/cmdline.cfg ')
        paramiko_GKG(r""" export PYTHONPATH='/home/remlab/bhb_tools/lib'; python -c "from pylib.drive_power import pita; pita.PITA('/dev/ttyACM1').powerCycle()" """)
        time.sleep(90)
        paramiko_GKG('rm -r /home/remlab/cmdline.cfg ')
        paramiko_GKG(command="lspci | grep -i Non-Volatile")
        print('************** Recovery process ended **********************************************')

        UARTKILL = False
        HOST_REBOOT = True
    except Exception as e:
        print(e)
    finally:
        if HOST_REBOOT:
            paramiko_GKG('sudo reboot')
    
try:
    start_time = datetime.now()
    print('************** Recovery process start time:  {} **********************************************'.format(start_time))
    assert True == ping('10.74.134.70'), "-E- host is down"
    if not host_status('23170'):
        load_check()
    else:
        print("The host is healhty")
except Exception as e:
    print("Error: %s", str(e))
finally:
    print('recovery script duration: {}'.format(datetime.now() - start_time))