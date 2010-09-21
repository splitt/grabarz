## -*- coding: utf-8 -*-

from flask import Flask, g, request, make_response
from flaskext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
db = SQLAlchemy(app)

from views.layout import layout
from views.files import files
from views.system import system
from views.event_calendar import event_calendar
app.register_module(layout)
app.register_module(files)
app.register_module(system)
app.register_module(event_calendar)