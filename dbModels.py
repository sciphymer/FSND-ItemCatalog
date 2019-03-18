import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from userModel import User

Base = declarative_base()


class Category(Base):
	__tablename__ = 'categories'

	id = Column(Integer, primary_key=True)
	name = Column(String(80), nullable=False)
	# user_id = Column(Integer, ForeignKey(User.id))
	# user = relationship(User)


	@property
	def serialize(self):
		return {
			'id': self.id,
			'name': self.name,
		}


class Item(Base):
	__tablename__ = 'items'

	id = Column(Integer, primary_key=True)
	title = Column(String(80), nullable=False)
	description = Column(String(250), nullable=True)
	cat_id = Column(Integer, ForeignKey('categories.id'))
	category = relationship(Category)
	user_id = Column(Integer, ForeignKey(User.id))
	user = relationship(User)
	created_date = Column(DateTime, default=datetime.datetime.utcnow)


	@property
	def serialize(self):
		"""Return object data in easily serializeable format"""
		return {
			'id': self.id,
			'title': self.title,
			'description': self.description,
			'cat_id': self.cat_id
		}


engine = create_engine('sqlite:///sportCategories.db')
Base.metadata.create_all(engine)
