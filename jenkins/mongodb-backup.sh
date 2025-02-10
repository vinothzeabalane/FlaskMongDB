#!/bin/bash

# Define backup directory and date format
backup_dir="/mnt/udrive/ozeabalx/ps-mongodb-backup"
cd $backup_dir; ls -lrt;  
date_format=$(date +\%Y\%m\%d)
backup_file="$backup_dir/$date_format.zip"

# Perform MongoDB dump (backup) and pipe to zip compression
mongodump --host 10.74.135.88 --port 27017 --db openstack --archive | zip "$backup_file" -

# Find and delete files older than 5 days
find "$backup_dir" -type f -name "*.zip" -mtime +5 -exec rm -f {} +

echo "Backup and cleanup completed successfully."

#restore
#mongorestore --host 10.74.135.88 --port 27017 --db mydatabase /backups/mongo_dump/mydatabase
#mongorestore --host 10.74.135.88 --port 27017 --username <your_username> --password <your_password> --authenticationDatabase admin /path/to/backup/folder

