from flask import Flask, g
from peewee import *   # noqa
from peewee import SqliteDatabase

app = Flask(__name__)

app.config.from_object('settings')

database = SqliteDatabase(app.config['DATABASE'])

from mhvdb2.admin import admin  # noqa
app.register_blueprint(admin, url_prefix='/admin')


@app.before_request
def before_request():
    g.db = database
    g.db.connect()


@app.after_request
def after_request(response):
    g.db.close()
    return response

import mhvdb2.routes   # noqa

from mhvdb2.models import Entity, User  # noqa

database.connect()
if not Entity.table_exists():
    Entity.create_table()
if not User.table_exists():
    User.create_table()
database.close()
