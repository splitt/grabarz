## -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import os
import time

from flask import Flask, g, request
from flaskext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
db = SQLAlchemy(app)

from views.layout import layout
from views.movies import movies
app.register_module(layout)
app.register_module(movies)