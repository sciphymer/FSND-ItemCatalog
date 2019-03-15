from flask import Flask, render_template, request, flash, redirect, url_for
from flask import session as login_session
from flask import make_response
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from dbModels import Base, Category, Item, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import random, string, requests
import json

user_engine = create_engine('sqlite:///users.db', connect_args={'check_same_thread': False})
app_engine = create_engine('sqlite:///sportCategories.db', connect_args={'check_same_thread': False})
app = Flask(__name__)

Base.metadata.bind = app_engine
Base.metadata.bind = user_engine
app_DBSession = sessionmaker(bind=app_engine)
user_DBSession = sessionmaker(bind=user_engine)
app_session = app_DBSession()
user_session = user_DBSession()

categories = app_session.query(Category).all()

CLIENT_ID = json.loads(
	open('client_secrets.json', 'r').read())['web']['client_id']

@app.route('/login')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
	print "state %s" % state
	login_session['state'] = state
	return render_template('login3.html', STATE=state, redirectPath="/")

@app.route('/logout')
def logout():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCategories'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCategories'))

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
	url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
		app_id, app_secret, access_token)
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]

	# Use token to get user info from API
	userinfo_url = "https://graph.facebook.com/v2.8/me"
	'''
		Due to the formatting for the result from the server token exchange we have to
		split the token first on commas and select the first index which gives us the key : value
		for the server access token then we split it on colons to pull out the actual token value
		and replace the remaining quotes with nothing so that it can be used directly in the graph
		api calls
	'''
	token = result.split(',')[0].split(':')[1].replace('"', '')

	url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	# print "url sent for API access:%s"% url
	# print "API JSON result: %s" % result
	data = json.loads(result)
	login_session['provider'] = 'facebook'
	login_session['username'] = data["name"]
	login_session['email'] = data["email"]
	login_session['facebook_id'] = data["id"]

	# The token must be stored in the login_session in order to properly logout
	login_session['access_token'] = token

	# Get user picture
	url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
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


@app.route('/fbdisconnect')
def fbdisconnect():
	facebook_id = login_session['facebook_id']
	# The access token must me included to successfully logout
	access_token = login_session['access_token']
	url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
	h = httplib2.Http()
	result = h.request(url, 'DELETE')[1]
	return "you have been logged out"


@app.route('/gconnect', methods=['POST'])
def gconnect():
	# Validate state token
	print "hit the route /gconnect"
	if request.args.get('state') != login_session['state']:
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

	# Check that the access token is valid.
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
		response = make_response(json.dumps('Current user is already connected.'),
								 200)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Store the access token in the session for later use.
	login_session['access_token'] = credentials.access_token
	login_session['gplus_id'] = gplus_id

	# Get user info
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)

	data = answer.json()

	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']
	# ADD PROVIDER TO LOGIN SESSION
	login_session['provider'] = 'google'

	# see if user exists, if it doesn't make a new one
	user_id = getUserID(data["email"])
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

@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/')
@app.route('/catalog')
def showCategories():
	return render_template('index.html', categories=categories)

@app.route('/newItem', methods=['GET', 'POST'])
def newItem():
	if request.method == 'GET':
		return render_template('newItem.html', categories=categories)
	if request.method == 'POST':
		if request.form['title'] and request.form['description'] and request.form['cat_id']:
			item = Item(
				title=request.form['title'],
				description=request.form['description'],
				cat_id=request.form['cat_id'])
			app_session.add(item)
			app_session.commit()
			return redirect(url_for('showCategories'))


@app.route('/catalog/<string:category>/items')
def showItems(category):
	items = app_session.query(Item).filter(Item.category.has(name=category)).all()
	itemQty = len(items)
	return render_template('item.html', items=items, categories=categories, category=category, itemQty=itemQty)


@app.route('/catalog/<string:category>/<string:item>')
def showDescription(category, item):
	print category
	print item
	item = app_session.query(Item)\
		.filter(Item.category.has(name=category))\
		.filter_by(title=item).one()
	print item.title
	print item.description
	return render_template('description.html', categories=categories, category=category, item=item)


@app.route('/catalog/<string:category>/<string:item>/edit', methods=['GET', 'POST'])
def editItem(category, item):
	edit_item = app_session.query(Item).filter(Item.category.has(name=category)).filter_by(title=item).one()
	if request.method == 'GET':
		return render_template('editItem.html', item=edit_item, categories=categories, category=category)
	if request.method == 'POST':
		if request.form['title'] and request.form['description'] and request.form['cat_id']:
			edit_item.title = request.form['title']
			edit_item.description = request.form['description']
			edit_item.cat_id = request.form['cat_id']
			app_session.add(edit_item)
			app_session.commit()
			#flash('Category ID: %s, %s Successfully updated' % (edit_item.cat_id, edit_item.title))
			return redirect(url_for('showCategories'))
		else:
			flash('The form is incomplete!')
			return render_template('editItem.html', item=edit_item)


@app.route('/catalog/<string:category>/<string:item>/delete', methods=['GET', 'POST'])
def deleteItem(category, item):
	delete_item = app_session.query(Item)\
		.filter(Item.category.has(name=category))\
		.filter_by(title=item).one_or_none()
	if delete_item is not None:
		if request.method == 'GET':
			return render_template('deleteItem.html', item=delete_item, category=category)
		if request.method == 'POST':
			app_session.delete(delete_item)
			app_session.commit()
			return redirect(url_for('showItems', category=category))
	else:
		#flash('Item does not exist in db')
		return redirect(url_for('showItems', category=category))

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    user_session.add(newUser)
    user_session.commit()
    user = user_session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = user_session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = user_session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host='0.0.0.0', port=5050)
