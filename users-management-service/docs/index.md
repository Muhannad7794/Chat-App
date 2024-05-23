# Welcome to Users Management Service Documentation

For full documentation visit [mkdocs.org](https://www.mkdocs.org).

## Overview

The Users Management Service is responsible for handling all user-related operations within our application, including user registration, authentication, profile management, and security features such as password reset and email verification.

## Features

- **User Registration**: Allows new users to register by providing essential details such as username, email, and password. The registration process also includes sending a verification email to confirm the user's email address.
- **Authentication**: Supports various authentication mechanisms, including token-based authentication, to ensure secure access to the application.
- **Profile Management**: Users can update their profiles and manage settings like email preferences and account details.
- **Password Management**: Includes features for password change and reset, enhancing the security and usability of the application.
- **Email Verification**: Ensures that the email provided by users during registration is valid and belongs to them.

## Technical Details

- **Framework**: Django 5.0
- **API**: Django REST Framework for creating RESTful services.
- **Database**: MySQL, connected via Django’s ORM.
- **Authentication**: Token-based authentication using Django REST Framework's token system.
- **Email Service**: Utilizes Django's email functionality integrated with an SMTP server for sending verification and notification emails.

## Configuration

Here's an example of essential settings from `settings.py`:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": "localhost",
        "PORT": 3306,
        "NAME": "users_db",
        "USER": "user",
        "PASSWORD": "password",
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-email-password'

## API End Points:
Endpoint	HTTP Method	Description
/api/users/	POST	Register a new user.
/api/users/login/	POST	Authenticate a user and return a token.
/api/users/update/	PUT	Update user profile details.
/api/users/password/	PUT	Change user password.
/api/users/reset/	POST	Reset user password and send it via email.
/api/users/verify/{verification_code}/	GET	Verify user's email address.

## Commands
mkdocs new [dir-name] - Create a new project.
mkdocs serve - Start the live-reloading docs server.
mkdocs build - Build the documentation site.
mkdocs -h - Print help message and exit.

```
