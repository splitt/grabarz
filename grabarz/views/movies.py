## -*- coding: utf-8 -*-
from flask import Module
from grabarz.lib.beans import Config, Desktop, MultiLoader, HTML, Menu
from grabarz.lib.utils import jsonify
from grabarz import app

movies = Module(__name__)