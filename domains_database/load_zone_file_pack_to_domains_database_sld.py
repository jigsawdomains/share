# Setup
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "common"))

# Internal
import argparse
import datetime

# External
import mariadb

# Local
import util

#-------------------------------------------------------------------------------

class Main():

    def __init__(self):
        # Arguments.
        self._zone_file_tld = None
        self._zone_file_date_obj = None
        self._domains_database_user = None
        self._domains_database_password = None
        self._domains_database_name = None
        self._sld_path_file = None

        # State.
        self._tld_id = None
        self._zone_file_date_str = None
        self._con = None
        self._cur = None

    def process_arguments(self):
        argument_parser = argparse.ArgumentParser()
        argument_parser.add_argument("--zone_file_tld",
                            type=str,
                            required=True,
                            help="Zone File TLD. "
                                 "Must exist. "
                                 "(Mandatory)")
        argument_parser.add_argument("--zone_file_date_str",
                                     type=str,
                                     required=True,
                                     help="Zone File date (YYYY-MM-DD). "
                                          "(Mandatory)")
        argument_parser.add_argument("--domains_database_user",
                            type=str,
                            required=True,
                            help="Domains Database user. "
                                 "(Mandatory)")
        argument_parser.add_argument("--domains_database_password",
                            type=str,
                            required=True,
                            help="Domains Database password. "
                                 "(Mandatory)")
        argument_parser.add_argument("--domains_database_name",
                            type=str,
                            required=True,
                            help="Domains Database name. "
                                 "(Mandatory)")
        argument_parser.add_argument("--sld_path_file",
                            type=str,
                            required=True,
                            help="SLD path file. "
                                 "Must exist. "
                                 "(Mandatory)")

        namespace = argument_parser.parse_args()
        self._zone_file_tld = namespace.zone_file_tld
        self._zone_file_date_obj = util.make_item_date_obj(namespace.zone_file_date_str)
        self._domains_database_user = namespace.domains_database_user
        self._domains_database_password = namespace.domains_database_password
        self._domains_database_name = namespace.domains_database_name
        self._sld_path_file = util.make_item_path_file_exist(namespace.sld_path_file)
        self._zone_file_date_str = self._zone_file_date_obj.isoformat()

    def open_database(self):
        self._con = util.make_database_connection(self._domains_database_user,
                                                  self._domains_database_password,
                                                  self._domains_database_name)
        self._cur = util.make_database_cursor(self._con)

    def process_tld(self):
        sql = f"SELECT tld.tld_id FROM tld WHERE tld.label='{self._zone_file_tld}';"
        self._cur.execute(sql)
        result_tuples = list(self._cur)
        if len(result_tuples) == 0:
            sql = f"INSERT INTO tld (tld.label) VALUES ('{self._zone_file_tld}');"
            self._cur.execute(sql)
            self._con.commit()
            self._tld_id = self._cur.lastrowid
        elif len(result_tuples) == 1:
            self._tld_id = result_tuples[0][0]
        else:
            msg = f"SQL: {sql} with unexpected result: {result_tuples}\n"
            util.stop(msg)

    def process_sld(self, label):
        sql = f"SELECT sld.sld_id FROM sld WHERE sld.label='{label}';"
        self._cur.execute(sql)
        result_tuples = list(self._cur)
        if len(result_tuples) == 0:
            sql = f"INSERT INTO sld (sld.label) VALUES ('{label}');"
            self._cur.execute(sql)
            self._con.commit()
            sld_id = self._cur.lastrowid
        elif len(result_tuples) == 1:
            sld_id = result_tuples[0][0]
        else:
            msg = f"SQL: {sql} with unexpected result: {result_tuples}\n"
            util.stop(msg)

        sql = f"SELECT known, start, until FROM fqdn WHERE fqdn.tld_id='{self._tld_id}' AND fqdn.sld_id='{sld_id}';"
        self._cur.execute(sql)
        result_tuples = list(self._cur)
        if len(result_tuples) == 0:
            sql = f"INSERT INTO fqdn (fqdn.tld_id, fqdn.sld_id, fqdn.known, fqdn.start, fqdn.until) VALUES ('{self._tld_id}', '{sld_id}', '{True:d}', '{self._zone_file_date_str}', '{self._zone_file_date_str}');"
            self._cur.execute(sql)
            self._con.commit()
            sld_id = self._cur.lastrowid
        elif len(result_tuples) == 1:
            known = result_tuples[0][0]
            start_date_obj = result_tuples[0][1]
            until_date_obj = result_tuples[0][2]
            update = False
            if not known:
                update = True
            if self._zone_file_date_obj < start_date_obj:
                adopt_start_date_str = self._zone_file_date_str
                update = True
            else:
                adopt_start_date_str = start_date_obj.isoformat()

            if self._zone_file_date_obj > until_date_obj:
                adopt_until_date_str = self._zone_file_date_str
                update = True
            else:
                adopt_until_date_str = until_date_obj.isoformat()

            if update:
                sql = f"UPDATE fqdn SET fqdn.known='{True:d}', fqdn.start='{adopt_start_date_str}', fqdn.until='{adopt_until_date_str}' WHERE fqdn.tld_id='{self._tld_id}' AND fqdn.sld_id='{sld_id}';"
                self._cur.execute(sql)
                self._con.commit()
        else:
            msg = f"SQL: {sql} with unexpected result: {result_tuples}\n"
            util.stop(msg)

    def process_slds(self):
        handle = open(self._sld_path_file, "r")
        for line in handle:
            label = line.strip()
            self.process_sld(label)
        handle.close()

    def start(self):
        self.process_arguments()
        self.open_database()
        self.process_tld()
        self.process_slds()

if __name__ == '__main__':
    main = Main()
    main.start()
