import re
import pandas as pd
import json
import os
import random
import string
from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client['openstack']

# Specify the path to your CSV file
file_path = 'C:/Users/ozeabala/OneDrive - NANDPS/Desktop/chewy20-8TB-SPI-2024-07-22.csv'
file_name = os.path.basename(file_path)
# Split the filename by '-' and extract the date part
parts = file_name.split('-')
date = f"{parts[-3]}-{parts[-2]}-{parts[-1][:2]}"  # Extract date parts and format
prefix = '-'.join(file_name.split('-')[:2])
print(file_name)

data = pd.read_excel(file_path)


d1 = {}
count =0
count1= 2
for i in range(33):
    print (data.iat[count,0])
    l1=[]
    for j in range(1,6):
        print (data.iat[count1,j])
        l1.append((data.iat[count1,j]))
    d1[data.iat[count,0]] = l1
    count += 4
    count1 += 4

print (d1)

def time_string_to_microseconds(time_str):
    """Convert time string 'ss.ms.us' to microseconds."""
    match = re.match(r"time elapsed in ss.ms.us : (\d{2})\.(\d{3})\.(\d{3})", time_str.strip())
    if match:
        seconds = int(match.group(1))
        milliseconds = int(match.group(2))
        microseconds = int(match.group(3))
        total_microseconds = (seconds * 1_000_000) + (milliseconds * 1_000) + microseconds
        return total_microseconds
    return None

def microseconds_to_time_string(microseconds):
    """Convert microseconds to time string 'ss.ms.us'."""
    seconds = microseconds // 1_000_000
    milliseconds = (microseconds % 1_000_000) // 1_000
    microseconds = microseconds % 1_000
    return f"{seconds:02}.{milliseconds:03}.{microseconds:03}"

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

# Get min and max times for each key
min_max_times = find_min_max_times(d1)

json_data = json.dumps(min_max_times, indent=4)

# Print the JSON data
print(json_data)

def generate_random_suffix(length=3):
    return ''.join(random.choices(string.digits, k=length))

dashboard_id = 'REC' + '-' + generate_random_suffix()

res = db.dashboard.insert_one({
    "_id": dashboard_id,
    "data": json_data,
})
print(res)
