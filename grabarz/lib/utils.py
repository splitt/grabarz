## -*- coding: utf-8 -*-
import simplejson
from decorator import decorator

from flask import make_response, session

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


def wrap(type, result):
    return dict(
        type=type,
        result=result,
    )


def wrapped(type, *args, **kwargs):
    """ Dekorator, który zawija slownik pod dany klucz
    
    @param type: str
    @param result: dict
    """
    def call(func, *args, **kwargs):
        return wrap(type, func(*args, **kwargs))
    return decorator(call)

def set_flash(text, title = 'Info'):
    session['messages'].append([title, text])
