## -*- coding: utf-8 -*-
from datetime import datetime
from threading import Thread
from decorator import decorator
from functools import wraps
import urllib2
import simplejson
from decorator import decorator
from flask import make_response, session, request, g, session

from grabarz import app
from grabarz.lib import beans

class HydraLog(object):
    """ Logs to normal application logger + extra logger to specific 
    application window """
        
    def __init__(self, window_slot, initial_message=""):
        session['hydra_loggers'][window_slot] = initial_message
        self.window_slot = window_slot        
        
        session['updates'].append(
            beans.Window(
                slotname = self.window_slot,
                url = '/layout/logger_window?slot_id=%s' % window_slot
            )                                
        )
        session.modified = True
        
    def emit(self, message):        
        app.logger.debug(message)        
        session['hydra_loggers'][self.window_slot] += message
        session.modified = True
            
        session['updates'].append(
            beans.Reload(
                slot = self.window_slot,                   
            )
        )
         

def download(url, local_name):
    """Copy the contents of a file from a given URL
    to a local file.
    """
    web_file = urllib2.urlopen(url)
    local_file = open(local_name, 'w')
    local_file.write(web_file.read())
    web_file.close()
    local_file.close()


def fixkeys(func, *args, **kwargs):    
    """ Decorator changing '_' for '-' in dictionary keys. """
    foo = func(*args, **kwargs)
    
    for k, v in foo.items():
        if '_' in k:
            foo[k.replace('_', '-')] = v
            del foo[k]
    return foo
fixkeys = decorator(fixkeys)


def jsonify(func, *args, **kwargs):
    """ Transform dict into json and returns it as response """    
    rv = func(*args, **kwargs)
    json = simplejson.dumps(rv)
    response = make_response(json)
    response.headers['Content-Type'] = 'application/json'
    return response
jsonify = decorator(jsonify)


def post2get():
    """ Returns GET arguments from post MultiDict """
    try:
        request.form
    except(AttributeError):
        return ''
    
    return '?'+'&'.join(["%s=%s" % (k, v) 
                         for k, v in request.form.items(True)])
    
    
