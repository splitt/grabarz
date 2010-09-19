## -*- coding: utf-8 -*-

from flask import Flask, g, request, make_response
from flaskext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
db = SQLAlchemy(app)

from views.layout import layout
from views.movies import movies
from views.system import system
from views.event_calendar import event_calendar
app.register_module(layout)
app.register_module(movies)
app.register_module(system)
app.register_module(event_calendar)