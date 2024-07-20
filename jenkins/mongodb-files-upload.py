from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId
from datetime import date

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['openstack']  # Replace with your database name

# Access GridFS
fs = GridFS(db)

# Example: Reading data from a file
with open('C:/Users/ozeabala/OneDrive - NANDPS/Desktop/chewy20-8TB-SPI-2024-07-20.csv', 'rb') as f:
    # Store data in GridFS, which handles chunking automatically
    file_id = fs.put(f, filename='chewy20-8TB-SPI-2024-07-20.csv')

print(f'Uploaded file with _id: {file_id}')



# Find the uploaded file by filename
file_info = db.fs.files.find_one({"filename": "chewy20-8TB-SPI-2024-07-20.csv"})
today = date.today()
date_string = today.strftime("%Y-%m-%d")


# Update metadata
if file_info:
    file_id = file_info["_id"]
    new_metadata = {"date": date_string, "commit_id": "XXXXFFFFFFFFF"}
    db.fs.files.update_one({"_id": ObjectId(file_id)}, {"$set": {"metadata": new_metadata}})
    
    print("Metadata updated successfully.")
else:
    print("File not found.")
