## -*- coding: utf-8 -*-
import cgi
from calendar import Calendar
from collections import defaultdict
import datetime
from flask import Module, request, session
from grabarz import common
from grabarz.lib import beans

event_calendar = Module(__name__)

WEEKDAYS = [u'Pn', u'Wt', u'Śr', u'Cz', u'Pt', u'So', u'Nd']
FULL_WEEKDAYS = [
    u'Poniedziałek', u'Wtorek', u'Środa', u'Czwartek', 
    u'Piątek', u'Sobota', u'Niedziela'
]

MONTHS = [
    u'grudzień',
    u'styczeń', u'luty', u'marzec', u'kwiecień', u'maj',
    u'czerwiec', u'lipiec', u'sierpień', u'wrzesień', u'październik', 
    u'listopad', u'grudzień',
    u'styczeń'
]

MONTHS_VERBOSE = [
    u'stycznia', u'lutego', u'marca', u'kwietnia', u'maja',
    u'czerwca', u'lipca', u'sierpnia', u'września', u'października', 
    u'listopada', u'grudnia'
]


COLSIZE = 40
CALENDAR = Calendar()


def get_year_month_day():
    """ Get the year, month and day from the request parameters.
    Use today for the missing values.
    """
    today = datetime.date.today()
    
    year = session.get('calendar-year') or today.year
    month = session.get('calendar-month') or today.month
    day = session.get('calendar-day') or today.day
    return year, month, day

def save_year_month_day():
    if request.args.get('year'):
        session['calendar-year'] = int(request.args['year'])
    
    if request.args.get('month'):    
        session['calendar-month'] = int(request.args['month'])
    
    if request.args.get('day'):
        session['calendar-day'] = int(request.args['day'])

@event_calendar.route('/calendar/calendar-canvas')
@common.jsonify
def calendar_canvas():
    """ Displays the calendar canvas. """
    return  beans.Slots(                        
        beans.Slot(
            id = 'calendar-content',
            data = ['WEST', 286],
            link = beans.Link(
                url = '/calendar/calendar-content',
            ),            
        ),        
        beans.Slot(
            id = 'calendar-notes',
            data = ['CENTER'],
            link = beans.Link(
                url = '/calendar/calendar-notes',                  
            )            
        )            
    )

def calendar_menu():
    """ Displays the top menu.
    """
    year, month, day = get_year_month_day()
    url = '/calendar/calendar-refresh?year=%d&month=%d'
    return beans.Actions(
        links = [
            beans.Link(
                type = 'button',
                title = '<<<' + '&nbsp'*2,
                link = beans.Link(
                    url = url % (year, (month-2)%12+1),                              
                ),
                icon = 'icon-date_previous',                   
            ),
            
            beans.Link(
                type = 'menu',
                title = MONTHS[month].title() ,
                icon = 'icon-date',
                links = [
                    beans.Link(
                        type = 'button',
                        title = MONTHS[m],
                        link = beans.Link(
                            url = url % (year, m),
                        )                                            
                    ) for m in range(1, 13)                     
                ]                
            ),
    
            beans.Link(
              type = 'button',
              title =  '>>>',
              link = beans.Link( 
                    url = url % (year, month%12+1),        
              ),
              icon = 'icon-date_next',                   
            ),
            
            dict(type = 'fill'),
            dict(type = 'separator'),
                    
            dict(
                 type = 'menu',
                 title = `year`,
                 icon = 'icon-calendar',
                links = [
                    beans.Link(
                        type = 'button',
                        title = str(y),
                        link = beans.Link(
                            url = url % (y, month),
                        )                                                   
                    ) for y in range(year-5, year+5)                     
                ]             
            ),
        ]
    )
        
@event_calendar.route('/calendar/calendar-refresh')
@common.jsonify
def calendar_refresh():
    """ Used to reload both the calendar content and slots at the same time."""
    save_year_month_day()
    common.reload_slot(['calendar-content', 'calendar-notes'])
    return beans.Null()

@event_calendar.route('/calendar/calendar-notes')
@common.jsonify
def calendar_notes():
    save_year_month_day()
    year, month, day = get_year_month_day()
    weekday = FULL_WEEKDAYS[datetime.date(year, month, day).weekday()]
    month_verbose = MONTHS_VERBOSE[month-1]
    
     
    data = [
        dict(
             desc = 'Brak wydarzeń'             
        )            
    ]
            
    return beans.Listing(
        autoexpand_column = "desc",
        heading = '%s, %s %s %s' % (weekday,`day`,month_verbose,`year`),
        columns = [
            beans.Column(
                id = 'time',
                title = u'Czas',
                width = '40',
                fixed = 'true',
            ),
            beans.Column(
                id = 'desc',
                title = u'Opis',
                width = '0',
            ),
            beans.Column(
                id = 'icon',
                title = '',
                width = '24',
                renderer = 'icon',
                fixed = 'true',
            ),
        ],
        data = data,
    )


@event_calendar.route('/calendar/calendar-content')
@common.jsonify
def calendar_content():
    """
    Displays the actual table with calendar.
    """
    year, month, day = get_year_month_day()
    calendar = CALENDAR.monthdays2calendar(year, month)
    today = datetime.date.today()
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
                cell['url'] = '/calendar/calendar-notes?year=%d&month=%d&day=%d' % (year, month, day)
                cell['active'] = 'true'
            else:
                cell['active'] = 'false'
                
#            events = schedule[(year, month, day)]
#            if events:
#                cell['value'] += u'<div class="calendar-icon icon-note">×%d</div>' % len(events)
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
        
    return beans.Composite(
                           
        calendar_menu(),
        
        beans.Listing(
            columns = [
                dict(
                    id = str(col),
                    title = title,
                    width = str(COLSIZE),
                    renderer = 'text',
                    resizable = 'false',
                    fixed = 'true',
                ) for col, title in enumerate(WEEKDAYS)
            ],
            selection_model = "cell",
            data =  data,
        ),    
    )    