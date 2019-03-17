from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context

Base = declarative_base()


class User(Base):
	__tablename__ = 'users'

	id = Column(Integer, primary_key=True)
	username = Column(String(64), index=True)
	password_hash = Column(String(64))

	# User Info while login with OAuth
	name = Column(String(250), nullable=True)
	email = Column(String(250), nullable=True)
	picture = Column(String(250), nullable=True)

	def hash_password(self, password):
		self.password_hash = pwd_context.encrypt(password)

	def verify_password(self, password):
		return pwd_context.verify(password, self.password_hash)

	@property
	def serialize(self):
		return{
			self.username,
			self.name,
			self.email,
			self.picture
		}


engine = create_engine('sqlite:///users.db')
Base.metadata.create_all(engine)