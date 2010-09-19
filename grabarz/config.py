## -*- coding: utf-8 -*-
from os.path import join

class Config(object):
    SECRET_KEY = '^&@&*$@#BRKFJ*(@#RUY(*#FH#YUBG#*F@&R*G#GF@&*#FG'
    UPDATE_INTERVAL = 100000
    
class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:////home/mzajonz/workspace/grabarz/db/devel.db'
    DEBUG = True
    DUMP_DIR = '/home/mzajonz/workspace/grabarz/shares'
    MOVIES_DIR = join(DUMP_DIR, 'movies')
    MOVIES_READY_DIR = join(MOVIES_DIR, 'ready')
    MOVIES_WATCHED_DIR = join(MOVIES_DIR, 'watched')
    MOVIES_DOWNLOADING_DIR = join(MOVIES_DIR, 'downloading')
    MOVIES_FOUND_DIR = join(MOVIES_DIR, 'found')
    URL_ROOT = 'http://grabarz.milosz'

class ProductionConfig(Config):    
    DATABASE = '../db/dev.db'
    DEBUG = False
    DUMP_DIR = '/shares/rtorrent/'
    MOVIES_DIR = '/shares/rtorrent/movies'
    MOVIES_READY_DIR = '/shares/rtorrent/movies/ready'
    MOVIES_WACTHED_DIR = '/shares/rtorrent/movies/watched'
    MOVIES_DOWNLOADING_DIR = '/shares/rtorrent/movies/downloading'
    MOVIES_FOUND_DIR = '/shares/rtorrent/movies/found'
    URL_ROOT = 'http://grabarz.zajonz.pl'