# Setup
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "common"))

# Internal
import argparse

# Local
import util

#-------------------------------------------------------------------------------

class Main():

    IGNORE_RECORD_TYPES = ["nsec3",
                           "nsec3param",
                           "rrsig",
                           "dnskey"]

    def __init__(self):
        # Arguments.
        self._domains_database_user = None
        self._domains_database_password = None
        self._domains_database_name = None
        self._zone_file_path_file = None
        self._part_size = None
        self._load_zone_file_pack_path = None

        # State.
        self._zone_file_tld = None
        self._zone_file_date_obj = None
        self._config = None
        self._zone_file_octet_total = None
        self._zone_file_octet_count = None
        self._last_sld = None
        self._part_number = 0

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
        argument_parser.add_argument("--domains_database_name",
                            type=str,
                            required=True,
                            help="Domains Database name. "
                                 "(Mandatory)")
        argument_parser.add_argument("--zone_file_path_file",
                                     type=str,
                                     required=True,
                                     help="Zone File path file. "
                                          "File name format: TLD#YYYY-MM-DD#full.txt "
                                          "Must exist. "
                                          "(Mandatory)")
        argument_parser.add_argument("--part_size",
                                     type=int,
                                     required=True,
                                     help="Part size. "
                                          "Must be 1 or more. "
                                          "(Mandatory)")
        argument_parser.add_argument("--load_zone_file_pack_path",
                                     type=str,
                                     required=True,
                                     help="Load Zone File pack path. "
                                          "Must exist and must be empty. "
                                          "(Mandatory)")

        namespace = argument_parser.parse_args()
        self._domains_database_user = namespace.domains_database_user
        self._domains_database_password = namespace.domains_database_password
        self._domains_database_name = namespace.domains_database_name
        self._zone_file_path_file = util.make_item_path_file_exist(namespace.zone_file_path_file)
        zone_file_file_name = os.path.basename(self._zone_file_path_file)
        zone_file_file_name_parts = zone_file_file_name.split("#")
        if len(zone_file_file_name_parts) != 3:
            msg = "--zone_file_path_file not in format: TLD#YYYY-MM-DD#full.txt\n"
            util.stop(msg)
        self._zone_file_tld = zone_file_file_name_parts[0]
        self._zone_file_date_obj = util.make_item_date_obj(zone_file_file_name_parts[1])
        self._part_size = util.make_int_ge(namespace.part_size, 1)
        self._load_zone_file_pack_path = util.make_item_path_exist_empty(namespace.load_zone_file_pack_path)
        self._zone_file_octet_total = os.path.getsize(self._zone_file_path_file)
        self._zone_file_octet_count = 0

    def generate_sld(self, zone_file_handle):
        self._part_number = self._part_number + 1
        sld_file_name = f"{self._part_number:06}.sld.txt"
        sld_path_file = os.path.join(self._load_zone_file_pack_path, sld_file_name)
        sld_handle = open(sld_path_file, "w")
        remain = True
        current_part_size = 0
        while (remain and (current_part_size < self._part_size)):
            # Line format:
            # <Host Label><tab><TTL><tab><Record Class><tab><Record Type><tab><Record Data>[<tab><Extra>...]
            # The Extra content is expected on the first and last lines.
            line = zone_file_handle.readline()
            self._zone_file_octet_count = self._zone_file_octet_count + len(line)
            if len(line) == 0:
                remain = False
            else:
                line_parts = line.split(sep="\t")
                if len(line_parts) < 5:
                    msg = f"Unexpected Line format: {line}\n"
                    util.stop(msg)
                host_label = line_parts[0]
                record_type = line_parts[3]
                if record_type not in Main.IGNORE_RECORD_TYPES:
                    host_label_parts = host_label.split(sep=".")
                    # Entries without an sld have form:
                    # "tld." ==> ['tld', ''] ==> length as 2
                    #
                    # Entries with a sld have form:
                    # "sld.tld." ==> ['sld', 'tld', ''] ==> length as 3
                    #
                    # Entries with a subdomain have form:
                    # "subdomain.tld.com." ==> ['subdomain', 'sld', 'tld', ''] ==> length as 4
                    # The sld always occurs without the subdomain, thus these
                    # may be ignored.
                    if len(host_label_parts) < 2:
                        msg = f"Unexpected Host Label format: {host_label}\n"
                        util.stop(msg)
                    if len(host_label_parts) == 3:
                        sld = host_label_parts[-3]
                        if sld != self._last_sld:
                            sld_handle.write(f"{sld}\n")
                            current_part_size = current_part_size + 1
                            self._last_sld = sld
        sld_handle.close()
        return remain

    def generate_config(self):
        self._config = util.Config(self._load_zone_file_pack_path)
        self._config.add_key_to_value("domains_database_user", self._domains_database_user)
        self._config.add_key_to_value("domains_database_password", self._domains_database_password)
        self._config.add_key_to_value("domains_database_name", self._domains_database_name)
        self._config.add_key_to_value("zone_file_tld", self._zone_file_tld)
        self._config.add_key_to_value("zone_file_date_str", self._zone_file_date_obj.isoformat())
        self._config.write()

    def generate_slds(self):
        zone_file_handle = open(self._zone_file_path_file, "r")
        # Discard header.
        zone_file_handle.readline()
        remain = True
        last_per = None
        while remain:
            remain = self.generate_sld(zone_file_handle)
            per = int((self._zone_file_octet_count / self._zone_file_octet_total) * 100)
            if per != last_per:
                util.info(f"{per}%\n")
                last_per = per
        util.info(f"{per}%\n")
        zone_file_handle.close()

    def start(self):
        self.process_arguments()
        self.generate_config()
        self.generate_slds()

if __name__ == '__main__':
    main = Main()
    main.start()
