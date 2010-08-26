## -*- coding: utf-8 -*-
from decorator import decorator

def fixkeys(func, *args, **kwargs):    
    """ Decorator changing '_' for '-' in dictionary keys. """
    foo = func(*args, **kwargs)
    
    for k, v in foo.items():
        if '_' in k:
            foo[k.replace('_', '-')] = v
            del foo[k]
    return foo
fixkeys = decorator(fixkeys)