
# Description

This is a test Flask API for a simple application where football/soccer fans will create fantasy teams and will be able to sell or buy players.

# Requirements

  * MySQL Server version 5.7
  * Python version 3.6
  * Pip version 21.0.1


# Set up the environment

## Set up the Database

  Create databases `localhost/soccer_online` and `localhost/test_soccer_online`

  Create user, grant all permissions to both databases and add user configuration in `config.py`

## Installation

  Install app requirements running `pip install -r requirements.txt`
  
  If you prefer to run the app without prepending `python` command, change permissions to `soccer_online.py` and make it executable.

## Initialize the Database

  Run `python soccer_online.py restart_db` or `./soccer_online.py restart_db`


# Run server

  Run `python soccer_online.py runserver` or `./soccer_online.py runserver`


# Run tests

  Run `python soccer_online.py test` or `./soccer_online.py test`