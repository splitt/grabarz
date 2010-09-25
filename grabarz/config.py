## -*- coding: utf-8 -*-
from os.path import join

class Config(object):
    SECRET_KEY = '^&@&*$@#BRKFJ*(@#RUY(*#FH#YUBG#*F@&R*G#GF@&*#FG'
    UPDATE_INTERVAL = 1000
    
class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:////home/mzajonz/workspace/grabarz/db/devel.db'
    DEBUG = True
    URL_ROOT = 'http://grabarz.milosz'    
    FAKE_TORRENT = True    
    DUMP_DIR = '/home/mzajonz/workspace/grabarz/shares'    
    MOVIES_DIR = join(DUMP_DIR, 'movies')
    MOVIES_FOUNDED_DIR = join(MOVIES_DIR, 'founded')
    MOVIES_QUEUED_DIR = join(MOVIES_DIR, 'queued')
    MOVIES_DL_DIR = join(MOVIES_DIR, 'downloading')
    MOVIES_UP_DIR = join(MOVIES_DIR, 'uploading')
    MOVIES_COMPLETED_DIR = join(MOVIES_DIR, 'completed')
    MOVIES_WATCHED_DIR = join(MOVIES_DIR, 'watched')        

    RTORRENT_DIR = join(DUMP_DIR, 'rtorrent')
    RTORRENT_WATCH_DIR = join(RTORRENT_DIR, 'watch')
    RTORRENT_SESSION_DIR = join(RTORRENT_DIR, 'session')
    RTORRENT_DOWNLOADING_DIR = join(RTORRENT_DIR, 'downloading')
    RTORRENT_COMPLETED_DIR = join(RTORRENT_DIR, 'completed')
    
    TVSHOWS_DIR = join(DUMP_DIR, 'tvshows')
    TVSHOWS_ARCHIVE_DIR = join(TVSHOWS_DIR, 'archive')
    TVSHOWS_CURRENT_DIR = join(TVSHOWS_DIR, 'current')
    
    OTHER_FILES_DIR = join(DUMP_DIR, 'other')     

class ProductionConfig(Config):    
    DATABASE = '../db/dev.db'
    DEBUG = False
    DUMP_DIR = '/shares/rtorrent/'
    MOVIES_DIR = '/shares/rtorrent/movies'
    MOVIES_COMPLETED_DIR = '/shares/rtorrent/movies/completed'
    MOVIES_WACTHED_DIR = '/shares/rtorrent/movies/watched'
    MOVIES_DL_DIR = '/shares/rtorrent/movies/downloading'
    MOVIES_FOUNDED_DIR = '/shares/rtorrent/movies/founded'
    URL_ROOT = 'http://grabarz.zajonz.pl'