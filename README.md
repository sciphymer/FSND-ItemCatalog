# FSND-Project2-ItemCatalog

#Introduction

This project is to develop an web application that show a lists of items within a variety of categories. There is a user registration and authentication system implemented by both the Google OAuth and local Database. Registered users will be able to post, edit and delete their own items on the application. Users only have right to do changes on their own posts. The application includes API endpoint for authenicated users to get protected resources.
The whole web application from Frontend to Backend is built from scratches.

#Technology used

##Backend
- This application is written in Python, using Flask framework to implement the web server and do CRUD routing and Jinja2 in Flask for rending HTML templates.
- The database is in sqlite3. Using SQLAlchemy ORM library to communicate with the sqlite3 database and doing read write of data.
- User registration and authenication part can choose from choosing OAuth 2.0 protocol and local database.
To use OAuth 2.0 with Google account login, the application is first registered on the "Google Developer Console", a "client_secrets.json" is downloaded from the "Developer Console". A "client id" in the client_secrets.json is needed to attached to the web application, so that during the Google account OAuth login, Google knows the user is authenticating the application.
For the local database authentication, the user account is created by saving the username and hashed password in the database. Everytime, only hashed password is compared to increase the security.

##Frontend
- Bootstrap 4.0 has been used to assist the layout styling.


#How to run

Prepare an ubuntu or linux environment which support Python v2.7.
Download the project folder, and run ```python prepareDB.py``` to load the default item categories to the database, sportCategories.db will be created.
Then run the application by ```python app.py``` the web application will be host on the localhost:5050 correspondingly. In the initial run of the application, the database is empty, you will need to create the users account and add the catelog's items one by one.

#How to use the application

- On the top right hand corner, press the "login in" button, you can choose either using Google account to sign or create a local account.
- After successfully signed in, you can click "Add Item" on the home page and add Item's Title, description, and choosing its Category belonged to.
- To view the created item, navigate from the left hand side menu by clicking the corresponding category.
- While you are logged in, the 'Edit' and 'Delete' buttons on the item description page are available for the item's author.
- There is an API endpoint provided for getting the database data in json format. The details of the endpoints are described as follows.

#API endpoints

- localhost:5050/api/v1/users, Method="POST"
Description: To create new user account.
Request body parameters:
{"username":"enter_your_username","password":"enter_your_password"}
Return: If user account is successfully created, a json format of username will be return

- /api/v1/catalog, Method="GET"
Description: To get all the category names
Request body parameters: Basic Auth is required using the user account credentials
Return: A list of Category names in json format

- /api/v1/catalog/<string:category>/items, Method="GET"
Description: To get all the items under a specific category name.
Request body parameters: Basic Auth is required using the user account credentials
Return: A list of item details in json format

*This project is created by Vincent Ng for Udacity FullStack Nanodegree course @2019*
