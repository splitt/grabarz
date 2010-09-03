## -*- coding: utf-8 -*-
from __future__ import with_statement
import os
from flask import Flask, g, session, request, redirect, make_response, session

app = Flask('grabarz')


import grabarz
path = '/'.join(grabarz.__path__[0].split('/')[:-1]) + '/__instance__.txt'
#: Read config depended on instance type
with open(path) as f:
    instance = f.read().capitalize().strip()
app.config.from_object('grabarz.config.%sConfig' % instance)

from views.layout import layout
from views.movies import movies
app.register_module(layout)
app.register_module(movies)

#@app.before_request
#def before_request():
#    pass
#
#@app.after_request
#def after_request(response):
#    pass