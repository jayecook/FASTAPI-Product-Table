Localhost for the file to be run can be completed by loading all subsequent files and running as a uvicorn app.
admin login information can be provided upon request.

Steps to be completed if running into issues from VS Code - 
Open terminal and run the following in Bash - python -m venv .venv
Activate the environment - source .venv/Scripts/activate , you should see (.venv)
Upgrade or install the necessary pip - python -m pip install --upgrade pip
* To be completely sure that all packages are running, run the following command - pip install fastapi uvicorn sqlalchemy jinja2 python-multipart python-dotenv passlib psycopg2-binary itsdangerous email-validator
Run the packages - pip install -r requirements.txt
Next, initialize the database - python init_db.py
Reload the uvicorn pacakge/module if needed - python -m uvicorn app:app --reload

You should now see on your terminal - 
Uvicorn running on http://127.0.0.1:8000
Application startup complete.

You can now access the site from a browser.

Admin login information - 
Username: admin
Password: admin123
