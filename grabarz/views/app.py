# -*- coding: utf-8 -*-

from calendar import Calendar
from collections import defaultdict
from urllib import urlencode
import datetime
import logging
import cgi
import traceback
from stxnext.piu.memcacheutil import MemcacheUtility
from vwbackoffice.lib.base import *
from vwbackoffice.lib.helpers import create_tab, beaninify, date_formatter,\
                                     unicode_urlencode, batching
from vwbackoffice.lib.auth.auth_helpers import get_loggedin_user_id, get_user_profile
from vwbackoffice.lib.auth.auth_helpers import get_loggedin_user_data
from vwbackoffice.lib.report_helpers import _get_consultants
from vwbackoffice.lib.mappings.common import application_details_inmapping, \
                                             application_details_get_outmapping
from pylons import request, config as pylons_config, session
from pylons.controllers.util import redirect
from stxnext.piu import iwm_call
from stxnext.piu.commonutils import IWMResponseError
from stxnext.xmlmapper import DictStruct, DictEntry, IterationStruct,\
                              ListStruct
from stxnext.xmlmapper import Node, TextNode, Attr, BaseNode, Entry

WEEKDAYS = [u'Pn', u'Wt', u'Śr', u'Cz', u'Pt', u'So', u'Nd']
MONTHS = [
    u'grudzień',
    u'styczeń', u'luty', u'marzec', u'kwiecień', u'maj',
    u'czerwiec', u'lipiec', u'sierpień', u'wrzesień',
    u'październik', u'listopad', u'grudzień',
    u'styczeń']
COLSIZE = 40
CALENDAR = Calendar()

notification_list_inmapping = Node('notification-list',
    TextNode('date-from', key='from'),
    TextNode('date-to', key='to'),
    TextNode('notification-id', key='id'),
    TextNode('operator-id', key='operator'),
    show_empty=True,
)

notification_add_inmapping = Node('notification-add',
    Node('notification',
        TextNode('operator-id', key='operator'),
        TextNode('application-id', key='task-short-id'),
        Node('author',
            Node('operator',
                TextNode('id', key='author'),
                TextNode('first-name', key='first-name'),
                TextNode('last-name', key='last-name'),
            ),
        ),
        TextNode('date-time', key='datetime',
                 formatter=lambda t:t.strftime('%Y-%m-%dT%H:%M:%S')),
        TextNode('description', key='text'),
    ),
)

notification_delete_inmapping = Node('notification-delete',
    TextNode('notification-id', key='id'),
)

notification_list_outmapping = IterationStruct(
        row = DictStruct(
            DictEntry('id', path='id'),
            DictEntry('date',
                path='date-time',
                formatter=lambda x:
                    datetime.datetime.strptime(x, '%Y-%m-%dT%H:%M:%S'),
            ),
            DictEntry('text', path='description'),
            DictEntry('operator', path='operator-id'),
            DictEntry('application', path='application-id'),
            DictStruct('author',
                DictEntry('first-name', path='author/operator/first-name'),
                DictEntry('last-name', path='author/operator/last-name'),
                DictEntry('id', path='author/operator/id'),
                DictEntry('mail', path='mail'),
            ),
            path='notification',
        ),
        show_empty = True,
    )


#def memcached(func, key_name):
#    def wrapper(*args, **kw):
#        mc = MemcacheUtility()
#        value = mc.get(key_name)
#        if schedule is not None:
#            return value
#        value = func(*args, **kw)
#        mc.set(key_name, value)
#        return value
#    return wrapper


class AppController(BaseController):
    """Controller serving application window."""

    def get_year_month_day(self):
        """
        Get the year, month and day from the request parameters.
        Use today for the missing values.
        """

        today = datetime.date.today()
        try:
            year = int(request.params['year'])
        except (KeyError, ValueError):
            year = today.year
        try:
            month = int(request.params['month'])
        except (KeyError, ValueError):
            month = today.month
        try:
            day = int(request.params['day'])
        except (KeyError, ValueError):
            day = today.day
        try:
            row = int(request.params['row'])
            column = int(request.params['column'])
        except (KeyError, ValueError):
            return year, month, day
        calendar = CALENDAR.monthdayscalendar(year, month)
        try:
            day = calendar[row][column]
        except IndexError:
            day = 0
        return year, month, day


    def get_note(self, note_id):
        data = iwm_call(notification_list_inmapping,
                        {'id': note_id},
                        notification_list_outmapping)
        return data[0]

    def get_schedule(self, year=None, month=None, day=None):
        """
        Pobiera z IWM liste powiadomień z danego miesiąca.
        """
        params = {}
        if year is not None:
            if month is not None:
                if day is not None:
                    params['from'] = '%d-%02d-%02dT00:00:00' % (year, month, day)
                    params['to'] = '%d-%02d-%02dT23:59:59' % (year, month, day)
                else:
                    params['from'] = '%d-%02d-01T00:00:00' % (year, month)
                    params['to'] = '%d-%02d-31T23:59:59' % (year, month)
            else:
                params['from'] = '%d-01-01T00:00:00' % year
                params['to'] = '%d-12-31T00:00:00' % year
        params['operator'] = get_loggedin_user_id()
        #params['author'] = get_loggedin_user_id()
        try:
            data = iwm_call(notification_list_inmapping, params,
                        notification_list_outmapping)
        except IWMResponseError:
            redirect_to('/calendar/app/handle_error')
        schedule = defaultdict(list)
        for note in data:
            date = note['date']
            schedule[(date.year, date.month,
                      date.day)].append(((date.hour, date.minute), note))
        return schedule


    @beaninify('composite')
    def handle_error(self):
        tu = {
            'type': 'timer-unregister',
            'result': {
                'name': 'calendar-reload'
                }
            }
        window_loader = {
                'type': 'multiloader',
                'result': [{'url': '/calendar/app/show_error_window', 'slot': 'internal'}]
                }
        return [
                tu, window_loader
                ]

    @beaninify('window')
    def show_error_window(self):
        w = {
                'heading': 'Wystąpił błąd aplikacji',
                'slotname': 'calendar-app-error',
                'width': 400,
                'height': 240,
                'html': u'<pre>Wystąpił błąd podczas odświeżania kalendarza.\n'
                    u'Odświeżanie kalendarza zostało wyłączone.</pre'
            }
        return w

    @beaninify('window')
    def calendar_note(self):
        """
        Displays note details.
        """
        json = {
                'maximizable': False,
                'resizeable': True,
                'minimizable': True,
                'icon': 'icon-note',
                'slotname': 'calendar_note_window',
                'heading': u'Przypomnienie',
                'width': 266,
                'height': 322,
                'object': {
                    'type': 'form',
                    'result': {
                        'heading': u'Przypomnienie',
                        'formdefs': [],
                        'buttons': [],
                    },
                }
        }
        return json

    @beaninify('composite')
    def calendar_window(self):
        """
        Displays the calendar window.
        """

        slots = [
            {
                'id': 'calendar-menu',
                'data': ['NORTH', 27],
                'margins': [2, 2, 2, 2],
                'layout': 'fit'
            },
            {
                'id': 'calendar-content',
                'data': ['CENTER', 0],
                'margins': [0, 0, 2, 2],
                'layout': 'fit',
                'scroll': 'NONE'
            },
            {
                'id': 'calendar-notes',
                'data': ['EAST', 396],
                'margins': [0, 2, 2, 2],
#                'layout': 'fit',
                'scroll': 'AUTOY'
            },
        ]
        init = [
           {'url': '/calendar/app/calendar_menu',
            'slot': 'calendar-menu'},
           {'url': '/calendar/app/calendar_listing',
            'slot': 'calendar-content'},
           {'url': '/calendar/app/calendar_notes',
            'slot': 'calendar-notes'},
        ]
        json = {
            'maximizable': False,
            'resizeable': False,
            'minimizable': True,
            'icon': 'icon-calendar',
            'slotname': 'calendar_window',
            'heading': 'Kalendarz',
            'width': COLSIZE*7+26+396,
            'height': 6*38+122,
            'slots': slots,
            'object': {
                'type': 'composite',
                'result': [
                    {
                        'type': 'multiloader',
                        'result': init
                    }
                ]
            },
            'events': {
                'onclose': {
                    'url': "/calendar/app/calendar_close",
                    'slot': "internal",
                }
            }
        }
        return [
            {
                'type': 'window',
                'result': json,
            },
            {
                "type": "timer-unregister",
                "result": {
                    "name": "calendar-reload",
                },
            },
            {
                "type": "timer-register",
                "result": {
                    "name": "calendar-reload",
                    "action": "/calendar/app/calendar_reload",
                    "interval": 1000 * 180,
                    "slot": "internal",
                },
            },
        ]

    @beaninify('composite')
    def calendar_close(self):
        return [
            {
                "type": "timer-unregister",
                "result": {
                    "name": "calendar-reload",
                },
            },
        ]

    @beaninify('actions')
    def calendar_menu(self):
        """
        Displays the top menu.
        """

        year, month, day = self.get_year_month_day()
        url = '/calendar/app/calendar_refresh?year=%d&month=%d'
        links = [
            {
                'type': 'button',
                'title': MONTHS[month-1].title(),
                'link': {
                    'url': url % (year, (month-2)%12+1),
                    'slot': 'internal',
                },
                "icon": "icon-date_previous"
                },
            {
                'type': 'menu',
                'title': u'Miesiac',
                'icon': 'icon-date',
                'links': [{
                    'type': 'button',
                    'title': MONTHS[m],
                    'link': {
                        'url': url % (year, m),
                        'slot': 'internal',
                    },
                } for m in range(1, 13)],
            },
            {
                'type': 'button',
                'title': MONTHS[month+1].title(),
                'link': {
                    'url': url % (year, month%12+1),
                    'slot': 'internal',
                },
                "icon": "icon-date_next"
            },
            {'type': 'separator', },
            {"type": "fill", },
            {'type': 'separator', },
            {
                'type': 'button',
                'title': str(year-1),
                'link': {
                    'url': url % (year-1, month),
                    'slot': 'internal',
                },
                "icon": "icon-control_rewind"
            },
            {
                'type': 'menu',
                'title': u'Rok',
                'icon': 'icon-calendar',
                'links': [{
                    'type': 'button',
                    'title': str(y),
                    'link': {
                        'url': url % (y, month),
                        'slot': 'internal',
                    },
                } for y in range(year-5, year+5)],
            },
            {
                'type': 'button',
                'title': str(year+1),
                'link': {
                    'url': url % (year+1, month),
                    'slot': 'internal',
                },
                "icon": "icon-control_fastforward"
            },
        ]
        return {'links': links}

    @beaninify('multiloader')
    def cancel(self):
        return []

    @beaninify('reload')
    def calendar_reload(self):
        return {
            'slot': ['calendar-content', 'calendar-notes'],
            'silent': True,
        }

    @beaninify('multiloader')
    def calendar_refresh(self):
        """
        Used to reload both the calendar content and slots at the same time.
        """

        year, month, day = self.get_year_month_day()
        init = [
            {
                'url': '/calendar/app/calendar_menu?year=%d&month=%d' %
                    (year, month),
                'slot': 'calendar-menu',
            },
            {
                'url': '/calendar/app/calendar_listing?year=%d&month=%d' %
                    (year, month),
                'slot': 'calendar-content',
            },
        ]
        return init

    @beaninify('listing')
    def calendar_notes(self):
        my_id = get_loggedin_user_id()
        year, month, day = self.get_year_month_day()
        schedule = self.get_schedule(year, month, day)
        data = []
        for time, note in schedule[(year, month, day)]:
            html = u''
            author_id = note['author'].get('id', '')
            recipient_id = note.get('operator', '')
            application_id = note.get('application', '')
            if my_id not in (author_id, recipient_id):
                continue
            author_name = u' '.join(x for x in [
                note['author'].get('first-name', ''),
                note['author'].get('last-name', ''),
            ] if x) or note['author'].get('id', '')
            if author_name and author_id != my_id:
                html += '<b class="author">%s</b><br/>' % cgi.escape(author_name)
            if application_id:
                html += 'Wniosek: <i class="application">%s</i><br/>' % cgi.escape(application_id)
                url = '/wnioski/formz/application_proxy?task-short-id=%s' % application_id
                style = 'calendar-note-row'
            else:
                url = None
                style = 'calendar-note-row-nolink'
            if recipient_id != my_id:
                if style == 'calendar-note-row':
                    style = 'calendar-note-row-own-link'
                else:
                    style = 'calendar-note-row-own'
                html += '<b class="recipient">%s</b><br/>' % cgi.escape(note.get('operator', ''))
            html += u'<div class="calendar-note-text">%s</div>' % cgi.escape(note['text'])
            data.append({
                'icon': {
                    'icon': 'icon-note_delete',
                    'url': '/calendar/app/delete_note?id=%s' % note['id'],
                    'slot': 'internal',
                },
                'time': '%02d:%02d' % time,
                'desc': html,
                '__params__': {
                    'uid': note['id'],
                    'style': style,
                },
            })
            if url:
                data[-1]['__params__']['link'] = {
                    'url': url,
                    'slot': 'internal',
                }
        if datetime.date(year=year, month=month, day=day)>=datetime.date.today():
            data.append({
                'icon': {
                    'icon': 'icon-add',
                    'slot': 'internal',
                    'url': '/calendar/app/add_note?year=%d&month=%d&day=%d' % (year, month, day),
                },
                'time': '',
                'desc': u'Dodaj przypomnienie',
                '__params__': {
                    'slot': 'internal',
                    'url': '/calendar/app/add_note?year=%d&month=%d&day=%d' % (year, month, day),
                }
            })
        result = {
            "autoexpand_column": "desc",
            "columns": [
                {
                    'id': 'time',
                    'title': u'Czas',
                    'width': '40',
#                    'renderer': 'text',
                    'fixed': 'true',
                },
                {
                    'id': 'desc',
                    'title': u'Opis',
                    'width': '0',
#                    'renderer': 'text',
                },
                {
                    'id': 'icon',
                    'title': '',
                    'width': '24',
                    'renderer': 'icon',
                    'fixed': 'true',
                },
            ],
            "groups": [
                {
                    'rowspan': 1,
                    'colspan': 3,
                    'title': '<b>%d %s %d</b>' % (day, MONTHS[month].title(), year),
                    'row': 0,
                    'column': 0,
                }
            ],
            "data": data,
        }
        return result

    @beaninify('listing')
    def calendar_listing(self):
        """
        Displays the actual table with calendar.
        """

        year, month, day = self.get_year_month_day()
        calendar = CALENDAR.monthdays2calendar(year, month)
        today = datetime.date.today()
        schedule = self.get_schedule(year, month)
        data = []
        for week_no, week in enumerate(calendar):
            row = {'__params__': {
                'uid': str(week_no),
                'style': 'calendar-month'}
            }
            for day, weekday in week:
                cell = {
                    'value': str(day or ''),
                }
                if day == today.day and month == today.month:
                    cell['value'] = u'<b>%s</b>' % cell['value']
                if weekday >= 5:
                    cell['value'] = (u'<span style="color:red">%s</span>' %
                                     cell['value'])
                if day>0:
                    cell['slot'] = 'calendar-notes'
                    cell['url'] = '/calendar/app/calendar_notes?year=%d&month=%d&day=%d' % (year, month, day)
                    cell['active'] = 'true'
                else:
                    cell['active'] = 'false'
                events = schedule[(year, month, day)]
                if events:
                    cell['value'] += u'<div class="calendar-icon icon-note">×%d</div>' % len(events)
                row[weekday] = cell
            data.append(row)
        for empty in range(week_no, 5):
            row = dict(zip(range(7), [{
                'value':'',
                'active': 'false',
            }]*7))
            row['__params__'] = {
                'uid': str(empty),
                'style': 'calendar-month',
            }
            data.append(row)
        result = {
            "columns": [
                {
                    'id': str(col),
                    'title': title,
                    'width': str(COLSIZE),
                    'renderer': 'text',
                    'resizable': 'false',
                    'fixed': 'true',
                } for col, title in enumerate(WEEKDAYS)],
            "groups": [
                {
                    'rowspan': 1,
                    'colspan': 7,
                    'title': '<b>%s %d</b>' % (MONTHS[month].title(), year),
                    'row': 0,
                    'column': 0,
                }
            ],
            "selection_model": "cell",
            "data": data,
        }
        return result

    @beaninify('multiloader')
    def really_delete_note(self):
        """
        Actually delete the note and refresh calendar.
        """

        note_id = request.params['id']
        data = iwm_call(notification_delete_inmapping, {'id': note_id}, None)
        year, month, day = self.get_year_month_day()
        return [
            {
                'url': '/calendar/app/calendar_notes?year=%d&month=%d&day=%s' %
                    (year, month, day),
                'slot': 'calendar-notes',
            },
            {
                'url': '/calendar/app/calendar_listing?year=%d&month=%d' %
                    (year, month),
                'slot': 'calendar-content',
            },
        ]

    @beaninify('dialog')
    def delete_note(self):
        """
        Display the note deletion confirmation dialog.
        """

        note_id = request.params['id']
        note = self.get_note(note_id)
        date = note['date']
        text = [u'Czy na pewno usunąć przypomnienie %s wysłane dnia %s, o godzinie %s ' % (
                note['id'],
                date.strftime('%Y-%m-%d'),
                date.strftime('%H:%M'))]
        author = u' '.join(x for x in [
            note['author'].get('first-name', ''),
            note['author'].get('last-name', ''),
        ] if x)
        if author:
            text.append('przez %s' % cgi.escape(author))
        if note.get('application'):
            text.append(u'w sprawie wniosku %s' % note['application'])
        if note.get('operator'):
            rec_data = get_user_profile(note['operator'])
            rec_name = u' '.join(x for x in [
                rec_data.get('first-name', ''),
                rec_data.get('last-name', ''),
            ] if x)
            text.append(u'do %s' % rec_name)
        text.append(u'o treści:')
        text.append(note['text'])
        return {
            'title': u'Usuwanie przypomnienia %s' % note_id,
            'text': u' '.join(cgi.escape(x) for x in text),
            'buttons': [
                {
                    'link': {
                        'url': ('/calendar/app/really_delete_note?id=%s&year=%d&month=%d&day=%d'
                                % (note_id, date.year, date.month, date.day)),
                        'slot': 'internal',
                    },
                    'label': 'Tak',
                },
                {
                    'link': {
                        'url': '/calendar/app/cancel',
                        'slot': 'internal',
                    },
                    'label': 'Nie',
                },
            ],
        }

    @beaninify('dialog')
    def calendar_error(self):
        """
        Display the error message.
        """

        return {
            'title': u'Błąd',
            'text': u'Dodanie powiadomienia nie powiodło się.',
            'buttons': [
                {
                    'link': {
                        'url': '/calendar/app/cancel',
                        'slot': 'internal',
                    },
                    'label': 'OK',
                },
            ],
        }


    @beaninify('composite')
    def really_add_note(self):
        """
        Do the actual addition of a note, and refresh the calendar.
        """

        params = dict(request.params)        
        date = datetime.datetime.strptime(' '.join([ params['date'], params['time'], ]), '%d-%m-%Y %H:%M')
        error_url = {
            'year': date.year,
            'month': date.month,
            'day': date.day,
            'time': params['time'],
            'text': params['text'],
            }
        if date.date() < datetime.date.today():
            error_url['date_error'] = 1
            return redirect('/calendar/app/add_note?%s' % urlencode(error_url))
        if date < datetime.datetime.now():
            error_url['time_error'] = 1
            return redirect('/calendar/app/add_note?%s' % urlencode(error_url))
        params['datetime'] = date
        operator = get_loggedin_user_data()
        params['author'] = operator['id']
        params['first-name'] = operator['first-name']
        params['last-name'] = operator['last-name']
        application = params.get('task-short-id', '')
        if application:
            summary_info = iwm_call(application_details_inmapping,
                                    {'task-short-id': application},
                                    application_details_get_outmapping)
            recipient = summary_info.get('operator-id', '')
            params['operator'] = recipient
        data = iwm_call(notification_add_inmapping, params, None)
        return [
            {
                'type': 'info',
                'result': {
                    'title': 'Przypomnienie',
                    'text': 'Dodano nowe przypomnienie',
                    'duration': 2500,
                },
            },
            {
                'type': 'reload',
                'result': {
                    'slot': 'calendar-content',
                    'silent': True,
                },
            },
            {
                'type': 'reload',
                'result': {
                    'slot': 'calendar-notes',
                    'silent': True,
                },
            },
            {
                'type': 'reload',
                'result': {
                    'slot': 'calendar-notes',
                    'silent': True,
                },
            },
            {
                'type': 'reload',
                'result': {
                    'slot': 'history-%s' % (application),
                    'silent': True,
                },
            },
        ]

    @beaninify('window')
    def add_note(self):
        """
        Display the new note form.
        """
        
        date_error = request.params.get('date_error') and u'Nie można wybrać przeszłej daty' or []
        time_error = request.params.get('time_error') and u'Nie mozna wybrać przeszłej godziny' or []
        time = request.params.get('time', (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime('%H:%M'))
        text = request.params.get('text', '')
        year, month, day = self.get_year_month_day()
        application = request.params.get('application', '')
        if application:
            recipient_field = {
                'widget': 'char',
                'name': 'task-short-id',
                'label': u'Wniosek',
                'value': application,
                'readonly': True,
            }
        else:
            operators = _get_consultants()
            recipient = get_loggedin_user_id()
            for operator in operators:
                if operator['value'] == recipient:
                    operator['selected'] = True
                else:
                    operator['selected'] = False
            recipient_field = {
                'widget': 'choice',
                'name': 'operator',
                'label': 'Adresat',
                'value': operators,
            }
        result = {
            'heading': u'Nowe przypomnienie',
            'width': 305,
            'height': 324,
            'slotname': 'calendar-add',
            'replace': True,
            'object': {
                'type': 'form',
                'result': {
                    'buttons': [
                        {
                            'label': u'Dodaj',
                            'link': {
                                'url': '/calendar/app/really_add_note',
                                'slot': 'internal',
                            },
                            'hide_window_onselect': True,
                        },
                        {
                            'label': u'Rezygnuj',
                            'link': {
                                'url': '/calendar/app/cancel',
                                'slot': 'internal',
                                'validation': False,
                            },
                            'hide_window_onselect': True,
                        }
                    ],
                    'formdefs': [
                        recipient_field,
                        {
                            'widget': 'datepicker',
                            'name': 'date',
                            'label': 'Data',
                            'value': '%d-%d-%d' % (day, month, year),
                            'error': date_error,
                        },
                        {
                            'widget': 'char',
                            'name': 'time',
                            'label': 'Godzina',
                            'value': time,
                            'validator': {
                                'type': 'regexp',
                                'value': r'[012]?\d:[012345]?\d',
                                'error_message': u'Błędna godzina',
                            },
                            'error': time_error
                        },
                        {
                            'widget': 'textarea',
                            'name': 'text',
                            'label': 'Treść powiadomienia',
                            'value': text,
                            'width': 255,
                            'height': 150,
                            'hidelabel': True,
                            'required': True,
                        },
                    ],
                },
            },
        }
        return result


    @beaninify('composite')
    def get_notes_alert(self):
        """
        Displays alert with current notes.
        """
        # sekunda dodana na wypadek dluzszej obslugi requestu (ryzyko podwojnego wyswietlenia okna)
        delta = datetime.timedelta(seconds = 1 + int(config.get('notification_interval', 300)))
        unregister = {"type" : "timer-unregister", "result" : {"name": "notifications_alert"}}

        try:
            from_dt = session['alert_from_dt']
        except KeyError:
            from_dt = datetime.datetime.now() - delta

        to_dt = datetime.datetime.now()

        params = {}
        params['from'] = from_dt.isoformat()
        params['to'] = to_dt.isoformat()
        params['recipient-type'] = 'OPERATOR'
        params['operator'] = get_loggedin_user_id()

        try:
            data = iwm_call(notification_list_inmapping, params,
                        notification_list_outmapping)
        except:
            return [unregister,
                    {
                        'type': 'window',
                        'result': {
                            'heading': u'Wystąpił błąd aplikacji',
                            'html': u'<pre>Wystąpił błąd podczas próby pobrania przypomnień.\n'
                            u'Pobieranie przypomnień zostało wyłączone.</pre>',
                            'width': 480,
                            'height': 320,
                            'scrollable': True,
                            'slotname': 'common-error-window',
                            'replace': True
                            }
                        }
                    ]

        output = []
        you = get_loggedin_user_id()
        for note in data:
            date = note['date']
            operator = note['operator']

            if from_dt < date <= to_dt and operator == you:
                note_json = self._get_alert_window()
                note_json['slotname'] = note_json['slotname'] % (note['id'])
                note_json['object']['result']['content'] = '<p><b>%s</b></p><p>%s</p>' % (
                                       date.strftime('%Y-%m-%d %H:%M:%S'), note['text'])

                output.append(
                              {
                               'type' : 'window',
                               'result': note_json
                               }
                              )

        session['alert_from_dt'] = to_dt
        session.save()
        return output

    def _get_alert_window(self):
        json = {
                'maximizable': False,
                'resizeable': False,
                'minimizable': False,
                'icon': 'icon-note',
                'slotname': 'calendar_note_alert_window_%s',
                'heading': u'Przypomnienie',
                'width': 266,
                'height': 322,
                'object': {
                    'type': 'html',
                    'result': {
                        'heading' : "",
                        'content' : ''
                       }
                },
                'sound' : {
                   'oncreate': 'notification'
                }
        }
        return json
