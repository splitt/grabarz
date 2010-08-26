## -*- coding: utf-8 -*-
from flask import Module
from grabarz.lib.beans import Config, Desktop, MultiLoader, HTML
from grabarz.lib.utils import jsonify, fixkeys

layout = Module(__name__)

@layout.route('/layout/config')
@jsonify
def config():
    return beans.Config(
        title="Komornik",
        default_errorwindowtitle="Wystąpił błąd aplikacji",
        debug=True,
        theme="olive",
        history_enabled=True,
    )

@layout.route('/layout/slots')
@jsonify
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
@jsonify
def init():
    return MultiLoader()


@layout.route('/layout/null')
@jsonify
def null():
    return HTML(
        heading=None,
        content="",
        scroll="NONE",
    )
