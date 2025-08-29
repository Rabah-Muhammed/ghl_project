# Go HighLevel Contact Updater

This is a Django project to update custom fields for HighLevel contacts via OAuth integration. The project allows users to log in via HighLevel, view a dashboard, and update a random contact with a specific custom field.

---

## Features

- OAuth 2.0 login with HighLevel
- Dashboard displaying location information
- Update a random contact with a custom field
- Success and error pages with detailed messages
- Token management with automatic refresh

---

## Technologies Used

- Python 3
- Django
- TailwindCSS
- Requests
- SQLite (default database)
- HighLevel API

---

## Project Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd ghl_project
```
2. **Create and activate virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
```
3. **Install dependencies**
```bash
pip install -r requirements.txt
```
4. **Create .env file**
```bash
CLIENT_ID=<your-highlevel-client-id>
CLIENT_SECRET=<your-highlevel-client-secret>
REDIRECT_URI=http://127.0.0.1/
```
5. **Apply migrations**
```bash
python manage.py migrate
```
6. **Run the development server**
```bash
sudo python manage.py runserver 0.0.0.0:80
```
#### Note: Apache must be stopped as Django will use port 80.

## Usage

- Open the app in your browser: http://127.0.0.1/
- Click Login to authenticate with HighLevel.
- After login, you will be redirected to the Dashboard.
- Click Update Random Contact to update the custom field DFS Booking Zoom Link.
- See the success or error page with details.

## Project Structure

```bash
ghl_project/
├─ hl_app/
│  ├─ models.py
│  ├─ views.py
│  ├─ urls.py
│  └─ templates/
│     ├─ dashboard.html
│     ├─ success.html
│     ├─ message.html
│     └─ redirect_login.html
├─ ghl_project/
│  ├─ settings.py
│  ├─ urls.py
│  └─ wsgi.py
└─ manage.py
```

## Notes

- Tokens are stored in the database (HighLevelToken) and automatically refreshed when expired.
- The app requires the redirect URL http://127.0.0.1/ as per HighLevel OAuth settings.
- Use TailwindCSS for all frontend styling.
