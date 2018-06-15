#!/usr/bin/env python
"""Create a new admin user able to view the /reports endpoint."""
from getpass import getpass
from werkzeug.security import generate_password_hash
import sys

from flask import Flask
from app.models import User, db
from app import create_app

def main():
    """Main entry point for script."""
    with Flask.app_context(create_app()):
        db.metadata.create_all(db.engine)
        if User.query.all():
            print ('A user already exists! Create another? (y/n):'),
            create = input()
            if create == 'n':
                return

        print('Enter email address: '),
        email = input()
        print('Enter username'),
        username = input()
        password = getpass()
        assert password == getpass('Password (again):')

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            admin=True)
        db.session.add(user)
        db.session.commit()
        print('User added.')


if __name__ == '__main__':
    sys.exit(main())