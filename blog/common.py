import datetime
from typing import Union


__all__ = ['Timestamp', 'Session', 'Namespace']


class Session:
    def __init__(self, session_id, csrf_token, expires, user_id):
        self.id = session_id
        self.csrf_token = csrf_token
        self.expires = expires
        self.user_id = user_id

    @classmethod
    def from_dict(cls, dict_) -> Union[object, None]:
        if not dict_:
            return None
        
        session = Session(
            dict_['session_id'],
            dict_['csrf_token'],
            Timestamp.from_str(dict_['expires']),
            dict_['user_id'],
        )
        return session

    @property
    def is_anonymous(self):
        return self.user_id == 0

    @property
    def is_expired(self):
        return Timestamp() > self.expires


class Namespace:

    def __init__(self, data):
        object.__setattr__(self, 'data', data)
    
    def __getattribute__(self, attr):
        data = object.__getattribute__(self, 'data')
        if attr not in self:
            raise AttributeError(f'Namespace doesn\'t contain member "{attr}"')
        return data[attr]

    def __setattr__(self, attr, value):
        data = object.__getattribute__(self, 'data')
        data[attr] = value

    def __str__(self):
        return str(object.__getattribute__(self, 'data'))

    def __dir__(self):
        return dir(object.__getattribute__(self, 'data'))

    def __repr__(self):
        return str(self)

    def __contains__(self, item):
        data = object.__getattribute__(self, 'data')
        return item in data.keys()


class Timestamp:
    def __init__(self, delta=None):
        date = datetime.datetime.now()
        if delta:
            date = date + datetime.timedelta(hours=delta)
        
        self.hours = date.hour
        self.minutes = date.minute
        self.day = date.day
        self.month = date.month
        self.year = date.year

    @classmethod
    def from_str(cls, string):
        time, date = string.split(' ')
        hours, minutes = time.split(':')
        day, month, year = date.split('.')
        ts = Timestamp()
        ts.hours = int(hours)
        ts.minutes = int(minutes)
        ts.day = int(day)
        ts.month = int(month)
        ts.year = int(year)
        return ts

    def __lt__(self, times):
        if times.year < self.year:
            return False
        if times.year > self.year:
            return True
        
        if times.month < self.month:
            return False
        if times.month > self.month:
            return True

        if times.day < self.day:
            return False
        if times.day > self.day:
            return True
        
        if times.hours < self.hours:
            return False
        if times.hours > self.hours:
            return True
        
        if times.minutes < self.minutes:
            return False
        if times.minutes > self.minutes:
            return True
        return False

    def __gt__(self, times):
        if times.year > self.year:
            return False
        if times.year < self.year:
            return True
        
        if times.month > self.month:
            return False
        if times.month < self.month:
            return True

        if times.day > self.day:
            return False
        if times.day < self.day:
            return True
        
        if times.hours > self.hours:
            return False
        if times.hours < self.hours:
            return True
        
        if times.minutes > self.minutes:
            return False
        if times.minutes < self.minutes:
            return True
        return False

    def __eq__(self, times):
        comparisons = [
            self.year == times.year,
            self.month == times.month,
            self.day == times.day,
            self.hours == times.hours,
            self.minutes == times.minutes,
        ]
        return all(comparisons)

    def __str__(self):
        parts = [
            str(self.hours).zfill(2),
            ':',
            str(self.minutes).zfill(2),
            ' ',
            str(self.day).zfill(2),
            '.',
            str(self.month).zfill(2),
            '.',
            str(self.year).zfill(4),
        ]
        return ''.join(parts)

    def __repr__(self):
        return str(self)