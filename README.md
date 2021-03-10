# Task Manager API
Task Manager api provide api calls for task manager app.
## Setup
The first thing to do is to clone the repository:
```
$ git clone https://github.com/MariaLeghari/taskmanager.git
$ cd taskmanager
```
Create a virtual environment to install dependencies in and activate it:
```
$ virtualenv -p python3 env
$ source env/bin/activate
```
Then install the dependencies:
```
(env)$ pip install -r requirements.txt
```
Once `pip` has finished downloading the dependencies:
```
(env)$ cd taskmanager
(env)$ python manager.py runserver
```

## Format of Environment Variables
Set the value of following variable in your `.env` file
```
ALLOWED_HOSTS = 
DATABASE_NAME =
DATABASE_USER =
DATABASE_PASSWORD =
DATABASE_HOST =
DATABASE_PORT =
DEBUG =
SECRET_KEY =
```

## API Documentation and working
You can read Task Manager Api documentation from following link:
```
https://app.swaggerhub.com/apis/MariaLeghari/task-manager_api/v1
```
or by calling `swagger/` after setup
```
http://127.0.0.1:8000/swagger/
```
