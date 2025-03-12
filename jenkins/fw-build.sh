#!/bin/bash

# Define paths for easy reference
REPO_PATH="/home/jenkins/repos/trenton"
PS_BOOT_COMPILE_PATH="/home/remlab/ps-boot-compile"
FINAL_BASH_PATH="/home/jenkins/repos/final_bash.sh"

echo "********************** PULL the latest Trenton repository code ******************"

# Remove the existing repository and clone the latest version
cd /home/jenkins/repos || exit 1
sudo rm -rf trenton
git clone ssh://git@npsg-bit.elements.local:7999/fsedev/trenton.git
echo "********* COMPILE THE BINARY *******"

# Copy required files to Trenton repo
sudo cp -r $PS_BOOT_COMPILE_PATH/run_time/ $REPO_PATH/configurator/
sudo cp -r $PS_BOOT_COMPILE_PATH/dependency_metadata.json $REPO_PATH/pfw/shared/fw_update_mic/
sudo cp -r $PS_BOOT_COMPILE_PATH/env.sh $REPO_PATH
sudo cp -r $PS_BOOT_COMPILE_PATH/MIC_FW.hex $REPO_PATH/pfw/shared/fw_update_mic/

# Pull the latest changes from the Trenton repo
cd $REPO_PATH || exit 1
sudo git pull
git log -1

# Create and update the final bash script
echo -e '\n source /home/jenkins/repos/trenton/hud/build-hudhwfwprep.sh -v kv7 -r c0' > $REPO_PATH/ps_bash.sh
echo -e '\n source ./clean-cmakebuild.sh && /home/jenkins/repos/trenton/hud/build-hudhwfwprep.sh -v kv7 -r c0' | sudo tee -a $REPO_PATH/ps_bash.sh > /dev/null
sudo cat /home/ozeabalx/env.sh $REPO_PATH/ps_bash.sh > $FINAL_BASH_PATH

# Make the final bash script executable and copy it to Trenton repo
sudo chmod u+x $FINAL_BASH_PATH
sudo cp -r $FINAL_BASH_PATH $REPO_PATH

# Run the final bash script
cd $REPO_PATH || exit 1
sudo ./final_bash.sh

# List the contents of the final build directory
cd $REPO_PATH/prod/hud/debug/hwfwprep-kv7/build/eeprom || exit 1
ls

echo "********************** FW Build binary Ended ******************"


cd; cd /home/remlab;
cd; cd /mnt/udrive/ozeabalx/ps-bootprofile; 
pwd; ls;
rm -r * || true


cp -r /home/jenkins/repos/trenton/prod/hud/debug/hwfwprep-kv7/build/eeprom /mnt/udrive/ozeabalx/ps-bootprofile
cp -r /home/jenkins/repos/trenton/prod/hud/debug/hwfwprep-kv7/build/unified_image/unified_image.bin /mnt/udrive/ozeabalx/ps-bootprofile
cd; cd /mnt/udrive/ozeabalx/ps-bootprofile; 
touch -f last_updated.txt
date '+Current Date: %F' > last_updated.txt

cd; cd /home/jenkins/repos/trenton
git config --global --add safe.directory /home/jenkins/repos/trenton
git show HEAD~1 --pretty=format:"%h" --no-patch > /home/remlab/commit_id.txt
cp -r /home/remlab/commit_id.txt /mnt/udrive/ozeabalx/ps-bootprofile/