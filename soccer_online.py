#!/usr/bin/env python
import os

from flask_script import Manager, Shell

from app import create_app, db
from app.models import Role, User

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)


def make_shell_context():
  return dict(app=app, db=db)


manager.add_command('shell', Shell(make_context=make_shell_context))


@manager.command
def test(coverage=False):
  import unittest
  tests = unittest.TestLoader().discover('tests')
  unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def restart_db():
  print('Dropping tables')
  db.drop_all()

  print('Creating tables')
  db.create_all()

  print('Initializing roles')
  Role.create_roles()

  print('Initializing admin user')
  User.create_admin_user()


if __name__ == '__main__':
  manager.run()
