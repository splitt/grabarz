## -*- coding: utf-8 -*-

from datetime import timedelta
from decorator import decorator
import simplejson

from flask import make_response, session
from grabarz import models, db, app
from grabarz.lib import beans

def push_bean(bean, method = 'session',*args, **kw):                
    if method == 'session':
        session['callback_updates'].append(bean)
    else:
        models.CallbackUpdate(bean, *args, **kw).commit()
        
        
def reload_slot(slotnames, method = 'session'):
    """ Reload given slot in next request """        
    
    if not isinstance(slotnames, (tuple, list)):
        slotnames = [slotnames]
                
    bean = beans.Reload(
        slot = slotnames
    )
    return push_bean(bean, method = method)

def reload_listing(sid, method = 'session'):        
    bean = beans.ReloadListing(
        listing = sid,
    )    
    return push_bean(bean, method = method)      
        
def jsonify(func, *args, **kwargs):
    """ Transform dict into json and returns it as response """    
    adict = func(*args, **kwargs)
    if not isinstance(adict, dict):
        return adict
    
            
    #: getting updates from session and database
    
    updates = list(session['callback_updates'])        
    updates.extend(models.CallbackUpdate.dump())
        
    if updates:
        if not adict.get('type') == 'composite':
            adict = beans._wrap('composite', [adict])            
        
        adict['result'].extend(updates)
    
    json = simplejson.dumps(adict)
    response = make_response(json)    
    response.headers['Content-Type'] = 'application/json'
    session['callback_updates'] = []
    db.session.commit()        
    return response
jsonify = decorator(jsonify)


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
        push_bean(bean, method = 'sql', delay=timedelta(seconds = 5))
        
    def emit(self, message):
        self.message +=  '<br/>' + message      
        app.logger.debug(message.replace('&nbsp;',' ').replace('<BR/>', '\n'))
        push_bean(self.get_window(), method = 'sql')