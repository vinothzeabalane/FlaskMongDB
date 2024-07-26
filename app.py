import os
from flask import Flask, flash, redirect, render_template, request, session, url_for, send_file, jsonify, Response
import gridfs
import pandas
import mongo
from pymongo import MongoClient
from gridfs import GridFSBucket
from pathlib import Path
from gevent.pywsgi import WSGIServer
from datetime import timedelta, datetime, timezone
from bson.objectid import ObjectId

app = Flask(__name__, static_url_path='/static')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)  # Session timeout set to 10 minutes
app.config.from_pyfile('config.cfg')
app.secret_key = os.urandom(12)


@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = app.config['PERMANENT_SESSION_LIFETIME']
    if 'last_activity' in session:
        naive_now = datetime.utcnow()
        aware_now = naive_now.replace(tzinfo=timezone.utc)
        last_activity = session.get('last_activity')

        # Ensure last_activity is timezone-aware
        if last_activity:
            # Assuming last_activity is a datetime object with timezone information
            if (aware_now - last_activity).total_seconds() > app.permanent_session_lifetime.total_seconds():
                session.clear()
                return render_template('login.html', error = "Your Session Expired")
    session['last_activity'] = datetime.utcnow()


@app.route('/account')
def account():
    access_right = get_access_user()
    return render_template('account.html',user=session['user'],password=session['password'], is_admin = access_right)


@app.route('/account_update', methods=['GET', 'POST'])
def account_update():
    try:
        if session.get("user"):
            oldpass = request.form["oldpass"]
            newpass = request.form["newpass"]
            access_right = get_access_user()
            res = get_mongo_connection().update_password(session['user'],oldpass,newpass)
            if res:
                flash('Your password has been updated successfully. <br/><br/> Re-login with new password!', 'success')
                return redirect(url_for('account'))
            else:
                return render_template('account.html',user=session['user'],is_admin = access_right, error = "Please enter correct old password")
        else:
            return render_template('login.html', error = "Your Session Expired")
    except Exception as e:
        print(e)
        
@app.route('/create_group', methods=['GET', 'POST'])
def create_group():
    try:
        name = request.form['name']
        res = get_mongo_connection().set_group(name)
        groups_list = get_mongo_connection().groups_list()
        access_right = get_access_user()
        if res:
            return redirect(url_for('groups'))
        else:
            return render_template("group.html",warning=True,groups=groups_list,user=session['user'],is_admin = access_right)
    except Exception as e:
        print(e)

@app.route('/groups')
def groups():
    try:
        if session.get("user"):
            res = get_mongo_connection().groups_list()
            access_right = get_access_user()
            return render_template('group.html',groups=res,user=session['user'],is_admin = access_right)
        else:
            return render_template('login.html', error = "Your Session Expired")
    except Exception as e:
        print(e)

@app.route('/update_group', methods=['GET', 'POST'])
def update_group():    
    try:
        access_right = get_access_user()
        grouplist = get_mongo_connection().groups_list()
        user_list = get_mongo_connection().users_list()
        if request.form:
            groups = request.form.getlist('chk')
            for i in groups:
                group_id = get_mongo_connection().check_group(i)
            res =  get_mongo_connection().check_group_in_users(group_id['_id'])
            if res:
                print("Warning: {} group is linked with one or more users. Please unlink before delete".format(i))
                return render_template("group.html",warning=True, error = "Warning: {} group is linked with one or more users. Please unlink before delete".format(i),users=user_list,groups=grouplist,user=session['user'],is_admin = access_right)
            res = get_mongo_connection().delete_groups(groups)
        return redirect(url_for('groups'))
    except Exception as e:
        print(e)
        
@app.route('/update_collection', methods=['GET', 'POST'])
def update_collection():
    try:
        if request.form:
            collections = request.form.getlist('chk')
            print(collections)
            res = get_mongo_connection().delete_collections(collections)
        return redirect(url_for('collections'))
    except Exception as e:
        print(e)

@app.route('/update_user', methods=['GET', 'POST'])
def update_user():
    try:
        if request.form:
            users = request.form.getlist('chk')
            res = get_mongo_connection().delete_users(users)
        return redirect(url_for('users'))
    except Exception as e:
        print(e)

@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    try:
        name = request.form['username']
        password = request.form["password"]
        request_user = request.form["hdnUserID"] or False
        group = request.form["group"]
        access_right = get_access_user()
        grouplist = get_mongo_connection().groups_list()
        # user_list = get_mongo_connection().users_list()
        user_aggregate_list = get_mongo_connection().users_aggregate()
        group = request.form["group"]
        admin = request.form.get("is_admin") or False
        group_id = get_mongo_connection().check_group(group)

        if request_user:
            filter = {'_id': ObjectId(request_user)}
            update = {'$set': {'username': name, 'group_id': group_id['_id'] }}
            if get_mongo_connection().update_user_details(filter,update):
                return render_template('users.html',users=get_mongo_connection().users_aggregate(),groups=get_mongo_connection().groups_list(),user=session['user'],is_admin = get_access_user())
        
        if get_mongo_connection().check_user_name(user=name):
            return render_template('users.html',warning=True,users=user_aggregate_list,groups=grouplist,user=session['user'],is_admin = access_right)
    
        val={"username":str(name),"group_id":group_id['_id'],"password":str(password),"is_admin":admin}

        res = get_mongo_connection().set_user(val)
        return redirect(url_for('users'))
    
    except Exception as e:
        print(e)

@app.route('/users')
def users():
    try:
        if session.get("user"):
            grouplist = get_mongo_connection().groups_list()
            # user_list = get_mongo_connection().users_list()
            user_aggregate_list = get_mongo_connection().users_aggregate()
            access_right = get_access_user()
             
            return render_template('users.html',users=user_aggregate_list,groups=grouplist,user=session['user'],is_admin = access_right)
        else:
            return render_template('login.html', error = "Your Session Expired")
    except Exception as e:
        print(e)

@app.route('/view_bpt', methods=['GET', 'POST'])
def view_bpt():
    try:
        if request.form:
            report = request.form.getlist('view')
            client = MongoClient("mongodb://localhost:27017/")
            db = client['openstack']
            fs = GridFSBucket(db)
            grid_out = fs.open_download_stream_by_name(report[0])
            data = pandas.read_excel(grid_out)
            return render_template('view_bpt.html', excelData = data.to_html())
    except Exception as e:
        print(e)

@app.route('/download_bpt', methods=['GET', 'POST'])
def download_bpt():
    try:
        if request.form:
            report = request.form.getlist('download')
            client = MongoClient("mongodb://localhost:27017/")
            db = client['openstack']
            fs = gridfs.GridFS(db)
            data = db.fs.files.find_one({'filename': report[0]})
            outputdata = fs.get(data['_id']).read()
            data = pandas.read_excel(outputdata)
            path = Path.home() / 'Downloads'
            filename = report[0]+'.csv'
            fullpath = os.path.join(path, filename)
            with open(fullpath, "wb") as file: 
                file.write(outputdata) 
            return send_file(fullpath , as_attachment = True)
              
    except Exception as e:
        # Log the error for debugging purposes
        app.logger.error(f"Error downloading file: {e}")
        # Return an error response or None
        return Response(f"Error downloading file: {e}", status=500)

@app.route('/bpt', methods=['GET', 'POST'])
def bpt():
    try:
        if session.get("user"):
            if request.form:
                bpt_list = get_mongo_connection().bpt_list(filter=request.form)
            else:
                bpt_list = get_mongo_connection().bpt_list(filter=None)
            grouplist = get_mongo_connection().groups_list()
            access_right = get_access_user()
                
            return render_template('bpt.html',bpt=bpt_list,groups=grouplist,user=session['user'],is_admin = access_right)
        else:
            return render_template('login.html', error = "Your Session Expired")
    except Exception as e:
        print(e)
        
@app.route('/home', methods=['GET', 'POST'])
def home():
    try:
        session['user'] = request.form['username']
        session['password'] = request.form['password']
        
        res = get_mongo_connection().check_user(session['user'],session['password'])
        access_right = get_access_user()
        
        if res:
            return render_template('dashboard.html', user=session['user'],is_admin = access_right)
        else:
            return render_template('login.html', error = "Invalid Username or Password")
    except Exception as e:
        print(e)

def get_mongo_connection():
    try:
        conn = mongo.MongoDB(host=app.config['MYSQL_HOST'],port=app.config['MYSQL_PORT'],db=app.config['MONGO_DB'])
        return conn
    except Exception as e:
        print(e)
    
def get_access_user():
    try:
        is_admin = get_mongo_connection().check_access_right(session['user'])
        if is_admin is None:
            access_right = False
        else:
            access_right = True
        return access_right
    except Exception as e:
        print(e)

@app.route('/dashboard')
def dashboard():
    if session.get("user"):
        access_right = get_access_user()
        return render_template('dashboard.html', user=session['user'],is_admin = access_right)
    else:
        return render_template('login.html', error = "Your Session Expired")

@app.route("/logout")
def logout():
    session.clear()
    return render_template('login.html')

#example code
@app.route('/data')
def data():
    data = [{'id': 1, 'name': 'John Doe', 'email': 'johndoe@example.com'},
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
    return render_template('data.html', data=data)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/')
def index():
    return redirect(url_for('login'))


if __name__ == "__main__":
    # http_server = WSGIServer(('localhost', 5000), app)
    # http_server.serve_forever()    
    app.run(debug=True, host=app.config['FLASK_HOST'], port=app.config['FLASK_PORT'], threaded=True)
