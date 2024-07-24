import os
import re

from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId
from datetime import date
from pathlib import Path


# Specify the directory where CSV files are located
directory = '/mnt/udrive/ozeabalx/ps-bootprofile'
#directory = 'C:/Users/ozeabala/OneDrive - NANDPS/Desktop/ps-bootprofile'
csv_files = []
commid_id = None
last_updated = []
pattern = r'\b\d{4}-\d{2}-\d{2}\b'
spiflow = False
eb0flow = True

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['openstack']  # Replace with your database name

# Access GridFS
fs = GridFS(db)

try:

    def read_file(file):
        with open(file,'r') as f1:
            return  f1.read()


    # Iterate through all files in the directory
    for file in os.listdir(directory):
        # Check if the file is a CSV file
        if file.startswith("commit_id"):
            commid_id = read_file(os.path.join(directory, file))

        elif file.startswith("last_updated"):
            last_updated = re.findall(pattern, read_file(os.path.join(directory, file)))

        elif file.endswith(".csv"):
            # If yes, add it to the list of CSV files
            csv_files.append(os.path.join(directory, file))


    for file in csv_files:
        filename = str(os.path.basename(file)).replace('.csv','')
        is_file_exit = db.fs.files.find_one({"filename": filename})
        if is_file_exit:
            print('File name already exists')
            continue
        with open(file, 'rb') as f:
            # Store data in GridFS, which handles chunking automatically
            file_id = fs.put(f, filename=filename)

        print('Uploaded file with _id: {file_id}')

        if 'SPI' in str(filename):
            spiflow = True
            eb0flow = False

        # Find the uploaded file by filename
        file_info = db.fs.files.find_one({"filename": filename})
        today = date.today()
        date_string = today.strftime("%Y-%m-%d")

        new_metadata = {"date": last_updated[0], "commit_id": commid_id, "is_spiflow": spiflow,
            "is_eb0flow": eb0flow, 'file_uploaded_date': date_string }

        # Update metadata
        if file_info:
            file_id = file_info["_id"]

            db.fs.files.update_one({"_id": ObjectId(file_id)}, {"$set": {"metadata": new_metadata}})
            
            print("Metadata updated successfully.")
            # Path(os.path.join(directory, filename)).unlink()
            # print("File deleted the shared location")
        else:
            print("File not found.")


except Exception as e:
    print ("Exception : {}".format(e))



