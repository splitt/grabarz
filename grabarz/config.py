## -*- coding: utf-8 -*-

class Config(object):
    SECRET_KEY = '^&@&*$@#BRKFJ*(@#RUY(*#FH#YUBG#*F@&R*G#GF@&*#FG'
    
class DevelopmentConfig(Config):
    DATABASE = '../db/prod.db'
    DEBUG = True    

class ProductionConfig(Config):
    DEBUG = False
    DATABASE = '../db/dev.db'
