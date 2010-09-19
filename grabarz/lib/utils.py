## -*- coding: utf-8 -*-
import time
import simplejson
from datetime import datetime, timedelta
from decorator import decorator
import urllib2

from flask import request, g, session, make_response
from grabarz import app, models
from grabarz.lib import beans
         

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


def post2get():
    """ Returns GET arguments from post MultiDict """
    try:
        request.form
    except(AttributeError):
        return ''
    
    return '?'+'&'.join(["%s=%s" % (k, v) 
                         for k, v in request.form.items(True)])
    
    
