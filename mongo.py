from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timedelta
import gridfs
import random
import string

class MongoDB:
    
    def __init__(self,host,port,db):
        self.client = MongoClient(host,port)
        self.db = self.client[db]
        
    
    def check_user(self,user,password):
        try:
            res = self.db.users.find_one({"username":str(user),"password":str(password)})
            return res
        except Exception as e:
            print(e)

    def check_user_name(self,user):
        try:
            if self.db.users.find_one({"username": { '$regex': user, '$options': 'i' }}):
                return True
            return False
        except Exception as e:
            print(e)

    def check_user_by_group(self,group_id):
        try:
            res = self.db.users.find_one({"group_id": group_id})
            return res
        except Exception as e:
            print(e)
            
    def check_access_right(self,user):
        try:
            res = self.db.users.find_one({"username":str(user),"is_admin":"True"})
            return res
        except Exception as e:
            print(e)
    
    def set_user(self,val):
        try:
            res = self.check_user_name(val.get("username"))
            if not res:
                res = self.db.users.insert_one(val)
            else:
                return "user already exits"
        except Exception as e:
            print(e)
        return True
    
    def groups_list(self):
        l1 = []
        try:
            res = self.db.groups.find()
            for i in res:
                l1.append(i)
            return l1
        except Exception as e:
            print(e)
            
    def users_list(self):
        l1 = []
        try:
            res = self.db.users.find({}, {"_id":0})
            for i in res:
                l1.append(i)
            return l1
                
        except Exception as e:
            print(e)

    def users_aggregate(self):
        l1=[]
        try:
            
            pipeline = [{"$lookup": {"from": "groups","localField": "group_id","foreignField": "_id","as": "group"}}]
            res = self.db.users.aggregate(pipeline)
            for i in res:
                l1.append(i)
            return l1
                
        except Exception as e:
            print(e)


    def users_aggregate_access(self, username):
        access_list = []
        try:
            # Define the aggregation pipeline
            pipeline = [
                {"$match": {"username": username}},  # Filter by username
                {"$lookup": {
                    "from": "groups",
                    "localField": "group_id",
                    "foreignField": "_id",
                    "as": "group"
                }},
                {"$project": {"_id": 0, "group": 1}}  # Include only the 'group' field
            ]
            
            # Execute the aggregation pipeline
            result = self.db.users.aggregate(pipeline)
            
            # Collect results
            for item in result:
                if 'group' in item:
                    for group in item['group']:
                        if 'access' in group:
                            access_list.append(group['access'])
            return access_list
                
        except Exception as e:
            print(e)
            return []


    def bpt_list(self, filter=None):
        l1 = []
        try:
            client = MongoClient("127.0.0.1", 27017)
            db = client.openstack 
            today = datetime.now().date()
            two_months_ago = today - timedelta(days=60)  # Approximate 2 months as 60 days

            query = {
                "metadata.date": {
                    "$gte": filter['StartDate'] if filter and 'StartDate' in filter else two_months_ago.strftime("%Y-%m-%d"),
                    "$lte": filter['EndDate'] if filter and 'EndDate' in filter else today.strftime("%Y-%m-%d")
                }
            }
            col = db.fs.files.find(query)
            for i in col:
                if 'filename' not in i:
                    continue
                l1.append({'name': i['filename'], 'data': i['metadata'] or None})
            return l1
                
        except Exception as e:
            print(e)
            
    def check_group(self,group):
        try:
            res = self.db.groups.find_one({"name":str(group)})
            return res
        except Exception as e:
            print(e)

    def check_group_in_users(self,group):
        try:
            res = self.db.users.find_one({"group_id":group})
            return res
        except Exception as e:
            print(e)
            
    def delete_groups(self,val):
        try:
            for i in val:
                res = self.db.groups.delete_one({"name":str(i)})
            return True
        except Exception as e:
            print(e)
            
    def delete_users(self,val):
        try:
            for i in val:
                res = self.db.users.delete_one({"username":str(i)})
            return True
        except Exception as e:
            print(e)

    def generate_random_suffix(self,length=3):
        return ''.join(random.choices(string.digits, k=length))
            
    def set_group(self,request=None):
        while True:
            data = request.form
            try:
                val = {'user':[False,False,False], 'group': [False,False,False]}

                if data['hdnGroupID'] == '':
                    group_id = 'GRP' + '-' + self.generate_random_suffix()
                    if self.db.groups.find_one({'name': { '$regex': data['name'], '$options': 'i' }}):
                        return False
                else:
                    group_id = data['hdnGroupID']

                if 'chkUserView' in data:
                    val['user'][0] = True if data['chkUserView'] == 'on' else False
                if 'chkUserEdit' in data:
                    val['user'][1] = True if data['chkUserEdit'] == 'on' else False
                if 'chkUserDelete' in data:
                    val['user'][2] = True if data['chkUserDelete'] == 'on' else False


                if 'chkGroupView' in data:
                    val['group'][0] = True if data['chkGroupView'] == 'on' else False
                if 'chkGroupEdit' in data:
                    val['group'][1] = True if data['chkGroupEdit'] == 'on' else False
                if 'chkGroupDelete' in data:
                    val['group'][2] = True if data['chkGroupDelete'] == 'on' else False

                if data['hdnGroupID'] == '':
                    self.db.groups.insert_one(
                            {
                            "_id":group_id,
                            "name": data['name'],
                            "access": val
                            })
                    print(f"Inserted document with group _id: {group_id}")
                    break
                else:
                    filter = {'_id': group_id}
                    update = {'$set': {"name": data['name'],"access": val}}

                    self.db.groups.update_one(filter, update) 
                    break        
            except DuplicateKeyError:
                # If DuplicateKeyError occurs, generate a new random suffix and retry
                print(f"Duplicate _id found, retrying...")
                continue
            except Exception as e:
                # Handle the exception
                print(f"An error occurred: {e}")

        return True
    
    def update_password(self,user,oldpass,newpass):
        try:
            res = self.db.users.find_one({"password":str(oldpass)})
            if res:
                result = self.db.users.update_one({ "username": user },{"$set":{"password": newpass}})
                return True
            else:
                return False
        except Exception as e:
            print(e)


    def update_user_details(self,filter,update):
        try:
            return  self.db.users.update_one(filter, update)
        except Exception as e:
            print(e)