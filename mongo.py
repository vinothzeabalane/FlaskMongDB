from pymongo import MongoClient
import gridfs


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
            res = self.db.users.find_one({"username":str(user)})
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
            res = self.check_user(val.get("username"),val.get("password"))
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
            res = self.db.groups.find({}, {"_id":0})
            for i in res:
                l1.append(i['name'])
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

    def bpt_list(self):
        l1 = []
        try:
            client = MongoClient("127.0.0.1", 27017)
            db = client.openstack 
            fs = gridfs.GridFS(db)

            col = db.fs.files.find()
            for i in col:
                print(i)
                if 'filename' not in i:
                    continue
                l1.append({'name': i['filename'], 'data': i['metadata'] or None})
            print ("BootProfileTime list:  {}".format(l1))
            return l1
                
        except Exception as e:
            print(e)
            
    def check_group(self,group):
        try:
            res = self.db.groups.find_one({"name":str(group)})
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
            
    def set_group(self,group):
        try:
            res = self.check_group(group)
            if not res:
                res = self.db.groups.insert_one(
                    {
                    "name": group
                    })
            else:
                return False
        except Exception as e:
            print(e)
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