#!/bin/bash

# Export Python path if necessary
export PYTHONPATH=$PYTHONPATH:/home/remlab/bhb_tools/lib
echo "PYTHONPATH: $PYTHONPATH"

# Prepare filename with current date
today=$(date +"%Y-%m-%d")
filename="lm-302-05-s2-raw-8TB-EB0-$today.csv"

# Print filename for verification
echo "Filename: $filename"

# List NVMe devices
sudo nvme list

# Change directory to /home/remlab
cd /home/remlab || exit

# Remove files with 'sudo rm -r' and ignore errors if files do not exist
sudo rm -r /home/remlab/cmdline.cfg /home/remlab/"$filename" 2>/dev/null || true

# Create the file
touch /home/remlab/$filename

# Create cmdline.cfg file with commands
echo -e "selectdev 1\ntc-unlock\nfwdownload -f /mnt/udrive/ozeabalx/ps-bootprofile/unified_image.bin\nfwcommit -s 1 -c 1 -b 0\nexit" > /home/remlab/cmdline.cfg

# Setup environment
cd /home/jenkins/repos/ent_ssd_test/lib/spdk/scripts/ || exit
sudo ./setup.sh

# Execute spdktest and append output to $filename
cd /home/jenkins/repos/ent_ssd_test/spdktest/ || exit
sudo ./spdktest -t -l /home/remlab/cmdline.cfg >> "/home/remlab/output.log"


# Wait for 5 seconds
sleep 5

# Run pita_cycle
cd /home/remlab/bhb_tools/ || exit
sudo ./pita_cycle -a

# Wait for 5 seconds
sleep 10

# Reset environment
cd /home/jenkins/repos/ent_ssd_test/lib/spdk/scripts/ || exit
sudo ./setup.sh reset

# List NVMe devices
sudo nvme list

# Change directory to /home/remlab
cd /home/remlab || exit

# Remove files with 'sudo rm -r' and ignore errors if files do not exist
sudo rm -r /home/remlab/cmdline.cfg /home/remlab/"$filename" 2>/dev/null || true

# Create cmdline.cfg file with commands
echo -e "selectdev 1\ntc-unlock\ntc-boot-profile\nexit" > /home/remlab/cmdline.cfg

echo "create a file"
touch "/home/remlab/$filename"

# Loop to execute commands 5 times
for (( i = 1; i <= 5; i++ ))
do
    cd /home/jenkins/repos/ent_ssd_test/lib/spdk/scripts/ || exit
    sudo ./setup.sh

    if sudo ./setup.sh status | grep -qi 'uio_pci_generic'; then
        echo "uio_pci_generic found"
        # Perform any additional actions here
    else
        echo "uio_pci_generic not found"
        cd /home/jenkins/repos/ent_ssd_test/lib/spdk/scripts/ || exit
        sudo ./setup.sh reset
        continue
    fi

    # Execute spdktest and check if the result contains "ConnectToSpdk() call failed"
    cd /home/jenkins/repos/ent_ssd_test/spdktest/ || exit
    result=$(sudo ./spdktest -t -l /home/remlab/cmdline.cfg)
    echo "***********************************************************"
    echo "spdk result -  $result"
    echo "***********************************************************"
    echo "$result" | grep -q "ConnectToSpdk() call failed"
    if [ $? -eq 0 ]; then
        echo "ConnectToSpdk() call failed. Skipping iteration."
        continue
    fi

    echo "Iteration:  $i " >> "/home/remlab/$filename"
    # Setup environment
    # cd /home/jenkins/repos/ent_ssd_test/lib/spdk/scripts/ || exit
    # sudo ./setup.sh

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
filename="lm-302-05-s2-8TB-EB0-$today.csv"
cd; cd /home/remlab;
sudo cp -r lm-302-05-s2-8TB-EB0-$today.csv /mnt/udrive/ozeabalx/ps-bootprofile


cd; cd /home/remlab;
sudo rm -r lm-302-05-s2-*.csv