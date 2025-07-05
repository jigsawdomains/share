# Internal
import os
import sys
import datetime

# External
import mariadb

#-------------------------------------------------------------------------------

def stop(msg):
    sys.stdout.write(msg)
    sys.stdout.flush()
    sys.exit(1)

#-------------------------------------------------------------------------------

def info(msg):
    sys.stdout.write(msg)
    sys.stdout.flush()

#-------------------------------------------------------------------------------

def make_item_path_exist(item):
    item_path = os.path.abspath(item)
    if not os.path.isdir(item_path):
        msg = f"Not a path: {item_path}\n"
        stop(msg)
    return item_path

#-------------------------------------------------------------------------------

def make_item_path_exist_empty(item):
    item_path = os.path.abspath(item)
    if not os.path.isdir(item_path):
        msg = f"Not a path: {item_path}\n"
        stop(msg)
    if not os.listdir(item_path) == []:
        msg = f"Not empty: {item_path}\n"
        stop(msg)
    return item_path

#-------------------------------------------------------------------------------

def make_item_path_file_viable(item):
    item_path_file = os.path.abspath(item)
    item_path = os.path.basename(item_path_file)
    if not os.path.isdir(item_path):
        msg = f"Not a path: {item_path}\n"
        stop(msg)
    return item_path_file

#-------------------------------------------------------------------------------

def make_item_path_file_exist(item):
    item_path_file = os.path.abspath(item)
    if not os.path.isfile(item_path_file):
        msg = f"Not a path file: {item_path_file}\n"
        stop(msg)
    return item_path_file

#-------------------------------------------------------------------------------

def make_item_path_file_absent(item):
    item_path_file = os.path.abspath(item)
    if os.path.exists(item_path_file):
        msg = f"Already exists: {item_path_file}\n"
        stop(msg)
    return item_path_file

#-------------------------------------------------------------------------------

def make_int_ge(item, limit):
    if item < limit:
        msg = f"Value: {item} must be greater than or equal to: {limit}\n"
        stop(msg)
    return item

#-------------------------------------------------------------------------------

def make_item_bool(item):
    if item == str(True):
        item_bool = True
    elif item == str(False):
        item_bool = False
    else:
        msg = f"Not a bool: {item}\n"
        stop(msg)
    return item_bool

#-------------------------------------------------------------------------------

def make_item_date(item):
    item_date = None
    try:
        item_date = datetime.date.fromisoformat(item)
    except ValueError as e:
        msg = f"Not YYYY-MM-DD date format: {item}\n"
        stop(msg)
    return item_date

#-------------------------------------------------------------------------------

def make_item_datetime(item):
    item_datetime = None
    try:
        item_datetime = datetime.datetime.fromisoformat(item)
    except ValueError as e:
        msg = f"Not recognised date time format: {item}\n"
        stop(msg)
    return item_datetime

#-------------------------------------------------------------------------------

def make_start_until_none_date_tuple(item_none_dates):
    dates = []
    for item_none_date in item_none_dates:
        if item_none_date is not None:
            dates.append(item_none_date)
    dates = sorted(dates)
    if len(dates) == 0:
        result = (None, None)
    else:
        result = (dates[0], dates[-1])
    return result

#-------------------------------------------------------------------------------

class Config():

    FILE_NAME = "config.txt"

    VALUE_TYPE_STR = "TYPE_STR"
    VALUE_TYPE_BOOL = "TYPE_BOOL"
    VALUE_TYPE_DATE = "TYPE_DATE"

    def __init__(self, item_path):
        self._item_path = item_path
        self._config_path_file = os.path.join(self._item_path, Config.FILE_NAME)
        self._key_to_value_type = {}
        self._key_to_value = {}

    def add_entry_str(self, key, value):
        self._key_to_value_type[key] = Config.VALUE_TYPE_STR
        self._key_to_value[key] = value

    def add_entry_bool(self, key, value):
        self._key_to_value_type[key] = Config.VALUE_TYPE_BOOL
        self._key_to_value[key] = value

    def add_entry_date(self, key, value):
        self._key_to_value_type[key] = Config.VALUE_TYPE_DATE
        self._key_to_value[key] = value

    def get_value(self, key):
        if key not in self._key_to_value.keys():
            msg = f"Provided key not known: {str(key)}\n"
            stop(msg)
        return self._key_to_value[key]

    def read(self):
        self._key_to_value_type = {}
        self._key_to_value = {}
        handle = open(self._config_path_file, "r")
        lines = []
        for line in handle:
            lines.append(line.strip())
        handle.close()
        for line in lines:
            valid = False
            parts = line.split(":")
            if len(parts) == 3:
                key = parts[0]
                value_type = parts[1]
                value_str = parts[2]
                value = None
                if value_type == Config.VALUE_TYPE_STR:
                    value = value_str 
                elif value_type == Config.VALUE_TYPE_BOOL:
                    value = make_item_bool(value_str)
                elif value_type == Config.VALUE_TYPE_DATE:
                    value = make_item_date(value_str)
                if value is not None:
                    self._key_to_value_type = value_type
                    self._key_to_value[key] = value
                    valid = True
            if not valid:
                msg = f"Unexpected entry as line: {line}\n"
                stop(msg)

    def write(self):
        handle = open(self._config_path_file, "w")
        for key in sorted(self._key_to_value.keys()):
            valid = False
            value_type = self._key_to_value_type[key]
            value = self._key_to_value[key]
            value_str = None
            if value_type == Config.VALUE_TYPE_STR:
                if type(value) == str:
                    value_str = value
            elif value_type == Config.VALUE_TYPE_BOOL:
                if type(value) == bool:
                    value_str = str(value)
            elif value_type == Config.VALUE_TYPE_DATE:
                if type(value) == datetime.date:
                    value_str = value.isoformat()
            if value_str is not None:
                handle.write(f"{key}:{value_type}:{value_str}\n")
                valid = True
            if not valid:
                msg = f"Unexpected entry as key: {str(key)} value_type: {str(value_type)} value:{str(value)}\n"
                stop(msg)
        handle.close()

#-------------------------------------------------------------------------------
