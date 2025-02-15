# Django App

## Overview

A Django-based web application designed for [briefly describe what your app does]. This project serves as [mention key functionalities or features].

## Features

- [Feature 1]
- [Feature 2]
- [Feature 3]
- [Feature 4]

## Requirements

- Python 3.x
- Django 3.x or later
- [Any other dependencies, e.g., PostgreSQL, Redis, etc.]

## Installation

### 1. Clone the repository:

```
git clone https://github.com/fatjan/be_lernen
cd be_lernen
```

2. Create a virtual environment:
```
python3 -m venv venv
```

3. Activate the virtual environment:
```
source venv/bin/activate
```

4. Install dependencies
```
pip install -r requirements.txt
```

5. Set up environment variables:
Copy the .env.example and paste it as .env file, fill in the required fields

6. Run migrations
```
python manage.py migrate
```

7. Create a superuser (for admin access):
```
python manage.py createsuperuser
```
Follow the prompts to create an admin user for accessing the Django admin panel.

8. Run the development server:
```
python manage.py runserver
```

Your app will be accessible at http://127.0.0.1:8000/

9. Testing
To run tests for your app, use the following command:

```
python manage.py test
```
