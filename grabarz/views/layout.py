## -*- coding: utf-8 -*-
from flask import Module
from grabarz.lib import beans
from grabarz.lib.utils import beanify, fixkeys

layout = Module(__name__)

@layout.route('/layout/config')
@fixkeys()
def config():
    return beans.Config(
        title="Komornik",
        default_errorwindowtitle="Wystąpił błąd aplikacji",
        debug=True,
        theme="olive",
        history_enabled=True,
    )

@layout.route('/layout/slots')
def slots():
    return beans.Desktop(
        heading='',
        menu_items=[
            dict(
                label='Dodaj wpis',
                icon='icon-note_add',
                link=dict(
                    url='/entry/add',
                    slot='dashboard',
                )
            ),
            dict(
                label='Zmiana danych użytkownika',
                icon='icon-user_edit',
                link=dict(
                    url='/user/change_data',
                    slot='new_window',
                )
            ),
            dict(
                label='Wyloguj',
                icon='icon-door_out',
                link=dict(
                    url='/auth/logout',
                    slot='dashboard',
                )
            ),
        ],
        show_desktop_tool=True,
        show_group_windows_tool=True,
        icon='icon-user',
        button_label='Menu',

        slots=[
             dict(
                 id='dashboard',
                 split=True,
                 data=['WEST', 800],
                 margins=[5, 5, 5, 5],
                 scroll='NONE',
                 url="/dashboard/show",
             ),

             dict(
                 id='history',
                 split=True,
                 data=['CENTER', 100, 100, 100],
                 margins=[5, 5, 5, 5],
                 scroll='AUTO',
                 url="/history/show",
             ),
        ]
    )


@layout.route('/layout/init')
@beanify("multiloader")
def init():
    return []

@layout.route('/layout/logo')
@beanify("html")
def logo():
    return dict(
        heading=None,
        scroll="NONE",
        content='<img src="/static/_komornik.jpg"/>',
    )


@layout.route('/layout/null')
@beanify("html")
def null():
    return dict(
        heading=None,
        content="",
        scroll="NONE",
    )
