# Setup
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "common"))

# Internal
import argparse

# Local
import util
import database

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
        self._domains_db = None

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
        self._domains_db = database.DomainsDB(self._domains_database_user,
                                              self._domains_database_password,
                                              self._domains_database_name)

    def process_slds(self):
        handle = open(self._sld_path_file, "r")
        for line in handle:
            zone_file_sld = line.strip()
            req_source = database.DomainsDB.ZONE_FILE
            req_sld_label = zone_file_sld 
            req_tld_label = self._zone_file_tld 
            req_start_none_date_obj = self._zone_file_date_obj
            req_until_none_date_obj = self._zone_file_date_obj
            self._domains_db.update_fqdn(req_source,
                                         req_sld_label,
                                         req_tld_label,
                                         req_start_none_date_obj,
                                         req_until_none_date_obj)
        handle.close()

    def start(self):
        self.process_arguments()
        self.process_slds()

if __name__ == '__main__':
    main = Main()
    main.start()
