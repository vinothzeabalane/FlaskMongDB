import os
from flask import Flask, flash, redirect, render_template, request, session, url_for, send_file, jsonify, Response
import gridfs
import pandas as pd
import mongo
from gridfs import GridFSBucket
from pathlib import Path
from gevent.pywsgi import WSGIServer
from datetime import timedelta, datetime, timezone
from bson.objectid import ObjectId

class MyApp:
    def __init__(self):
        try:
            self.app = Flask(__name__, static_url_path='/static')
            self.configure_app()  # Configure app settings
            self.add_routes()     # Add route handlers

            # Establish MongoDB connection
            self.conn = self.get_mongo_connection()
            self.gridfsbucket = GridFSBucket(self.conn.db)
            self.gridfs = gridfs.GridFS(self.conn.db)
        
        except Exception as e:
            # Log the error or handle it as needed
            print(f"Error during initialization: {e}")

    def configure_app(self):
        self.app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)  # Session timeout set to 10 minutes
        self.app.config.from_pyfile('config.cfg')
        self.app.secret_key = os.urandom(12)
        self.app.before_request(self.before_request)

    def add_routes(self):
        self.app.add_url_rule('/account', 'account', self.account)
        self.app.add_url_rule('/account_update', 'account_update', self.account_update, methods=['GET', 'POST'])
        self.app.add_url_rule('/create_group', 'create_group', self.create_group, methods=['GET', 'POST'])
        self.app.add_url_rule('/groups', 'groups', self.groups)
        self.app.add_url_rule('/update_group', 'update_group', self.update_group, methods=['GET', 'POST'])
        self.app.add_url_rule('/update_user', 'update_user', self.update_user, methods=['GET', 'POST'])
        self.app.add_url_rule('/create_user', 'create_user', self.create_user, methods=['GET', 'POST'])
        self.app.add_url_rule('/users', 'users', self.users)
        self.app.add_url_rule('/view_bpt', 'view_bpt', self.view_bpt, methods=['GET', 'POST'])
        self.app.add_url_rule('/download_bpt', 'download_bpt', self.download_bpt, methods=['GET', 'POST'])
        self.app.add_url_rule('/bpt', 'bpt', self.bpt, methods=['GET', 'POST'])
        self.app.add_url_rule('/home', 'home', self.home, methods=['GET', 'POST'])
        self.app.add_url_rule('/dashboard', 'dashboard', self.dashboard)
        self.app.add_url_rule('/logout', 'logout', self.logout)
        self.app.errorhandler(404)(self.page_not_found)
        self.app.add_url_rule('/login', 'login', self.login)
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/', 'data', self.data)

    def before_request(self):
        session.permanent = True
        self.app.permanent_session_lifetime = self.app.config['PERMANENT_SESSION_LIFETIME']
        if 'last_activity' in session:
            naive_now = datetime.utcnow()
            aware_now = naive_now.replace(tzinfo=timezone.utc)
            last_activity = session.get('last_activity')
            if last_activity and (aware_now - last_activity).total_seconds() > self.app.permanent_session_lifetime.total_seconds():
                session.clear()
                return render_template('login.html', error="Your Session Expired")
        session['last_activity'] = datetime.utcnow()

    def get_mongo_connection(self):
        try:
            res = mongo.MongoDB(
                host=self.app.config['MYSQL_HOST'],
                port=self.app.config['MYSQL_PORT'],
                db=self.app.config['MONGO_DB']
            )
            return res
        except Exception as e:
            self.app.logger.error(f"MongoDB connection error: {e}")

    def account(self):
        group_access = self.conn.users_aggregate_access(username=session['user'])
        return render_template('account.html', user_access=group_access[0], user=session['user'], password=session['password'])

    def account_update(self):
        try:
            if session.get("user"):
                oldpass = request.form["oldpass"]
                newpass = request.form["newpass"]
                res = self.conn.update_password(session['user'], oldpass, newpass)
                if res:
                    flash('Your password has been updated successfully. <br/><br/> Re-login with new password!', 'success')
                    return redirect(url_for('account'))
                else:
                    return render_template('account.html', user=session['user'], error="Please enter correct old password")
            else:
                return render_template('login.html', error="Your Session Expired")
        except Exception as e:
            self.app.logger.error(f"Error updating account: {e}")

    def create_group(self):
        try:
            name = request.form['name']
            res = self.conn.set_group(request)
            groups_list = self.conn.groups_list()
            group_access = self.conn.users_aggregate_access(username=session['user'])
            if res:
                return redirect(url_for('groups'))
            else:
                return render_template("group.html", warning=True, error=f"Group Name: {name} already exists", user_access=group_access[0], groups=groups_list, user=session['user'])
        except Exception as e:
            self.app.logger.error(f"Error creating group: {e}")

    def groups(self):
        try:
            if session.get("user"):
                res = self.conn.groups_list()
                group_access = self.conn.users_aggregate_access(username=session['user'])
                return render_template('group.html', groups=res, user_access=group_access[0], user=session['user'])
            else:
                return render_template('login.html', error="Your Session Expired")
        except Exception as e:
            self.app.logger.error(f"Error retrieving groups: {e}")

    def update_group(self):
        try:
            del_groups = []
            warning_groups = []
            if request.form:
                groups = request.form.getlist('chk')
                for i in groups:
                    group_id = self.conn.check_group(i)
                    if self.conn.check_group_in_users(group_id['_id']):
                        warning_groups.append(i)
                    else:
                        del_groups.append(i)
                self.conn.delete_groups(del_groups)
                grouplist = self.conn.groups_list()
                group_access = self.conn.users_aggregate_access(username=session['user'])
                if len(warning_groups) > 0:
                    warning_message = f"Warning: {warning_groups} group(s) are linked with one or more users. Please unlink before deleting!"
                    self.app.logger.warning(warning_message)
                    return render_template("group.html", warning=True, error=warning_message, user_access=group_access[0], groups=grouplist, user=session['user'])
            return redirect(url_for('groups'))
        except Exception as e:
            self.app.logger.error(f"Error updating groups: {e}")

    def update_user(self):
        try:
            if request.form:
                users = request.form.getlist('chk')
                self.conn.delete_users(users)
            return redirect(url_for('users'))
        except Exception as e:
            self.app.logger.error(f"Error updating users: {e}")

    def create_user(self):
        try:
            do_validation = True
            name = request.form['username']
            password = request.form["password"]
            request_user = request.form["hdnUserID"] or False
            group = request.form["group"]
            grouplist = self.conn.groups_list()
            user_aggregate_list = self.conn.users_aggregate()
            group_id = self.conn.check_group(group)
            group_access = self.conn.users_aggregate_access(username=session['user'])
            if request_user:
                result = next((item for item in user_aggregate_list if item['_id'] == ObjectId(request_user)), None)
                if result and result.get('username') != name:
                    do_validation = False

                if result.get('group')[0]['name'] != group:
                    do_validation = False

            if self.conn.check_user_name(user=name) and do_validation:
                return render_template('users.html', warning=True, users=user_aggregate_list, user_access=group_access[0], groups=grouplist, user=session['user'])
            if request_user:
                filter = {'_id': ObjectId(request_user)}
                update = {'$set': {'username': name, 'group_id': group_id['_id']}}
                if self.conn.update_user_details(filter, update):
                    return render_template('users.html', users=self.conn.users_aggregate(), user_access=group_access[0], groups=grouplist, user=session['user'])
            val = {"username": str(name), "group_id": group_id['_id'], "password": str(password)}
            self.conn.set_user(val)
            return redirect(url_for('users'))
        except Exception as e:
            self.app.logger.error(f"Error creating user: {e}")

    def users(self):
        try:
            if session.get("user"):
                grouplist = self.conn.groups_list()
                user_aggregate_list = self.conn.users_aggregate()
                group_access = self.conn.users_aggregate_access(username=session['user'])
                return render_template('users.html', users=user_aggregate_list, user_access=group_access[0], groups=grouplist, user=session['user'])
            else:
                return render_template('login.html', error="Your Session Expired")
        except Exception as e:
            self.app.logger.error(f"Error retrieving users: {e}")

    def view_bpt(self):
        try:
            if request.form:
                report = request.form.getlist('view')
                grid_out = self.gridfsbucket.open_download_stream_by_name(report[0])
                data = pd.read_excel(grid_out)
                return render_template('view_bpt.html', excelData=data.to_html())
        except Exception as e:
            self.app.logger.error(f"Error viewing BPT: {e}")

    def download_bpt(self):
        try:
            if request.form:
                report = request.form.getlist('download')
                data = self.conn.db.fs.files.find_one({'filename': report[0]})
                outputdata = self.gridfs.get(data['_id']).read()
                path = Path.home() / 'Downloads'
                filename = report[0] + '.csv'
                fullpath = os.path.join(path, filename)
                with open(fullpath, "wb") as file:
                    file.write(outputdata)
                return send_file(fullpath, as_attachment=True)
        except Exception as e:
            self.app.logger.error(f"Error downloading BPT: {e}")
            return Response(f"Error downloading file: {e}", status=500)

    def bpt(self):
        try:
            if session.get("user"):
                bpt_list = self.conn.bpt_list(filter=request.form if request.form else None)
                group_access = self.conn.users_aggregate_access(username=session['user'])
                return render_template('bpt.html', bpt=bpt_list, user_access=group_access[0], user=session['user'])
            else:
                return render_template('login.html', error="Your Session Expired")
        except Exception as e:
            self.app.logger.error(f"Error retrieving BPT: {e}")

    def home(self):
        try:
            session['user'] = request.form['username']
            session['password'] = request.form['password']
            res = self.conn.check_user(session['user'], session['password'])
            group_access = self.conn.users_aggregate_access(username=session['user'])
            if res:
                return render_template('dashboard.html', user_access=group_access[0], user=session['user'])
            else:
                return render_template('login.html', error="Invalid Username or Password")
        except Exception as e:
            self.app.logger.error(f"Error in home route: {e}")

    def dashboard(self):
        if session.get("user"):
            group_access = self.conn.users_aggregate_access(username=session['user'])
            return render_template('dashboard.html', user_access=group_access[0], user=session['user'])
        else:
            return render_template('login.html', error="Your Session Expired")

    def logout(self):
        session.clear()
        return render_template('login.html')

    def page_not_found(self, e):
        return render_template('404.html')

    def login(self):
        return render_template('login.html')

    def index(self):
        return redirect(url_for('login'))
    
    def data(self):
        sample = [{'id': 1, 'name': 'John Doe', 'email': 'johndoe@example.com'},
        {'id': 2, 'name': 'Jane Doe', 'email': 'janedoe@example.com'},
        {'id': 3, 'name': 'kane Doe', 'email': 'kanedoe@example.com'},
        {'id': 4, 'name': 'lane Doe', 'email': 'lanedoe@example.com'},
        {'id': 5, 'name': 'mane Doe', 'email': 'manedoe@example.com'},
        {'id': 6, 'name': 'nane Doe', 'email': 'nanedoe@example.com'},
        {'id': 7, 'name': 'oane Doe', 'email': 'oanedoe@example.com'},
        {'id': 8, 'name': 'pane Doe', 'email': 'panedoe@example.com'},
        {'id': 9, 'name': 'qane Doe', 'email': 'qanedoe@example.com'},
        {'id': 10, 'name': 'rane Doe', 'email': 'ranedoe@example.com'},
        {'id': 11, 'name': 'sane Doe', 'email': 'sanedoe@example.com'},]
        return render_template('data.html', data=sample)    

    def run(self):
        self.app.run(debug=True, host=self.app.config['FLASK_HOST'], port=self.app.config['FLASK_PORT'], threaded=True)

if __name__ == "__main__":
    app_instance = MyApp()
    app_instance.run()
