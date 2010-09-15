## -*- coding: utf-8 -*-
from decorator import decorator
from copy import deepcopy
from flask import request

def wrap(type, result):
    return dict(
        type=type,
        result=result,
    )

def wrapped(type, *args, **kwargs):
    """ Dekorator, który zawija slownik pod dany klucz
    
    @param type: str
    @param result: dict
    """
    def call(func, *args, **kwargs):
        return wrap(type, func(*args, **kwargs))
    return decorator(call)


class Conditional(object):
    """ Przechowuje obiekt + warunek konieczny, aby obiekt był zwrócony. """
    def __init__(self, value, __condition__=None):
        self.value = value

        if  __condition__ is None:
            self.__condition__ = bool(value)
        else:
            self.__condition__ = __condition__

    def isValid(self):
        if isinstance(self.__condition__, bool):
            return self.__condition__

        if callable(self.__condition__):
            return bool(self.__condition__(self.value))

class Bean(dict):
    """Abstrakcyjna klasa, która stanowi rozszerzenie słownika.
    Klasa ma na cełu ułatwić generowanie słowników, które budują jsonowe.    
    """
    def __init__(self, *args, **kwargs):
        #: Szukanie atrybutów, które zostały nadane w klasach pochodnych
        dict_attrs = dir(dict)
        data = dict([(k, getattr(self, k))
                     for k in dir(self) if not k.startswith('__') and 
                                           k not in dict_attrs])

        #: Filtrowanie atrybutów warunkowych
        for k, v in kwargs.items():
            if not isinstance(v, Conditional):
                continue
            if not v.isValid():
                del kwargs[k]
            else:
                kwargs[k] = v.value

        #: Aktualizacja danych
        data.update(kwargs)
        self.update(data)
        
        #: Zawinięcie wyniku pod klucz >>type<<
        if getattr(self, '__type__', None):
            result = deepcopy(dict(
                type=self.__type__, result=self
            ))

            for k in self.keys():
                del self[k]
            self.update(result)


class Listing(Bean):
    __type__ = 'listing'
    heading = None
    data = []
    columns = []


class Column(Bean):
    pass


class Row(Bean):
    pass

class Config(Bean):
    __type__ = 'config'
    
class TimerRegister(Bean):
    __type__ = 'timer-register'
    
class Desktop(Bean):
    __type__ = 'desktop'    

class WindowChange(Bean):
    __type__ = 'window_change'  

class Menu(Bean):
    __type__ = 'menu'
    
class Actions(Bean):
    __type__ = 'actions'  
    
    
class Reload(Bean):
    __type__ = 'reload'
    silent = False
    

class Fieldset(Bean):
    type = "fieldset"
    fieldsetheading = None
    fielddefs = []


class Link(Bean):
    url = ''
    slot = ""


@wrapped('composite')
def Composite(*args):
    result = []
    for a in args:
        if '__conditional__' in a and not a['__conditional__'].isValid():
            continue
        result.append(a)
    return result

@wrapped('slots')
def Slots(*args):
    return [a for a in args]


class MenuItem(Bean):
    pass

def MenuItems(*args):
    return dict(
        menu_items = [a for a in args]
    )



@wrapped('multiloader')
def MultiLoader(*args):
    result = []
    for a in args:
        if '__conditional__' in a and not a['__conditional__'].isValid():
            continue
        result.append(a)
    return result

class Button(Bean):
    widget = 'button'
    link = Link()

class Validator(Bean):
    valid = True
    error = ""


class Form(Bean):
    __type__ = 'form'
    heading = None
    buttons = []
    formdefs = []


class MultiField(Bean):
    type = 'multifield'
    fielddefs = []
    label = ""


class Window(Bean):
    __type__ = 'window'
    replace = True
    heading = None
    width = 500
    height = 300
    slotname = "window"


class HTML(Bean):
    __type__ = "html"
    content = ""
    heading = None
    scroll = "NONE"


class WindowCloser(Bean):
    __type__ = "window_change"
    slotname = ""
    action = 'close'


class Infobox(Bean):
    __type__ = "info"
    text = ""
    title = "Info"
    duration = 2500


class Dialog(Bean):
    __type__ = 'dialog'
    title = 'Potwierdzenie'
    text = 'na pewno?'
    buttons = []


class Field(Bean):
    """
    Zwraca słownik definiujący pole
    """
    def __init__(self, *args, **kwargs):
        super(Field, self).__init__(*args, **kwargs)

        self.update(dict(
            required=True,
        ))

        if kwargs.get('__default__'):
            self.update(dict(
                value=kwargs['__default__']
            ))


        #nadpisywanie wartości z POST        
        name = self.get('name')
        post_val = request.form.to_dict().get(name)
        old_value = self.get('value')

        if post_val:
            if isinstance(old_value, (str, unicode)):
                self.update(dict(
                    value=post_val,
                ))
            elif isinstance(old_value, (tuple, list)):
                for v in old_value:
                    v['selected'] = v['value'] == post_val



class DateField(Field):
    widget = 'datepicker'
    displayformat = 'dd-MM-yyyy'
    dateformat = 'dd-MM-yyyy'
    __sample_val__ = '19-08-2010'
    label = ''
    value = ''
    

class ChoiceField(Field):
    widget = 'choice'
    name = 'choice_field'
    label = 'Pole wyboru'
    value = []
    forceselection = True


class PasswordField(Field):
    widget = 'password'
    name = 'password'
    label = 'hasło'
    value = ''


class CheckBoxField(Field):
    widget = 'checkbox'
    name = 'checbkox'
    label = 'checbkox'
    value = 'true'


class TextAreaField(Field):
    widget = 'textarea'
    name = 'textarea'
    label = 'textarea'
    value = ''


class CharField(Field):
    widget = 'char'
    name = 'CharField'
    label = 'CharField'
    value = ''