# Setup
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "common"))

# Internal
import argparse

# Local
import task_support
import util

#-------------------------------------------------------------------------------

class TaskFqdn(task_support.Task):

    def __init__(self, 
                 domains_database_user,
                 domains_database_password,
                 domains_database_name,
                 batch_pack_path,
                 fqdn_file_name):
        self._domains_database_user = domains_database_user
        self._domains_database_password = domains_database_password
        self._domains_database_name = domains_database_name
        self._sld_path_file = os.path.join(batch_pack_path, fqdn_file_name)
        self._hit_path_file = os.path.join(batch_pack_path, fqdn_file_name.replace(".fqdn.txt", ".hit.txt"))
        self._gap_path_file = os.path.join(batch_pack_path, fqdn_file_name.replace(".fqdn.txt", ".gap.txt"))
        log_path_file = os.path.join(batch_pack_path, fqdn_file_name.replace(".fqdn.txt", ".log.txt"))
        did_path_file = os.path.join(batch_pack_path, fqdn_file_name.replace(".fqdn.txt", ".did.txt"))
        task_support.Task.__init__(self,
                                   log_path_file=log_path_file,
                                   did_path_file=did_path_file) 

    def make_command(self):
        pack_to_domains_database_path_file = os.path.abspath(__file__)
        pack_to_domains_database_path = os.path.dirname(pack_to_domains_database_path_file)
        pack_to_domains_database_sld_path_file = os.path.join(pack_to_domains_database_path, "check_batch_pack_fqdn.py")
        command = [sys.executable,
                   pack_to_domains_database_sld_path_file,
                   "--zone_file_tld", self._zone_file_tld,
                   "--zone_file_date_str", self._zone_file_date_obj.isoformat(),
                   "--domains_database_user", self._domains_database_user,
                   "--domains_database_password", self._domains_database_password, 
                   "--domains_database_name", self._domains_database_name,
                   "--sld_path_file", self._sld_path_file]
        return command

#-------------------------------------------------------------------------------

class Main():

    def __init__(self):
        # Arguments.
        self._batch_pack_path = None
        self._domains_database_user = None
        self._domains_database_password = None
        self._domains_database_name = None
        self._core_total = None

        # State.
        self._zone_file_tld = None
        self._zone_file_date_obj = None

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
        argument_parser.add_argument("--core_total",
                            type=int,
                            required=True,
                            help="Number of cores. "
                                 "Must be 1 or more. "
                                 "(Mandatory)")
        argument_parser.add_argument("--batch_pack_path",
                                     type=str,
                                     required=True,
                                     help="Batch pack path. "
                                          "Must exist. "
                                          "(Mandatory)")


        argument_parser.add_argument("--batch_pack_path",
                                     type=str,
                                     required=True,
                                     help="Batch pack path. "
                                          "Must exist. "
                                          "(Mandatory)")





        namespace = argument_parser.parse_args()
        self._domains_database_user = namespace.domains_database_user
        self._domains_database_password = namespace.domains_database_password
        self._domains_database_name = namespace.domains_database_name
        self._core_total = util.make_int_ge(namespace.core_total, 1)
        self._batch_pack_path = util.make_item_path_exist(namespace.batch_pack_path)

    def process_tld(self):
        tld_file_name = f"tld.txt"
        tld_path_file = os.path.join(self._batch_pack_path, tld_file_name)
        tld_handle = open(tld_path_file, "r")
        lines = []
        for line in tld_handle:
            lines.append(line.strip())
        tld_handle.close()
        for line in lines:
            key = "zone_file_tld:"
            if line.startswith(key):
                self._zone_file_tld = line.replace(key,"")
            key = "zone_file_date_str:"
            if line.startswith(key):
                self._zone_file_date_obj = util.make_item_date_obj(line.replace(key,""))
        if self._zone_file_tld is None:
            msg = "Absent: zone_file_tld\n"
            util.stop(msg)
        if self._zone_file_date_obj is None:
            msg = "Absent: zone_file_date_str\n"
            util.stop(msg)

    def process_fqdns(self):
        task_manager = task_support.TaskManager("FQDNS", self._core_total, idle_freq_seconds=5, track_freq_seconds=30)
        file_names = os.listdir(self._batch_pack_path)
        for file_name in sorted(file_names):
            if file_name.endswith(".fqdn.txt"):
                fqdn_path_file = os.path.join(self._batch_pack_path, file_name)
                task_fqdn = TaskFqdn(self._domains_database_user,
                                     self._domains_database_password,
                                     self._domains_database_name,
                                     self._batch_pack_path,
                                     file_name)
                task_manager.add_task(task_fqdn)
        task_manager.execute()

    def start(self):
        self.process_arguments()
        self.process_fqdns()

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    main = Main()
    main.start()
