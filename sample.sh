#!/bin/bash
 
# Set the recovery directory
echo -e "selectdev 1\ntc-unlock\ntc-drive-info\nexit" > /tmp/cmdline.cfg
 
repo_recovery="/home/remlab/HDC_drops/HDC_M23_WW09.5_C0_B.23.35/HDC_M23_WW09.5_C0_B.23.35/trenton-kv7/fw_release_package/recovery"
 
# Source the environment script
cd $repo_recovery
source /home/jenkins/repos/trenton/env.sh
 
# Run the script 2 times
for i in {1..2}
do
    echo "Running iteration $i..."
 
    # Run the jtag recovery script
    # ./jtag-recovery-kv7-SBBPH28X153TGF_MC0B271.sh
    # Wait for 2 minutes
    sleep 120
    # Switch to NVMe to UIO_interface
    cd /home/jenkins/repos/ent_ssd_test
    sudo driver-override=uio_pci_generic lib/spdk/scripts/setup.sh
    cd /home/jenkins/repos/ent_ssd_test/spdktest
    # Run spdktest and check for match
    if ! sudo ./spdktest -t -l /tmp/cmdline.cfg | tee /tmp/out.txt | grep -iq "FORCED_DL"; then
    echo "No match found for FORCED_DL in iteration $i, stopping iteration."
    break  # Stop the iteration if no match is found
    fi
    echo "Iteration $i complete."
done