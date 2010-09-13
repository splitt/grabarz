## -*- coding: utf-8 -*-
from grabarz import db

class System(db.Model):
    __tablename__ = 'system'
    
    def __init__(self, updates):            
        self.updates = updates 