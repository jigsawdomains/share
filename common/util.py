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

def make_item_date_obj(item):
    item_date_obj = None
    try:
        item_date_obj = datetime.date.fromisoformat(item)
    except ValueError as e:
        msg = f"Not YYYY-MM-DD date format: {item}\n"
        stop(msg)
    return item_date_obj

#-------------------------------------------------------------------------------

def ensure_valid_from_upto(from_date_obj, upto_date_obj):
    if from_date_obj > upto_date_obj:
        msg = ""
        msg = msg + f"empty date range (as from is after upto) "
        msg = msg + f"from: {from_date_obj.isoformat()} "
        msg = msg + f"upto: {upto_date_obj.isoformat()}"
        msg = msg + "\n"
        stop(msg)

#-------------------------------------------------------------------------------

def make_database_connection(database_user, database_password, database_name):
    try:
        con = mariadb.connect(user=database_user,
                              password=database_password,
                              database=database_name)
    except mariadb.Error as e:
        msg=f"Error connecting to database: {e}\n"
        stop(msg)
    con.autocommit = False
    return con

#-------------------------------------------------------------------------------

def make_database_cursor(con):
    return con.cursor()

#-------------------------------------------------------------------------------

# Assumes:
# from1_date_obj <= upto1_date_obj
# from2_date_obj <= upto2_date_obj
def range_overlap(from1_date_obj, upto1_date_obj, from2_date_obj, upto2_date_obj):
    return ((from1_date_obj <= upto2_date_obj) and (upto1_date_obj >= from2_date_obj))
