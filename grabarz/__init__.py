## -*- coding: utf-8 -*-
from flask import Flask, g, session, request, redirect, make_response

app = Flask('grabarz')

#: read config depended on instance type
with open("../__instance__.txt") as f:
    instance = f.read()            
app.config.from_object('config.%sConfig' % instance.capitalize())

from views.layout import layout
app.register_module(layout)

@app.before_request
def before_request():
    pass

@app.after_request
def after_request(response):
    pass