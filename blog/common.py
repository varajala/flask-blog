"""
Common dataclasses.

Author: Valtteri Rajalainen
"""

import os
import datetime
import typing


__all__ = [
    'Timestamp',
    'Session',
    'Namespace',
    'path_relative_to_file',
    ]


def path_relative_to_file(filepath: str, path: str) -> str:
    return os.path.join(os.path.dirname(filepath), path)


class Timestamp:
    def __init__(self, delta: int = None):
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

    def __lt__(self, times) -> bool:
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

    def __gt__(self, times) -> bool:
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

    def __eq__(self, times) -> bool:
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


class Session:
    def __init__(self, session_id: int, csrf_token: bytes, expires: Timestamp, user_id: int):
        self.id = session_id
        self.csrf_token = csrf_token
        self.expires = expires
        self.user_id = user_id

    @classmethod
    def from_dict(cls, dict_: dict) -> typing.Optional[object]:
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
    def is_anonymous(self) -> bool:
        return self.user_id == 0

    @property
    def is_expired(self) -> bool:
        return Timestamp() > self.expires


class Namespace:

    def __init__(self, data: dict):
        object.__setattr__(self, 'data', data)
    
    def __getattribute__(self, attr):
        data = object.__getattribute__(self, 'data')
        if attr not in self:
            raise AttributeError(f'Namespace doesn\'t contain member "{attr}"')
        return data[attr]

    def __setattr__(self, attr: str, value: object):
        data = object.__getattribute__(self, 'data')
        data[attr] = value

    def __str__(self):
        return str(object.__getattribute__(self, 'data'))

    def __dir__(self):
        return dir(object.__getattribute__(self, 'data'))

    def __repr__(self):
        return str(self)

    def __contains__(self, key: str):
        data = object.__getattribute__(self, 'data')
        return key in data.keys()

