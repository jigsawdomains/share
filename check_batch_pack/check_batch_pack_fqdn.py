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
        self._domains_database_user = None
        self._domains_database_password = None
        self._inspect_date = None
        self._rdap = None
        self._fqdn_path_file = None
        self._report_path_file = None

        # State.
        self._domains_db = None
        ###self._rdap = None

    def process_arguments(self):
        argument_parser = argparse.ArgumentParser()
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
        argument_parser.add_argument("--inspect_date",
                                     type=str,
                                     required=True,
                                     help="Inspect date (YYYY-MM-DD). "
                                          "(Mandatory)")
        argument_parser.add_argument("--fqdn_path_file",
                                     type=str,
                                     required=True,
                                     help="FQDN path file. "
                                          "Must exist. "
                                          "(Mandatory)")
        argument_parser.add_argument("--report_path_file",
                                     type=str,
                                     required=True,
                                     help="Report path file. "
                                          "May exist. Parent path must exist. "
                                          "(Mandatory)")

        namespace = argument_parser.parse_args()
        self._domains_database_user = namespace.domains_database_user
        self._domains_database_password = namespace.domains_database_password
        self._inspect_date = util.make_item_date(namespace.inspect_date)
        self._fqdn_path_file = util.make_item_path_file_exist(namespace.fqdn_path_file)
        self._report_path_file = util.make_item_path_file_viable(namespace.report_path_file)
        self._domains_db = database.DomainsDB(self._domains_database_user,
                                              self._domains_database_password)

    def process_fqdn(self, report_handle, sld_label, tld_label):
        free = True
        sources = []
        result = self._domains_db.inspect_fqdn(sld_label, tld_label)
        if result is not None:
            (sources, start_none_date, until_none_date) = result
            if len(sources) == 0:
                msg = f"Unexpected zero sources result for FQDN: {fqdn}\n"
                util.stop(msg)
            if ((start_none_date is not None) and (until_none_date is not None)):
                if ((start_none_date <= self._inspect_date) and (self._inspect_date <= until_none_date)):
                    free = False

        if free:
            report_handle.write(f"{sld_label}.{tld_label}#{','.join(sources)}\n")

    def process_fqdns(self):
        fqdn_handle = open(self._fqdn_path_file, "r")
        report_handle = open(self._report_path_file, "w")
        for line in fqdn_handle:
            fqdn = line.strip()
            fqdn_parts = fqdn.split(sep=".")
            if len(fqdn_parts) == 2:
                sld_label = fqdn_parts[0]
                tld_label = fqdn_parts[1]
            else:
                msg = f"Unexpected FQDN: {fqdn}\n"
                util.stop(msg)
            self.process_fqdn(report_handle, sld_label, tld_label)
        report_handle.close()
        fqdn_handle.close()

    def start(self):
        self.process_arguments()
        self.process_fqdns()

if __name__ == '__main__':
    main = Main()
    main.start()
