echo "********************** PULL the lastest trenton repository code ******************"
cd; cd /home/jenkins/repos/trenton;
sudo git reset --hard; git pull
git log -1


echo "********* COMPILE THE BINARY *******"
cd; cd /home/jenkins/repos/trenton;
sudo echo -e '\n source /home/jenkins/repos/trenton/hud/build-hudhwfwprep.sh -v kv7 -r c0' > /home/jenkins/repos/ps_bash.sh
sudo cat /home/ozeabalx/env.sh /home/jenkins/repos/ps_bash.sh > /home/jenkins/repos/final_bash.sh
sudo chmod u+x /home/jenkins/repos/final_bash.sh
sudo cp -r /home/jenkins/repos/final_bash.sh /home/jenkins/repos/trenton/
cd /home/jenkins/repos/trenton;
sudo ./final_bash.sh
cd /home/jenkins/repos/trenton/prod/hud/debug/hwfwprep-kv7/build/eeprom; ls;
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