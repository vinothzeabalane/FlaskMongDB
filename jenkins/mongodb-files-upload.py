import os
import re
import pandas as pd
import json
import random
import string
import math
import argparse

from pymongo import MongoClient, errors
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

# Setup argument parser
parser = argparse.ArgumentParser(description="Upload files to MongoDB GridFS")
parser.add_argument('--server', type=str, required=True, help="MongoDB server address")
args = parser.parse_args()

# Use the server address provided by the user as a command-line argument
server = args.server

# Connect to MongoDB using the provided server address
client = MongoClient(f'mongodb://{server}:27017/')
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

def is_nan(value):
    return isinstance(value, (int, float)) and math.isnan(value)

def find_min_max_times(d):
    """Find min and max times for each key in the dictionary."""
    result = {}
    for key, time_strings in d.items():
        if isinstance(key, float) and math.isnan(key):
            key = 'NONE'
        # Convert time strings to microseconds
        filtered_time_strings = [s for s in time_strings if isinstance(s, str) and not (isinstance(s, float))]
        time_values = [time_string_to_microseconds(ts) for ts in filtered_time_strings]
        # time_values = [time_string_to_microseconds(ts) for ts in time_strings]
        
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
            print('File name {} already exists in the files'.format(filename))
            continue
        with open(file, 'rb') as f:
            # Store data in GridFS, which handles chunking automatically
            file_id = fs.put(f, filename=filename)

        print('Uploaded file with _id: {file_id}')

        fparts = filename.split('-')
        spiflow = 'SPI' in fparts
        eb0flow = not spiflow

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
        skip_parent = False
        do_data_format = True
        file_name = os.path.basename(filepath).replace(".csv", "")
        # Split the file name by dashes
        parts = file_name.split('-')

        # Extract the parts based on the given rules
        date = '-'.join(parts[-3:])  # The last three parts form the date
        bootTpye = parts[-4]        # The fourth from the last part is the boot type
        skuSize = parts[-5]              # The fifth from the last part is the SKU
        hostname = '-'.join(parts[:-5])  # The remaining parts form the hostname

        is_filename_exit = db.dashboard.find_one({"filename": file_name})
        if is_filename_exit:
            print('File name: {} already exists in the dashboard collection'.format(file_name))
            continue
        df = pd.read_excel(filepath)
        
        # # Extract date part and prefix from filename
        parts = file_name.split('-')
        # date = "{}-{}-{}".format(parts[-3], parts[-2], parts[-1][:2]) 
        prefix = '-'.join(parts[:2])
        
        data = {}
        count = 0
        icount = 2
        
        if len(df) == 0:
            print('File name: {} is emptpy, and has no data'.format(file_name))
            do_data_format = False
            data = {}

        iter_count = df.shape[1]
        if do_data_format:
            # Collect data from DataFrame
            for _ in range(32):
                l1 = [df.iat[icount, j] for j in range(1, iter_count)]
                data[df.iat[count, 0]] = l1
                count += 4
                icount += 4
            
            for values in data.values():
                for value in values:
                    if is_nan(value):
                        skip_parent = True
                        print("Item is NaN")

        # if skip_parent:
        #     continue  # Continue to the next iteration of the parent loop

        min_max_times = find_min_max_times(data)


        res = db.dashboard.insert_one({
            "data": globals().get('min_max_times', {}),
            "filename": file_name,
            "hostname": hostname,
            "sku": skuSize,
            "bootType": bootTpye,
            "date": date
        })
        print ("Output: {}".format(res))


    
except Exception as e:
    print ("Exception : {}".format(e))

