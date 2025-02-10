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

#Start the MongoDB - Terminal1 ( Container)
sudo mongod --bind_ip_all

#restore
mongorestore --host localhost --port 27017 --archive=/mnt/ps-share/20250210/openstack/archive_file.archive

#Verify
mongosh --host localhost --port 27017
use openstack
show collections

# MongoDB Starts on Container Restart
docker run -d --name ps-mongod -p 27017:27017 --restart always mongo --bind_ip_all

sudo docker run -d -it --name ps-mongod -p 27017:27017 --network=bridge --restart always \
  --mount type=bind,source=/mnt/ps-share,target=/mnt/ps-share \
  --mount type=volume,source=ps_val,target=/mnt/ps_vol \
  vinothzeabalane/ps-mongod:v1 mongod --bind_ip_all


