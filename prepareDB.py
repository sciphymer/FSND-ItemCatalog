from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from dbModels import Base, Category, Item, User

sqlite_connStr = 'sqlite:////sportCategories.db'
postgreSQL_connStr = 'postgresql://dbadmin:dbadmin@localhost:5432/flaskappDB'
app_engine = create_engine(postgreSQL_connStr)

Base.metadata.bind = app_engine

app_DBSession = sessionmaker(bind=app_engine)

app_session = app_DBSession()

category = Category(name="Soccer")
app_session.add(category)
category = Category(name="BasketBall")
app_session.add(category)
category = Category(name="Baseball")
app_session.add(category)
category = Category(name="Frisbee")
app_session.add(category)
category = Category(name="Snowboarding")
app_session.add(category)
category = Category(name="Rock Climbing")
app_session.add(category)
category = Category(name="Foosball")
app_session.add(category)
category = Category(name="Skating")
app_session.add(category)
category = Category(name="Hockey")
app_session.add(category)

app_session.commit()