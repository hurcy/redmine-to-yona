#-*- coding: utf-8 -*-

import pprint
import datetime
import hashlib
import os

epoch = datetime.datetime.utcfromtimestamp(0)


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


def unix_time_millis(dt):
    return int((dt - epoch).total_seconds() * 1000)


def get_filehash(file_name):
    with open(file_name) as file_to_check:
        # read contents of the file
        data = file_to_check.read()
        # pipe contents of the file through
        md5_returned = hashlib.md5(data).hexdigest()
        return md5_returned
