## -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from threading import Thread
from decorator import decorator
from functools import wraps
import urllib2
import simplejson
from decorator import decorator
from flask import make_response, session, request, g, session

from grabarz import app, models
from grabarz.lib import beans

class HydraLog(object):
    """ Logs to normal application logger + extra logger to specific 
    application window """    
        
    def __init__(self, slot, heading="logger"):
        self.slot = slot
        self.message = ""
        self.heading = heading
        
        models.CallbackUpdate(self.get_window()).commit()
        
    def get_window(self):
        return beans.Window(
            slotname = self.slot,
            heading = self.heading,
            replace = True,
            savestate = True,
            object = beans.HTML(
                content = self.message,                
            )
        )
        
    def close(self):
        bean = beans.WindowChange(
            slotname = self.slot,
            action = 'close'
        )
        models.CallbackUpdate(bean, delay = timedelta(seconds = 5)).commit()
        
    def emit(self, message):
        self.message +=  '<br/>' + message      
        app.logger.debug(message)        
                                
        models.CallbackUpdate(self.get_window()).commit()
         

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
    
    
