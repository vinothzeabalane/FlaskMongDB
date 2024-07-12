#!/usr/bin/bash 
echo "---------------------------------------"
echo "HOST NAME"
hostname
echo "---------------------------------------"
sudo rm -r /tmp/jenkins.txt || true
cd /home/remlab/Desktop/Dediprog-latest/SF100Linux;
sudo ./dpcmd -d  > /tmp/jenkins.txt
echo "Parse Output"
cat /tmp/jenkins.txt 

if cat /tmp/jenkins.txt | grep -i "Error"
then
    echo "Dediprog is not identified, rebooting the host"
	exit 1
else
    echo "Dediprog identified"
    
fi