from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, make_response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
import requests
import json
import random
import string
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2

# Initial configuration - create SQLAlchemy session

engine = create_engine('postgresql:///catalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Define FLask app
app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "catalog_app"

# Home page handler - displays category list and latest items


@app.route('/')
@app.route('/home/')
def homePage():
    categories = session.query(Category).all()
    # Query the 10 latest items, sorted by creation date, along with the
    # category names
    items = session.query(
        Item.id,
        Item.title,
        Item.description,
        Item.created_date,
        Category.name).join(
        Category,
        Item.category_id == Category.id).order_by(
            Item.created_date.desc()).limit(10).all()
    return render_template('home.html', categories=categories, items=items)

# Show all items in a selected category


@app.route('/<int:category_id>/items')
def showCategory(category_id):
    categories = session.query(Category).all()
    selected_category = session.query(Category).filter_by(id=category_id).one()
    q = session.query(Item).filter_by(
        category_id=category_id).order_by(
        Item.created_date.desc())
    count = q.count()
    items = q.all()
    return render_template(
        'category.html',
        categories=categories,
        items=items,
        category_name=selected_category.name,
        count=count)

# Add a new item

@app.route('/category/new', methods=['GET', 'POST'])
def addCategory():
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    if request.method == 'POST':
        print "post method for add category"
        create_action = request.form['create_action']
        if create_action == 'Create':
            name = request.form['name']
            newcategory = Category(name=name)
            session.add(newcategory)
            session.commit()
            flash('New category %s Successfully Created' % (newcategory.name))
        return redirect(url_for('homePage'))
    else:
        return render_template('newcategory.html')

@app.route('/item/new', methods=['GET', 'POST'])
def addItem():
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    categories = session.query(Category).all()
    if request.method == 'POST':
        create_action = request.form['create_action']
        if create_action == 'Create':
            title = request.form['title']
            description = request.form['description']
            category_id = request.form['category']
            user_id = login_session['user_id']
            newitem = Item(
                title=title,
                description=description,
                category_id=category_id,
                user_id=user_id)
            session.add(newitem)
            session.commit()
            flash('New item for %s Successfully Created' % (newitem.title))
        return redirect(url_for('homePage'))
    else:
        return render_template('newitem.html', categories=categories)

# Show Item details


@app.route('/item/<int:item_id>/')
def showItem(item_id, del_mode='False'):
    item = session.query(Item).filter_by(id=item_id).one()
    return render_template('showitem.html', item=item, del_mode=del_mode)

# Edit item details


@app.route('/item/<int:item_id>/edit/', methods=['GET', 'POST'])
def editItem(item_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    item = session.query(Item).filter_by(id=item_id).one()
    categories = session.query(Category).all()

    if request.method == 'GET':
        return render_template(
            'edititem.html',
            item=item,
            categories=categories)
    else:
        edit_action = request.form['edit_action']
        if edit_action == 'Save':
            item.title = request.form['title']
            item.description = request.form['description']
            item.category_id = request.form['category']
            session.add(item)
            session.commit()
            flash('Your changes have been saved.')
        return redirect(url_for('showItem', item_id=item.id))

# Delete an item


@app.route('/item/<int:item_id>/delete/', methods=['POST', 'GET'])
def deleteItem(item_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    item = session.query(Item).filter_by(id=item_id).one()

    if request.method == 'POST':
        delete_action = request.form['delete_action']
        print delete_action
        if delete_action == 'Yes':
            session.delete(item)
            session.commit()
            flash('Item %s has been deleted.' % item.title)
            return redirect(url_for('homePage'))
        else:
            return redirect(
                url_for(
                    'showItem',
                    item_id=item.id,
                    del_mode='False'))

    if request.method == 'GET':
        return render_template('showitem.html', item=item, del_mode='True')

# JSON endpoint giving all details of all items in a particular category


@app.route('/category/<int:category_id>/JSON')
def categoryItemsJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(
        category_id=category.id).all()
    return jsonify(Items=[i.serialize for i in items])

# JSON endpoint giving details of a particular item


@app.route('/item/<int:item_id>/JSON')
def itemJSON(item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Item=item.serialize)

# JSON endpoint giving all details of all categories


@app.route('/category/JSON')
def categoryJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])

# Login handler, returns the random state value.


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # Login file facilitates login using google and facebook
    return render_template('login.html', STATE=state)

# Connects using google account


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session.get('state'):
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    login_session['provider'] = 'google'

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# Adds the user details to the user table


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

# Provides the user details using user id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

# Queries user's email using user id


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except BaseException:
        return None

# disconnects google account


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session.get('username')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session.get(
        'access_token')
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result.status == 200:
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps(
                'Failed to revoke token for given user.',
                400))
        response.headers['Content-Type'] = 'application/json'
        return response

# Connects to facebook account


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/v2.8/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    data = json.loads(result)
    token = 'access_token=' + data['access_token']

    url = 'https://graph.facebook.com/v2.9/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly
    # logout, let's strip out the information before the equals sign in our
    # token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.9/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output

# Disconnects facebook account


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
        facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out" + result

# common logout function to disconnect either google or facebook accounts


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            # del login_session['gplus_id']
            # del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
            del login_session['username']
            del login_session['email']
            del login_session['picture']
            del login_session['user_id']
            del login_session['access_token']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('homePage'))
    else:
        flash("You were not logged in")
        return redirect(url_for('homePage'))


# Run the app
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
