import select
import threading
import subprocess
import time
import platform
import paramiko
import requests

from requests.auth import HTTPBasicAuth
from datetime import datetime
# from queue import Queue
import Queue

headers = {'Accept': 'application/json'}
USER = 'remlab'
PASSWORD = '1001SMT!'
HOST_BUFFER = 20

class FirmwarePrep(object):

    def __init__(self):
        self.ulog = True
        self.host_reboot = True

    def host_status(self, host):
        res = True
        timeout_start = time.time()
        while time.time() < timeout_start + HOST_BUFFER:
            self.response = requests.get('https://tidbits.elements.local/tidbits/tb_hostinfo.php?id={}'.format(host),
                auth = HTTPBasicAuth('ozeabalx', 'SeyonSiva@2022'), verify = False, headers=headers)
            time.sleep(5)
            print ("res-before condition check: {}".format(res))
            #print ("response: {}").format(response.text)
            if  ('ozeabalx' in self.response.text):
                res = False
                print ("res-Starting: {}".format(res))
                return res
        return res

    def do_tail(self, lock):
        
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

            while self.ulog:
                time.sleep(5)
                try:
                    rl, _, _ = select.select([channel], [], [], 0.0)
                    if len(rl) > 0:
                        print ("ready to read ...")
                        for line in self.linesplit(channel):
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

    def paramiko_GKG(self, command, timeout = None):
        self.cmd_output = None
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.load_system_host_keys()
        self.client.connect('10.74.134.70', port=22, username=USER, password=PASSWORD)
        print('running...')
        time.sleep(10)
        try:
            (self.stdin, self.stdout, self.stderr) = self.client.exec_command(command, timeout=timeout)
            self.cmd_output = self.stdout.read()
            print('log : ', command, self.cmd_output)
            while True:
                print (self.stdout.channel.recv_exit_status() )
                time.sleep(5)
                if self.stdout.channel.recv_exit_status() in [0,1,-1]:
                    break
        except Exception as e:
            print(e)
        finally:
            self.client.close()

        return self.cmd_output  

    def linesplit(self, socket):
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

    def load_check(self):
        print("Recovery: STARTED")
        self.hal_lock = threading.Lock()
        self.hal_lock.acquire()
        que = Queue.Queue()
        self.job1 = threading.Thread(target=lambda q, arg1: q.put(self.do_tail(arg1)), args=(que, self.hal_lock))
        self.job2 = threading.Thread(target=self.recovery, args=[])
        self.job1.start()
        self.hal_lock.acquire()
        self.job2.start()
        self.job1.join()
        self.job2.join()
        self.ret = False
        while not que.empty():
            self.ret = que.get()
            if self.ret is False:
                break
        return self.ret

    def ping(self, ip=None):
        param = '-n' if platform.system().lower()=='windows' else '-c'
        command = ['ping', param, '1', ip]
        return subprocess.call(command) == 0

    def recovery(self):
        count = 0
        try:
            print('************** Recovery process started **********************************************')
            self.paramiko_GKG('cd /home/remlab/Desktop/Dediprog-latest/SF100Linux; sudo ./dpcmd -z /mnt/udrive/ozeabalx/ps-bootprofile/eeprom/eeprom-SBBPH28X076TGF_MC0B271.bin')
            self.paramiko_GKG('cd; cd bhb_tools/; sudo ./pita_cycle -a')
            self.paramiko_GKG(command="lspci | grep -i Non-Volatile")
            self.paramiko_GKG("sleep 5")
            self.paramiko_GKG('cd /home/jenkins/repos/ent_ssd_test; sudo ["driver-override=uio_pci_generic"] lib/spdk/scripts/setup.sh')
            self.paramiko_GKG('echo -e "selectdev 1\ntc-unlock\ntc-cdm\ntc-llf\nexit" > /home/remlab/cmdline.cfg')
            self.paramiko_GKG('cd /home/jenkins/repos/ent_ssd_test/spdktest; sudo ./spdktest -t -l /home/remlab/cmdline.cfg ')
            self.paramiko_GKG(r""" export PYTHONPATH='/home/remlab/bhb_tools/lib'; python -c "from pylib.drive_power import pita; pita.PITA('/dev/ttyACM1').powerCycle()" """)
            time.sleep(20)
            self.paramiko_GKG('rm -r /home/remlab/cmdline.cfg ')
            self.paramiko_GKG(command="lspci | grep -i Non-Volatile")
            res = self.paramiko_GKG(command="sudo nvme list")
            print (" kill the thread ")
            self.paramiko_GKG(command="kill $(ps aux | grep '[d]ev/ttyACM0' | awk '{print $2}')")
            if "/dev/nvme0n1" in str([res]):
                self.host_reboot = False
                self.ulog = False

            print('************** Recovery process ended **********************************************')

        except Exception as e:
            print(e)
        finally:
            if self.host_reboot:
                self.paramiko_GKG('sudo reboot')


if __name__ == "__main__":
    fp = FirmwarePrep()
    try:
        start_time = datetime.now()
        print('************** Recovery process start time:  {} **********************************************'.format(start_time))
        assert True == fp.ping('10.74.134.70'), "-E- host is down"
        if not fp.host_status('23170'):
            fp.load_check()
        else:
            print("The host is healhty")
    except Exception as e:
        print("Error: %s", str(e))
    finally:
        print('recovery script duration: {}'.format(datetime.now() - start_time))