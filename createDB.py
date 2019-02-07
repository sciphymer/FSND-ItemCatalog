from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dbModels import Item, Category, Base
from userModel import User

user_engine = create_engine('sqlite:///users.db')
app_engine = create_engine('sqlite:///sportCategories.db')

Base.metadata.bind = app_engine
Base.metadata.bind = user_engine
app_DBSession = sessionmaker(bind=app_engine)
user_DBSession = sessionmaker(bind=user_engine)
app_session = app_DBSession()
user_session = user_DBSession()


user = User(id=1, username='admin', password_hash='admin')
user_session.add(user)
user_session.commit()
categories = (["Soccer", "BasketBall",
			  "Baseball", "Frisbee",
			  "Snowboarding", "Rock Climbing",
			   "Foosball", "Skating", "Hockey"])
for category in categories:
	cat = Category(name=category, user_id=1)
	app_session.add(cat)
app_session.commit()

