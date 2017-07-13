#-*- coding: utf-8 -*-

import pprint
import calendar
from datetime import datetime, timedelta
import hashlib
import os
from pytz import timezone


class MyPrettyPrinter(pprint.PrettyPrinter):

    def format(self, _object, context, maxlevels, level):
        if isinstance(_object, unicode):
            return "'%s'" % _object.encode('utf8'), True, False
        elif isinstance(_object, str):
            _object = unicode(_object, 'utf8')
            return "'%s'" % _object.encode('utf8'), True, False
        return pprint.PrettyPrinter.format(self, _object,
                                           context, maxlevels, level)


def kprint(d):
    MyPrettyPrinter().pprint(d)
    return MyPrettyPrinter().pformat(d)


def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)


def yona_timeformat(dt, fmt=None):
    if fmt is None:
        fmt = '%Y-%m-%dT%H:%M:%SZ'

    if isinstance(dt, unicode) or isinstance(dt, str):
        dt = datetime.strptime(dt, fmt)

    return dt.replace(tzinfo=timezone('Asia/Seoul')).strftime('%Y-%m-%d %p %H:%M:%S %z')


def get_filehash(file_name):
    with open(file_name) as file_to_check:
        # read contents of the file
        data = file_to_check.read()
        # pipe contents of the file through
        md5_returned = hashlib.md5(data).hexdigest()
        return md5_returned


def get_mimeType(attachment):
    if 'content_type' in dir(attachment):
        return attachment['content_type']
    else:
        # TODO: map file mimetypes
        return '*/*'
