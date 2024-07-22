#!/bin/bash

# Export Python path if necessary
export PYTHONPATH=$PYTHONPATH:/home/remlab/bhb_tools/lib
echo "PYTHONPATH: $PYTHONPATH"

# Prepare filename with current date
today=$(date +"%Y-%m-%d")
filename="chewy20-raw-8TB-SPI-$today.csv"

# Print filename for verification
echo "Filename: $filename"

# List NVMe devices
sudo nvme list

# Change directory to /home/remlab
cd /home/remlab || exit

# Remove files with 'sudo rm -r' and ignore errors if files do not exist
sudo rm -r /home/remlab/cmdline.cfg /home/remlab/"$filename" 2>/dev/null || true

# Create cmdline.cfg file with commands
echo -e "selectdev 1\ntc-unlock\ntc-boot-profile\nexit" > /home/remlab/cmdline.cfg

# Loop to execute commands 5 times
for (( i = 1; i <= 5; i++ ))
do
    echo "Iteration:  $i " >> "/home/remlab/$filename"

    # Setup environment
    cd /home/jenkins/repos/ent_ssd_test/lib/spdk/scripts/ || exit
    sudo ./setup.sh

    # Execute spdktest and append output to $filename
    cd /home/jenkins/repos/ent_ssd_test/spdktest/ || exit
    sudo ./spdktest -t -l /home/remlab/cmdline.cfg >> "/home/remlab/$filename"

    # Wait for 5 seconds
    sleep 5

    # Run pita_cycle
    cd /home/remlab/bhb_tools/ || exit
    sudo ./pita_cycle -a

    # Wait for 5 seconds
    sleep 5

    # Reset environment
    cd /home/jenkins/repos/ent_ssd_test/lib/spdk/scripts/ || exit
    sudo ./setup.sh reset

    # Wait for 10 seconds before next iteration
    sleep 10
done



today=$(date +"%Y-%m-%d")
filename="chewy20-8TB-SPI-$today.csv"
cd; cd /home/remlab;
sudo cp -r chewy20-8TB-SPI-$today.csv /mnt/udrive/ozeabalx/ps-bootprofile


cd; cd /home/remlab;
sudo rm -r chewy20-*.csv