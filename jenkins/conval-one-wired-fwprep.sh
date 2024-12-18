#!/bin/bash

echo "Process Started..."

# Prompt the user for input
read -p "Enter the firmware binary (e.g., HDC_M22_WW51.1_C0_B.22.28): " fw_binary

# Display the entered value
echo "You entered: $fw_binary"

# Proceed with the rest of your script
cd /mnt/udrive/ozeabalx/HDC_drops/$fw_binary/trenton-kv7/fw_release_package/platform_services_fw/sbbph28x019tgf_mc0b271 || exit
sudo rm -rf /mnt/udrive/ozeabalx/one-wired/*

sudo cp eeprom-SBBPH28X019TGF_MC0B271.bin /mnt/udrive/ozeabalx/one-wired/eeprom-SBBPH28X019TGF_MC0B271.bin

cd /mnt/udrive/ozeabalx/one-wired/
# Function to corrupt EEPROM at a specific slot and verify it
corrupt_eeprom() {
    local slot_offset=$1
    local search_pattern=$2
    local eeprom_file=$3

    echo "Corrupting the EEPROM at $search_pattern"
    
    # Show the original hexdump at the specified offset
    hexdump -C "$eeprom_file" | grep "$search_pattern"
    
    # Perform the corruption by writing the given pattern at the specified offset
    sudo printf '\xfb\xfb\xfb\xfb\xfb\xfb\xfb\xfb' | sudo dd of=eeprom-SBBPH28X019TGF_MC0B271.bin bs=1 seek=$slot_offset count=8 conv=notrunc
    
    # Show the hexdump again after corruption
    hexdump -C "$eeprom_file" | grep "$search_pattern"
}

# Corrupt slot-0 and slot-1 of the EEPROM

corrupt_eeprom 917520 "000e0010" eeprom-SBBPH28X019TGF_MC0B271.bin
corrupt_eeprom 3276816 "00320010" eeprom-SBBPH28X019TGF_MC0B271.bin

echo "You can find the corrputed EERPOM binary at /mnt/udrive/ozeabalx/one-wired/"

echo "Process Completed"
