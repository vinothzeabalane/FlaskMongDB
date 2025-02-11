#!/bin/bash

# Define directories and filename
intermediate_dir="/home/remlab/HDC_buddyDrops/"
source_dir="/mnt/ydrive/fast-data/Releases/CV/HuntsdaleC/Internal/"
final_dest_dir="/mnt/udrive/mpanginx/buddy_image/"

# Prompt the user for the filename
read -p "Enter the filename (e.g., HDC_M21_WW35.4_C0_B.21.20.tgz): " filename

# Confirm the operation
read -p "This will delete all contents in $intermediate_dir and $final_dest_dir, and perform file operations. Continue? (y/n): " confirm
if [[ $confirm != "y" ]]; then
    echo "Operation canceled."
    exit 0
fi

# Clean the intermediate directory
echo "Cleaning the intermediate directory: $intermediate_dir"
sudo rm -rf "$intermediate_dir"/* || { echo "Failed to delete contents in $intermediate_dir"; exit 1; }

# Clean the final destination directory
echo "Removing old directory: $final_dest_dir"
sudo rm -rf "$final_dest_dir"/* || { echo "Failed to delete $final_dest_dir"; exit 1; }

# Ensure the intermediate directory exists
echo "Ensuring the intermediate directory exists."
sudo mkdir -p "$intermediate_dir" || { echo "Failed to create $intermediate_dir"; exit 1; }

# Copy the file from source to intermediate directory
echo "Copying file $filename from $source_dir to $intermediate_dir"
sudo cp -r "$source_dir$filename" "$intermediate_dir" || { echo "Failed to copy $filename to $intermediate_dir"; exit 1; }

# Navigate to the intermediate directory and extract the tarball
echo "Changing directory to $intermediate_dir and extracting $filename"
cd "$intermediate_dir" || { echo "Failed to change directory to $intermediate_dir"; exit 1; }
sudo tar -xvzf "$filename" || { echo "Failed to extract $filename"; exit 1; }

# Remove .tgz extension from the filename
filename_no_extension="${filename%.tgz}"

# Now use the modified filename in the path
echo "Copying contents of $intermediate_dir/$filename_no_extension/trenton-kv7/fw_release_package/benchsigned/release/unified_image.bin to $final_dest_dir"
sudo cp -r "$intermediate_dir/$filename_no_extension/trenton-kv7/fw_release_package/benchsigned/release/unified_image.bin" "$final_dest_dir" || { echo "Failed to copy contents to $final_dest_dir"; exit 1; }

echo "Operation completed successfully."
