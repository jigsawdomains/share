# Setup
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "common"))

# Internal
import argparse
import datetime
import json
import re
import mariadb
import subprocess
import sys

# Local
import task_support
import util

#-------------------------------------------------------------------------------

class Main():

    def __init__(self):
        # Arguments.
        self._database_user = None
        self._database_password = None
        self._database_name = None
        self._tld = None 
        self._slds_path_file = None 
        self._window_from_date_obj = None
        self._window_upto_date_obj = None
        self._pack_path = None

        # State.
        self._con = None
        self._cur = None
        self._result_path_file = None
        self._result_handle = None

    def stop(self, msg):
        sys.stdout.write(msg)
        sys.exit(1)

    def process_arguments(self):
        argument_parser = argparse.ArgumentParser()

        argument_parser.add_argument("--database_user",
                            type=str,
                            required=True,
                            help="Database user. "
                                 "(Mandatory)")
        argument_parser.add_argument("--database_password",
                            type=str,
                            required=True,
                            help="Database password. "
                                 "(Mandatory)")
        argument_parser.add_argument("--database_name",
                            type=str,
                            required=True,
                            help="Database name. "
                                 "(Mandatory)")
        argument_parser.add_argument("--tld",
                            type=str,
                            required=True,
                            help="TLD. "
                                 "(Mandatory)")
        argument_parser.add_argument("--slds_path_file",
                            type=str,
                            required=True,
                            help="SLDs. "
                                 "Must exist. "
                                 "(Mandatory)")
        argument_parser.add_argument("--window_from_date_str",
                            type=str,
                            required=True,
                            help="Window from date (YYYY-MM-DD). "
                                 "(Mandatory)")
        argument_parser.add_argument("--window_upto_date_str",
                            type=str,
                            required=True,
                            help="Window upto date (YYYY-MM-DD). "
                                 "(Mandatory)")
        argument_parser.add_argument("--pack_path",
                                     type=str,
                                     required=True,
                                     help="Report pack path. "
                                          "Must exist and must be empty. "
                                          "(Mandatory)")
        namespace = argument_parser.parse_args()
        self._database_user = namespace.database_user
        self._database_password = namespace.database_password
        self._database_name = namespace.database_name
        self._tld = namespace.tld
        self._slds_path_file = util.make_item_path_file_exist(namespace.slds_path_file)
        self._window_from_date_obj = util.make_item_date_obj(namespace.window_from_date_str)
        self._window_upto_date_obj = util.make_item_date_obj(namespace.window_upto_date_str)
        util.ensure_valid_from_upto(self._window_from_date_obj, self._window_upto_date_obj)
        self._pack_path = util.make_item_path_exist_empty(namespace.pack_path)
        result_file_name = "result.txt"
        self._result_path_file = os.path.join(self._pack_path, result_file_name)

    def open_database(self):
        self._con = util.make_database_connection(self._database_user,
                                                  self._database_password,
                                                  self._database_name)
        self._cur = util.make_database_cursor(self._con)

    def open_result(self):
        self._result_handle = open(self._result_path_file, "a")
        self._result_handle.write(f"Start: {datetime.datetime.now().isoformat()}\n")
        self._result_handle.flush()

    def process_tld(self):
        sql = f"SELECT tld.tld_id FROM tld WHERE tld.label='{self._tld}';"
        self._cur.execute(sql)
        result_tuples = list(self._cur)
        if len(result_tuples) == 1:
            self._tld_id = result_tuples[0][0]
        else:
            msg = f"TLD not known to database: {self._tld}\n"
            self.stop(msg)

    def process_sld(self, sld):
        sql = f"SELECT fqdn.from,fqdn.upto FROM fqdn INNER JOIN sld ON fqdn.sld_id = sld.sld_id where fqdn.tld_id={self._tld_id} and sld.label='{sld}';";
        self._cur.execute(sql)
        result_tuples = list(self._cur)
        if len(result_tuples) == 1:
            from_date_obj = result_tuples[0][0]
            upto_date_obj = result_tuples[0][1]
            if util.range_overlap(from_date_obj,
                             upto_date_obj,
                             self._window_from_date_obj,
                             self._window_upto_date_obj):
                self._result_handle.write(f"FOUND: {sld}.{self._tld} (from: {from_date_obj.isoformat()} upto: {upto_date_obj.isoformat()})\n")
            else:
                self._result_handle.write(f"ABSENT: {sld}.{self._tld} (from: {from_date_obj.isoformat()} upto: {upto_date_obj.isoformat()})\n")
        if len(result_tuples) == 0:
            self._result_handle.write(f"ABSENT: {sld}.{self._tld} (from: Absent upto: Absent)\n")


    def process_slds(self):
        handle = open(self._slds_path_file, "r")
        remain = True
        while remain:
            line = handle.readline()
            sld = line.strip()
            if len(sld) == 0:
                remain = False
            else:
                self.process_sld(sld)
        handle.close()


    def start(self):
        self.process_arguments()
        self.open_database()
        self.open_result()
        self.process_tld()
        self.process_slds()

if __name__ == '__main__':
    main = Main()
    main.start()





