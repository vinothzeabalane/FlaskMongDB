import os
import re
import pandas as pd
import json
import random
import string

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


def generate_random_suffix(length=3):
    return ''.join(random.choices(string.digits, k=length))

def time_string_to_microseconds(time_str):
    """Convert time string 'ss.ms.us' to microseconds."""
    match = re.match(r"time elapsed in ss.ms.us : (\d{2})\.(\d{3})\.(\d{3})", time_str.strip())
    if match:
        seconds = int(match.group(1))
        milliseconds = int(match.group(2))
        microseconds = int(match.group(3))
        total_microseconds = (seconds * 1000000) + (milliseconds * 1000) + microseconds
        return total_microseconds
    return None

def microseconds_to_time_string(microseconds):
    """Convert microseconds to time string 'ss.ms.us'."""
    seconds = microseconds // 1000000
    milliseconds = (microseconds % 1000000) // 1000
    microseconds = microseconds % 1000
    return "{:02}.{:03}.{:03}".format(seconds, milliseconds, microseconds)

def find_min_max_times(d):
    """Find min and max times for each key in the dictionary."""
    result = {}
    for key, time_strings in d.items():
        # Convert time strings to microseconds
        time_values = [time_string_to_microseconds(ts) for ts in time_strings]
        
        # Find min and max values
        min_time = min(time_values)
        max_time = max(time_values)
        
        # Convert back to readable format
        min_time_str = microseconds_to_time_string(min_time)
        max_time_str = microseconds_to_time_string(max_time)
        
        result[key] = {
            'min': min_time_str,
            'max': max_time_str
        }
    
    if result:
        result['Date'] = date
        if 'SPI' in file_name:
            result['BootType'] = 'SPI'
        else:
            result['BootType'] = "EB0"
        result['HOST'] =  prefix  
    return result

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
            #Path(os.path.join(directory, filename)).unlink()
            #print("File deleted the shared location")
        else:
            print("File not found.")


    for filepath in csv_files:
        file_name = os.path.basename(filepath).replace(".csv", "")
        parts = file_name.split('-')
        hostname = parts[0]
        skuSize = parts[1]
        bootTpye = parts[2]
        is_filename_exit = db.dashboard.find_one({"filename": file_name})
        if is_filename_exit:
            print('File name already exists')
            continue
        df = pd.read_excel(filepath)
        
        # Extract date part and prefix from filename
        parts = file_name.split('-')
        date = "{}-{}-{}".format(parts[-3], parts[-2], parts[-1][:2]) 
        prefix = '-'.join(parts[:2])
        
        data = {}
        count = 0
        icount = 2
        
        # Collect data from DataFrame
        for _ in range(33):
            l1 = [df.iat[icount, j] for j in range(1, 6)]
            data[df.iat[count, 0]] = l1
            count += 4
            icount += 4
        
        min_max_times = find_min_max_times(data)
        dashboard_id = 'REC-{}'.format(generate_random_suffix())
        
        # Insert into database
        res = db.dashboard.insert_one({
            "_id": dashboard_id,
            "data": min_max_times,
            "filename": file_name,
            "hostname": hostname,
            "sku": skuSize,
            "bootType": bootTpye,
            "date": date
        })

except Exception as e:
    print ("Exception : {}".format(e))



