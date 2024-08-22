from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timedelta
from pymongo import DESCENDING
from collections import defaultdict
import gridfs
import random
import string
import logging
import pytz

class MongoDB:
    
    def __init__(self, host, port, db):
        self.client = MongoClient(host, port)
        self.db = self.client[db]
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.ERROR)
        
    def _log_error(self, e):
        self.logger.error(e)

    def check_user(self, user, password):
        try:
            return self.db.users.find_one({"username": str(user), "password": str(password)})
        except Exception as e:
            self._log_error(e)

    def check_user_name(self, user):
        try:
            return self.db.users.find_one({"username": {'$regex': user, '$options': 'i'}}) is not None
        except Exception as e:
            self._log_error(e)

    def set_user(self, val):
        try:
            if not self.check_user_name(val.get("username")):
                self.db.users.insert_one(val)
            else:
                return "user already exists"
        except Exception as e:
            self._log_error(e)
        return True
    
    def groups_list(self):
        try:
            return list(self.db.groups.find())
        except Exception as e:
            self._log_error(e)
            
    def users_aggregate(self):
        try:
            pipeline = [
                {"$lookup": {
                    "from": "groups",
                    "localField": "group_id",
                    "foreignField": "_id",
                    "as": "group"
                }}
            ]
            return list(self.db.users.aggregate(pipeline))
        except Exception as e:
            self._log_error(e)

    def users_aggregate_access(self, username):
        try:
            pipeline = [
                {"$match": {"username": username}},
                {"$lookup": {
                    "from": "groups",
                    "localField": "group_id",
                    "foreignField": "_id",
                    "as": "group"
                }},
                {"$project": {"_id": 0, "group": 1}}
            ]
            result = self.db.users.aggregate(pipeline)
            return [group['access'] for item in result if 'group' in item for group in item['group'] if 'access' in group]
        except Exception as e:
            self._log_error(e)
            return []

    def bpt_list(self, filter=None):
        try:
            # Get today's date and calculate the date two months ago
            today = datetime.now().date()
            two_months_ago = today - timedelta(days=60)

            # Determine the date range for the query
            from_date = filter['StartDate'] if filter and 'StartDate' in filter else two_months_ago.strftime("%Y-%m-%d")
            to_date = filter['EndDate'] if filter and 'EndDate' in filter else today.strftime("%Y-%m-%d")

            # Construct the query with date filters
            query = {
                "metadata.date": {
                    "$gte": from_date,
                    "$lte": to_date
                }
            }

            # Query the collection and sort by date in descending order
            col = self.db.fs.files.find(query).sort("metadata.date", DESCENDING)

            # Extract filenames and metadata
            result = [
                {
                    'name': i['filename'],
                    'data': i.get('metadata')
                }
                for i in col if 'filename' in i
            ]

            # Prepare the date range dictionary
            date_range = {
                'from_date': from_date,
                'to_date': to_date
            }

            # Insert the date range at the beginning of the result list
            result.insert(0, date_range)

            return result
        except Exception as e:
            self._log_error(e)
            return []  # Return an empty list if there's an error
            
    def check_group(self, group):
        try:
            return self.db.groups.find_one({"name": str(group)})
        except Exception as e:
            self._log_error(e)

    def check_group_in_users(self, group):
        try:
            return self.db.users.find_one({"group_id": group})
        except Exception as e:
            self._log_error(e)
            
    def delete_groups(self, values):
        try:
            for group in values:
                self.db.groups.delete_one({"name": str(group)})
            return True
        except Exception as e:
            self._log_error(e)
            
    def delete_users(self, values):
        try:
            for user in values:
                self.db.users.delete_one({"username": str(user)})
            return True
        except Exception as e:
            self._log_error(e)

    def generate_random_suffix(self, length=3):
        return ''.join(random.choices(string.digits, k=length))
            
    def set_group(self, request=None):
        while True:
            try:
                data = request.form if request else {}
                if data.get('hdnGroupID') == '':
                    group_id = 'GRP' + '-' + self.generate_random_suffix()
                    if self.db.groups.find_one({'name': {'$regex': data['name'], '$options': 'i'}}):
                        return False
                else:
                    group_id = data['hdnGroupID']

                access = {
                    'user': [data.get(f'chkUser{perm}', 'off') == 'on' for perm in ['View', 'Edit', 'Delete']],
                    'group': [data.get(f'chkGroup{perm}', 'off') == 'on' for perm in ['View', 'Edit', 'Delete']]
                }

                if data.get('hdnGroupID') == '':
                    self.db.groups.insert_one({
                        "_id": group_id,
                        "name": data['name'],
                        "access": access
                    })
                    break
                else:
                    self.db.groups.update_one(
                        {'_id': group_id},
                        {'$set': {"name": data['name'], "access": access}}
                    )
                    break
            except DuplicateKeyError:
                self.logger.warning(f"Duplicate _id found, retrying...")
                continue
            except Exception as e:
                self._log_error(e)
        return True
    
    def update_password(self, user, oldpass, newpass):
        try:
            if self.db.users.find_one({"password": str(oldpass)}):
                self.db.users.update_one({"username": user}, {"$set": {"password": newpass}})
                return True
            return False
        except Exception as e:
            self._log_error(e)

    def update_last_login(self, username):
        try:
            self.db.users.update_one({"username": username},
            {"$set": {"last_login": datetime.now(pytz.utc)}}
            )
            return True
        except Exception as e:
            self._log_error(e)

    def update_user_details(self, filter, update):
        try:
            return self.db.users.update_one(filter, update)
        except Exception as e:
            self._log_error(e)

    def get_dashboard_details(self):
        try:
            # Step 1: Find the latest date in the collection
            latest_date_doc = self.db.dashboard.find().sort('date', -1).limit(1)
            latest_date_doc_list = list(latest_date_doc)  # Convert cursor to list
            latest_date = latest_date_doc_list[0]['date'] if latest_date_doc_list else None

            if not latest_date:
                raise ValueError("No documents found in the collection.")

            # Step 2: Fetch documents for the latest date
            documents = self.db.dashboard.find({
                'date': latest_date
            }).sort('hostname', 1)
            
            grouped_docs = defaultdict(list)

            for doc in documents:
                hostname = doc.get('hostname', 'Unknown')
                grouped_docs[hostname].append(doc)

            # Convert grouped results to a list of lists
            result_list = list(grouped_docs.values())

            # Print the results
            for group in result_list:
                print(f"Group for hostname: {group[0]['hostname']}")
                for doc in group:
                    print(doc)
            
            return result_list
        except Exception as e:
            self._log_error(e)

    def get_dashboard_details_filter(self, date= None, hostname=None):
        try:
            fields_to_exclude = ['BootType', 'Date', 'HOST']
            documents = self.db.dashboard.find({
                'date': date,
                'hostname': hostname
            })
            
            grouped_docs = defaultdict(list)

            for doc in documents:
                filtered_doc = {key: value for key, value in doc.items()}

                # Check if the key 'data' exists in the dictionary 'filtered_doc'
                if 'data' in filtered_doc:
                    # Use dictionary comprehension to filter out keys in 'fields_to_exclude'
                    filtered_doc['data'] = {
                        key: value for key, value in filtered_doc['data'].items() if key not in fields_to_exclude
                    }

                # Get hostname, default to 'Unknown' if not present
                host = filtered_doc.get('hostname', 'Unknown')
                grouped_docs[host].append(filtered_doc)

            # Convert grouped results to a list of lists
            result_list = list(grouped_docs.values())

            # Print the results
            for group in result_list:
                print(f"Group for hostname: {group[0]['hostname']}")
                for doc in group:
                    print(doc)
            
            return result_list
        except Exception as e:
            self._log_error(e)