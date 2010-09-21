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
    MOVIES_COMPLETED_DIR = join(MOVIES_DIR, 'completed')
    MOVIES_WATCHED_DIR = join(MOVIES_DIR, 'watched')
    MOVIES_DOWNLOADING_DIR = join(MOVIES_DIR, 'downloading')
    MOVIES_UPLOADING_DIR = join(MOVIES_DIR, 'uploading')
    MOVIES_QUEUED_DIR = join(MOVIES_DIR, 'queued')
    MOVIES_FOUND_DIR = join(MOVIES_DIR, 'found')
    
    RTORRENT_DIR = join(DUMP_DIR, 'rtorrent')
    RTORRENT_COMPLETED_DIR = join(RTORRENT_DIR, 'completed')
    RTORRENT_SESSION_DIR = join(RTORRENT_DIR, 'session')
    RTORRENT_WATCH_DIR = join(RTORRENT_DIR, 'watch')
    
    TVSHOWS_DIR = join(DUMP_DIR, 'tvshows')
    TVSHOWS_ARCHIVE_DIR = join(TVSHOWS_DIR, 'archive')
    TVSHOWS_CURRENT_DIR = join(TVSHOWS_DIR, 'current')
    
    URL_ROOT = 'http://grabarz.milosz'

class ProductionConfig(Config):    
    DATABASE = '../db/dev.db'
    DEBUG = False
    DUMP_DIR = '/shares/rtorrent/'
    MOVIES_DIR = '/shares/rtorrent/movies'
    MOVIES_COMPLETED_DIR = '/shares/rtorrent/movies/completed'
    MOVIES_WACTHED_DIR = '/shares/rtorrent/movies/watched'
    MOVIES_DOWNLOADING_DIR = '/shares/rtorrent/movies/downloading'
    MOVIES_FOUND_DIR = '/shares/rtorrent/movies/found'
    URL_ROOT = 'http://grabarz.zajonz.pl'