from flask import Flask, render_template, request, flash, redirect, url_for, g, abort, jsonify
from flask import session as login_session
from flask import make_response
from flask_httpauth import HTTPBasicAuth
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from dbModels import Base, Category, Item, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import random, string, requests
import json

auth = HTTPBasicAuth()

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

@auth.verify_password
def verify_password(username, password):
	user = user_session.query(User).filter_by(username = username).first()
	if not user or not user.verify_password(password):
		return False
	g.user = user
	return True

@app.route('/api/v1/users', methods = ['POST'])
def new_user():
	username = request.json.get('username')
	password = request.json.get('password')
	if username is None or password is None:
		print "missing arguments"
		abort(400)

	if user_session.query(User).filter_by(username = username).first() is not None:
		print "existing user"
		user = user_session.query(User).filter_by(username=username).first()
		return jsonify({'message':'user already exists'}), 200, {'Location': url_for('get_user', id = user.id, _external = True)}
	#Create new users
	user = User(username = username)
	user.hash_password(password)
	user_session.add(user)
	user_session.commit()
	return jsonify({ 'username': user.username }), 201, {'Location': url_for('get_user', id = user.id, _external = True)}

@app.route('/api/v1/catalog',methods=['GET'])
@auth.login_required
def get_catelog():
	return jsonify({'category': [category.serialize for category in categories]})

@app.route('/api/v1/catalog/<string:category>/items',methods=['GET'])
@auth.login_required
def get_items(category):
	items = app_session.query(Item).filter(Item.category.has(name=category)).all()
	return jsonify({'category': category, 'item':[item.serialize for item in items]})

@app.route('/login/webAuth',methods =['POST'])
#local DB Auth
def checkAuth():
	username = request.form['username']
	password = request.form['password']
	if username is None or password is None:
		response = make_response(
			json.dumps("Either username or password is empty"), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	user = user_session.query(User).filter_by(username = username).first()
	output = '<p> You have login successfully! </p>'
	if user is None:
		#Create new user
		user = User(username = username)
		user.hash_password(password)
		user_session.add(user)
		user_session.commit()
		user = user_session.query(User).filter_by(username = username).first()
		login_session['username'] = username
		login_session['user_id'] = user.id
		login_session['provider'] = "local"
		output += '<p> The login credentials entered cannot be found in database, </p>'
		output += '<p> a new account has been created for you! </p>'
		output += '<h1>Welcome, '
		output += login_session['username']
		output += '!</h1>'
		flash("Now logged in as %s" % login_session['username'],'info')
	else:
		if user.verify_password(password):
			user = user_session.query(User).filter_by(username = username).first()
			login_session['username'] = username
			login_session['user_id'] = user.id
			login_session['provider'] = "local"
			output += '<h1>Welcome, '
			output += login_session['username']
			output += '!</h1>'
		else:
			flash("Your password is incorrect, Please try again!",'error')
			return render_template("login3.html")
	return render_template("loginSuccess.html", result=output)

@app.route('/login')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
	login_session['state'] = state
	return render_template('login3.html', STATE=state, redirectPath="/")

@app.route('/logout')
def logout():
	if 'provider' in login_session:
		if login_session['provider'] == 'local':
			del login_session['username']
			del login_session['user_id']
			del login_session['provider']
			flash("You have successfully been logged out.",'info')
			return redirect(url_for('showCategories'))
		if login_session['provider'] == 'google':
			gdisconnect()
			del login_session['gplus_id']
			del login_session['access_token']
		#for future extension
		if login_session['provider'] == 'facebook':
			fbdisconnect()
			del login_session['facebook_id']
		del login_session['username']
		del login_session['email']
		del login_session['picture']
		del login_session['user_id']
		del login_session['provider']
		flash("You have successfully been logged out.",'info')
		return redirect(url_for('showCategories'))
	else:
		flash("You were not logged in",'info')
		return redirect(url_for('showCategories'))

@app.route('/')
@app.route('/catalog')
def showCategories():
	user_items = []
	user_items = app_session.query(Item).order_by(Item.created_date.desc()).limit(10).all()
	return render_template('index.html', categories=categories, items = user_items)

@app.route('/newItem', methods=['GET', 'POST'])
def newItem():
	if request.method == 'GET':
		if 'username' not in login_session:
			return redirect('/login')
		return render_template('newItem.html', categories=categories)
	if request.method == 'POST':
		if request.form['title'] and request.form['description'] and request.form['cat_id']:
			item = Item(
				title=request.form['title'],
				description=request.form['description'],
				cat_id=request.form['cat_id'],
				user_id=login_session['user_id'])
			app_session.add(item)
			app_session.commit()
			flash('New Item %s is successfully Created.' % item.title,'info')
			return redirect(url_for('showCategories'))

@app.route('/catalog/<string:category>/items')
def showItems(category):
	items = app_session.query(Item).filter(Item.category.has(name=category)).all()
	itemQty = len(items)
	return render_template('item.html', items=items, categories=categories, category=category, itemQty=itemQty)


@app.route('/catalog/<string:category>/<string:item>')
def showDescription(category, item):
	item = app_session.query(Item)\
		.filter(Item.category.has(name=category))\
		.filter_by(title=item).one()
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
			flash('Category ID: %s, %s Successfully updated' % (edit_item.cat_id, edit_item.title),'info')
			return redirect(url_for('showCategories'))
		else:
			flash('The form is incomplete!','error')
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
		return redirect(url_for('showItems', category=category))

#for OAuth Auth
def createUser(login_session):
	newUser = User(username=login_session['email'], name=login_session['username'],
					email=login_session['email'], picture=login_session['picture'])
	user_session.add(newUser)
	user_session.commit()
	user = user_session.query(User).filter_by(email=login_session['email']).one()
	return user.id

#for OAuth Auth
def getUserInfo(user_id):
	user = user_session.query(User).filter_by(id=user_id).one()
	return user

#for OAuth Auth
def getUserID(email):
	try:
		user = user_session.query(User).filter_by(email=email).one()
		return user.id
	except:
		return None

#for Google OAuth Auth
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

#for Google OAuth Auth
@app.route('/gconnect', methods=['POST'])
def gconnect():
	# Validate state token
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	# Obtain authorization code
	code = request.data
	try:
		# Upgrade the authorization code into a credentials object
		print "Upgrade the authorization code into a credentials object"
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		print "oauth_flow=%s"%oauth_flow
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
		print "credentials=%s"%credentials
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
	flash("you are now logged in as %s" % login_session['username'],'info')
	return output

if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host='0.0.0.0', port=5050)
