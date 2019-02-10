from flask import Flask, render_template, request, flash, redirect, url_for
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from dbModels import Base, Category, Item, User

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


@app.route('/')
def showCategories():
	return render_template('categories.html', categories=categories)


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
	return render_template('item.html', items=items, category=category, itemQty=itemQty)


@app.route('/catalog/<string:category>/<string:item>')
def showDescription(category, item):
	item = app_session.query(Item)\
		.filter(Item.category.has(name=category))\
		.filter_by(title=item).one()
	return render_template('description.html', category=category, item=item)


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


if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0', port=5050)
