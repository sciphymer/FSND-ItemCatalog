from flask import Flask, render_template, request, flash, redirect, url_for

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from dbModels import Base, Category, Item, User

user_engine = create_engine('sqlite:///users.db')
app_engine = create_engine('sqlite:///sportCategories.db')
app = Flask(__name__)

Base.metadata.bind = app_engine
Base.metadata.bind = user_engine
app_DBSession = sessionmaker(bind=app_engine)
user_DBSession = sessionmaker(bind=user_engine)
app_session = app_DBSession()
user_session = user_DBSession()


@app.route('/')
def showCategories():
	categories = app_session.query(Category).all
	return render_template('categories.html', categories=categories)


@app.route('/catalog/<string:category>/items')
def showItems(category):
	cat = app_session.query(Category).filter_by(name=category).one()
	categories = app_session.query(Item).filter_by(cat_id=cat.id).all
	return render_template('item.html', categories=categories)


@app.route('/catalog/<string:category>/<string:item>')
def showDescription(category, item):
	cat = app_session.query(Category).filter_by(name=category).one()
	item = app_session.query(Item).filter_by(title=item).filter_by(cat_id=cat.id).one()
	return render_template('description.html', title=item.title, description=item.description)


@app.route('/catalog/<string:category>/<string:item>/edit', methods=['GET', 'POST'])
def editItem(category, item):
	edit_item = app_session.query(Item).filter(Item.category.has(name=category)).filter_by(title=item).one()
	if request.method == 'GET':
		return render_template('editItem.html',item=edit_item)
	if request.method == 'POST':
		if request.form['title'] and request.form['description'] and request.form['category']:
			edit_item.title = request.form['title']
			edit_item.description = request.form['description']
			db_cat = app_session.query(Category).filter_by(name=category).one()
			edit_item.cat_id = db_cat.id
			app_session.add(edit_item)
			flash('Category ID: %s, %s Successfully updated' % (edit_item.cat_id, edit_item.title))
			app_session.commit()
			return redirect(url_for('showCategories'))
		else:
			flash('The form is incomplete!')
			return render_template('editItem.html',item=edit_item)


@app.route('/catalog/<string:category>/<string:item>/delete', methods=['GET', 'POST'])
def deleteItem(category, item):
	delete_item = app_session.query(Item).filter(Item.category.has(name=category)).filter_by(title=item).one()
	if request.method == 'GET':
		return render_template('deleteItem.html, item=delete_item')
	if request.method == 'POST':
		app_session.delete(delete_item)
		app_session.commit()
		return redirect(url_for('showItems(category)', category = category))


if __name__ == '__main__':
	app.run()
