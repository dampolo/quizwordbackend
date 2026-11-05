# Quizword Backend

Django backend for the Quizword web and mobile apps. The frontend runs separately.

## Prerequisites

- Python 3.13 (used by this project's Dockerfile).
- A running PostgreSQL server (the Docker configuration uses PostgreSQL 17).
- A local copy of this repository.

Run the commands below from the project directory containing `manage.py`.

## 1. Create a virtual environment

```sh
python -m venv env
```

## 2. Activate the virtual environment

In your current Windows terminal:

```sh
env/Scripts/activate
```

Or explicitly select the Windows PowerShell activation script:

```powershell
.\env\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
env\Scripts\activate.bat
```

macOS or Linux:

```sh
source env/bin/activate
```

Activate the environment again whenever you open a new terminal.

## 3. Install dependencies

```sh
python -m pip install -r requirements.txt
```

## 4. Configure PostgreSQL and environment variables

Start PostgreSQL. Using pgAdmin or a PostgreSQL administrator connection, create a database and login, for example:

```sql
CREATE USER quizword WITH PASSWORD 'replace-with-your-local-password';
CREATE DATABASE quizword OWNER quizword;
```

Create `.env` beside `manage.py` with the following content. Replace the example values with your own. This file is ignored by Git; do not commit secrets.

```dotenv
DEBUG=True
SECRET_KEY=replace-with-a-generated-secret
DB_NAME=quizword
DB_USER=quizword
DB_PASSWORD=replace-with-your-local-password
DB_HOST=127.0.0.1
DB_PORT=5432

# Frontend URL used for email links and redirects; keep the trailing slash.
MAIN_API=http://127.0.0.1:5173/

SENDGRID_API_KEY=replace-with-your-sendgrid-api-key
DEFAULT_FROM_EMAIL=replace-with-your-verified-sender-email
RECAPTCHA_SECRET_KEY=replace-with-your-recaptcha-secret
GOOGLE_TRANSLATE_API_KEY=replace-with-your-google-translate-api-key
GOOGLE_CLIENT_ID=replace-with-your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=replace-with-your-google-oauth-client-secret
```

Generate a Django secret key with:

```sh
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

All variables above are read by the current settings. Placeholder values let the settings load, but email, reCAPTCHA, translation, and Google sign-in require valid credentials and service configuration to work. For local Google sign-in, configure this callback URL in your Google OAuth application: `http://127.0.0.1:8000/api/accounts/google/login/callback/`.

## 5. Set up the database

Apply the migrations already included in the repository:

```sh
python manage.py migrate
```

After changing Django models, create migrations and apply them:

```sh
python manage.py makemigrations
python manage.py migrate
```

Optionally create an administrator account:

```sh
python manage.py createsuperuser
```

Check the configuration:

```sh
python manage.py check
```

## 6. Run for web

```sh
python manage.py runserver
```

The backend runs at `http://127.0.0.1:8000/`. API routes are under `/api/`; the admin page is at `http://127.0.0.1:8000/admin/`. There is no homepage route at `/`.

Start the web frontend separately and configure its API address to use this backend. The current development settings allow the browser frontend origin `http://127.0.0.1:5173`. For a different frontend origin, update `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` in `quizword_core/settings.py`.

## 7. Run for mobile

```sh
python manage.py runserver 0.0.0.0:8000
```

For a physical phone:

1. Connect the computer and phone to the same local network.
2. Find the computer's local IPv4 address (`ipconfig` on Windows).
3. Add that address to the development `ALLOWED_HOSTS` list in `quizword_core/settings.py`. The current list includes `192.168.178.92`; replace it if your address differs.
4. Configure the mobile app's API address to use `http://<computer-ip>:8000/api/`.
5. Allow inbound connections to port 8000 on your private network if your firewall blocks them.

`0.0.0.0` is the server's listening address. Connect from your phone using the computer's local IP address.

These commands run Django's development server. Production deployment requires separate configuration.

## Stop the server

Press `Ctrl+C`. To leave the virtual environment:

```sh
deactivate
```

## Update the dependency list

After intentionally installing, upgrading, or removing packages in the project's virtual environment, save the installed versions:

```sh
python -m pip freeze > requirements.txt
```

Review the changes before committing `requirements.txt`. This command overwrites the file with everything installed in the active environment. It is not a startup step: when setting up the project, use `python -m pip install -r requirements.txt` instead.
