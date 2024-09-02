from pymongo import MongoClient
from datetime import datetime, timedelta
import argparse

# Function to connect to MongoDB and retrieve data
def fetch_and_compare_data(hostname):
    # MongoDB connection
    client = MongoClient('mongodb://localhost:27017/')
    db = client['openstack']
    collection = db['dashboard']

    # Define the date ranges
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    # Convert to ISODate format for querying
    today_str = str(today)
    yesterday_str = str(yesterday)

    # Fetch documents for the recent date
    recent_docs = collection.find({
        'hostname': hostname,
        'date': today_str
    })

    # Fetch documents for the previous date
    previous_docs = collection.find({
        'hostname': hostname,
        'date': yesterday_str
    })

    # Convert documents to dictionaries for easy access
    def extract_data(docs):
        data_dict = {}
        for doc in docs:
            data = doc['data']
            for key, value in data.items():
                if key not in data_dict:
                    data_dict[key] = {'min': value['min'], 'max': value['max']}
                else:
                    # Merge min and max if multiple documents exist
                    data_dict[key]['min'] = min(data_dict[key]['min'], value['min'])
                    data_dict[key]['max'] = max(data_dict[key]['max'], value['max'])
        return data_dict

    recent_data = extract_data(recent_docs)
    previous_data = extract_data(previous_docs)

    # Compare values
    def compare_values(recent_data, previous_data):
        for key in recent_data:
            if key in previous_data:
                recent_min = recent_data[key]['min']
                previous_min = previous_data[key]['min']
                if compare_versions(recent_min, previous_min) < 0:
                    print(f"Alert: Value for '{key}' got reduced. Previous: {previous_min}, Recent: {recent_min}")

    # Function to compare version strings
    def compare_versions(version1, version2):
        v1_parts = list(map(int, version1.split('.')))
        v2_parts = list(map(int, version2.split('.')))
        return (v1_parts > v2_parts) - (v1_parts < v2_parts)

    compare_values(recent_data, previous_data)

# Main function to parse arguments and execute the script
if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description="Compare values in MongoDB for a specific hostname.")
    # parser.add_argument('hostname', type=str, help="The hostname to filter the data by.")
    # args = parser.parse_args()

    fetch_and_compare_data("chewy20")
