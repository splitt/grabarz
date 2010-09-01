## -*- coding: utf-8 -*-
import os
from flask import Flask, g, session, request, redirect, make_response
app = Flask('grabarz')

#: Read config depended on instance type
app.logger.error('A value for debugging')

import grabarz

path = '/'.join(grabarz.__path__[0].split('/')[:-1]) + '/__instance__.txt'

with open(path) as f:
    instance = f.read().capitalize().strip()
app.config.from_object('grabarz.config.%sConfig' % instance)

from views.layout import layout
app.register_module(layout)

#@app.before_request
#def before_request():
#    pass
#
#@app.after_request
#def after_request(response):
#    pass