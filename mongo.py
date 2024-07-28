from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timedelta
import gridfs
import random
import string
import logging

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

    def check_user_by_group(self, group_id):
        try:
            return self.db.users.find_one({"group_id": group_id})
        except Exception as e:
            self._log_error(e)
            
    def check_access_right(self, user):
        try:
            return self.db.users.find_one({"username": str(user), "is_admin": "True"})
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
            
    def users_list(self):
        try:
            return list(self.db.users.find({}, {"_id": 0}))
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
            today = datetime.now().date()
            two_months_ago = today - timedelta(days=60)

            query = {
                "metadata.date": {
                    "$gte": filter['StartDate'] if filter and 'StartDate' in filter else two_months_ago.strftime("%Y-%m-%d"),
                    "$lte": filter['EndDate'] if filter and 'EndDate' in filter else today.strftime("%Y-%m-%d")
                }
            }
            col = self.db.fs.files.find(query)
            return [{'name': i['filename'], 'data': i.get('metadata')} for i in col if 'filename' in i]
        except Exception as e:
            self._log_error(e)
            
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

    def update_user_details(self, filter, update):
        try:
            return self.db.users.update_one(filter, update)
        except Exception as e:
            self._log_error(e)
