## -*- coding: utf-8 -*-
from flask import Flask, g, session, request, redirect

app = Flask('grabarz')

from views.layout import layout
app.register_module(layout)


@app.before_request
def before_request():
    pass


@app.after_request
def after_request(response):
    pass
