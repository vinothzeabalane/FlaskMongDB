import os
from flask import Flask, flash, redirect, render_template, request, session, url_for

import mongo

app = Flask(__name__, static_url_path='/static')
app.config.from_pyfile('config.cfg')
app.secret_key = os.urandom(12)


@app.route('/create_collection', methods=['GET', 'POST'])
def create_collection():
    try:
        name = request.form['name']
        address = request.form["address"]
        group = request.form["group"]
        phone = request.form.get("phone")
        offer_amt = request.form.get("offer_amt")
        c1_care_of = request.form.get("c1_care_of")
        c1_collected_amt = request.form.get("c1_collected_amt")
        c2_care_of = request.form.get("c2_care_of")
        c2_collected_amt = request.form.get("c2_collected_amt")
        payment_mode = request.form.get("payment_mode")
        remarks = request.form.get("remarks")
    
        val={
            "name":str(name),
            "address":str(address),
            "group":str(group),
            "phone":str(phone),
            "offer_amt":str(offer_amt),
            "c1_care_of":str(c1_care_of),
            "c1_collected_amt":str(c1_collected_amt),
            "c2_care_of":str(c2_care_of),            
            "c2_collected_amt":str(c2_collected_amt),
            "payment_mode":str(payment_mode),
            "remarks":str(remarks),
            "user":session.get("user")            
        }
        res = get_mongo_connection().set_collection(val)
        return redirect(url_for('collections'))
    except Exception as e:
        print(e)


@app.route('/account')
def account():
    access_right = get_access_user()
    return render_template('account.html',user=session['user'],is_admin = access_right)


@app.route('/account_update', methods=['GET', 'POST'])
def account_update():
    try:
        if session.get("user"):
            oldpass = request.form["oldpass"]
            newpass = request.form["newpass"]
            res = get_mongo_connection().update_password(session['user'],oldpass,newpass)
            if res:
                return redirect(url_for('logout'))
            else:
                return render_template('account.html', error = "Please enter correct Old password")
        else:
            return render_template('login.html', error = "Your Session Expired")
    except Exception as e:
        print(e)
        

@app.route('/collections')
def collections():
    try:
        if session.get("user"):
            grouplist = get_mongo_connection().groups_list()
            res = get_mongo_connection().collections_list(session.get("user"))
            access_right = get_access_user()
            
            return render_template('collection.html',collections=res,groups=grouplist,user=session['user'],is_admin = access_right)
        else:
            return render_template('login.html', error = "Your Session Expired")
    except Exception as e:
        print(e)
        
        
@app.route('/collections_status')
def collections_status():
    try:
        if session.get("user"):
            res = get_mongo_connection().collections_status(session.get("user"))
            access_right = get_access_user()
            
            return render_template('collection_status.html',collections=res,user=session['user'],is_admin = access_right)
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
        if request.form:
            groups = request.form.getlist('chk')
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
        group = request.form["group"]
        admin = request.form.get("is_admin") or False
    
        val={"username":str(name),"group":group,"password":str(password),"is_admin":admin}
        
        res = get_mongo_connection().set_user(val)
        return redirect(url_for('users'))
    
    except Exception as e:
        print(e)


@app.route('/users')
def users():
    try:
        if session.get("user"):
            grouplist = get_mongo_connection().groups_list()
            user_list = get_mongo_connection().users_list()
            access_right = get_access_user()
             
            return render_template('users.html',users=user_list,groups=grouplist,user=session['user'],is_admin = access_right)
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
    session.pop('username', None)
    session.pop('password', None)
    return render_template('login.html')


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
    app.run(debug=False, host=app.config['FLASK_HOST'], port=app.config['FLASK_PORT'], threaded=True)
