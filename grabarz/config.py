## -*- coding: utf-8 -*-
from os.path import abspath

class Config(object):
    SECRET_KEY = '^&@&*$@#BRKFJ*(@#RUY(*#FH#YUBG#*F@&R*G#GF@&*#FG'
    
class DevelopmentConfig(Config):
    DATABASE = '../db/prod.db'
    DEBUG = True
    DUMP_DIR = '/'.join(abspath('').split('/')[:-1])+'/shares'

class ProductionConfig(Config):    
    DATABASE = '../db/dev.db'
    DEBUG = False
