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

def make_item_date_obj(item):
    item_date_obj = None
    try:
        item_date_obj = datetime.date.fromisoformat(item)
    except ValueError as e:
        msg = f"Not YYYY-MM-DD date format: {item}\n"
        stop(msg)
    return item_date_obj

#-------------------------------------------------------------------------------

def make_start_until_none_date_obj_tuple(none_date_objs):
    date_objs = []
    for none_date_obj in none_date_objs:
        if none_date_obj is not None:
            date_objs.append(none_date_obj)
    date_objs = sorted(date_objs)
    if len(date_objs) == 0:
        result = (None, None)
    else:
        result = (date_objs[0], date_objs[-1])
    return result

#-------------------------------------------------------------------------------

class Config():

    FILE_NAME = f"config.txt"

    def __init__(self, config_path):
        self._config_path = config_path
        self._config_path_file = os.path.join(self._config_path, Config.FILE_NAME)
        self._key_to_value = {}

    def add_key_to_value(self, key, value):
        self._key_to_value[key] = value

    def make_value(self, key):
        if key not in self._key_to_value.keys():
            msg = f"Provided key not known: {str(key)}\n"
            stop(msg)
        return self._key_to_value[key]

    def read(self):
        self._key_to_value = {}
        handle = open(self._config_path_file, "r")
        lines = []
        for line in handle:
            lines.append(line.strip())
        handle.close()
        for line in lines:
            parts = line.split(":")
            if len(parts) == 2:
                key = parts[0]
                value = parts[1]
                self._key_to_value[key] = value
            else:
                msg = f"Unexpected format: {line}\n"
                stop(msg)

    def write(self):
        handle = open(self._config_path_file, "w")
        for key in sorted(self._key_to_value.keys()):
            value = self._key_to_value[key]
            handle.write(f"{key}:{value}\n")
        handle.close()
