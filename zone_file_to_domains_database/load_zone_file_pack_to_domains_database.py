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

class TaskSld(task_support.Task):

    def __init__(self, 
                 zone_file_tld,
                 zone_file_date_obj,
                 domains_database_user,
                 domains_database_password,
                 domains_database_name,
                 load_zone_file_pack_path,
                 sld_file_name):
        self._zone_file_tld = zone_file_tld 
        self._zone_file_date_obj = zone_file_date_obj
        self._domains_database_user = domains_database_user
        self._domains_database_password = domains_database_password
        self._domains_database_name = domains_database_name
        self._sld_path_file = os.path.join(load_zone_file_pack_path, sld_file_name)
        log_path_file = os.path.join(load_zone_file_pack_path, sld_file_name.replace(".sld.txt", ".log.txt"))
        did_path_file = os.path.join(load_zone_file_pack_path, sld_file_name.replace(".sld.txt", ".did.txt"))
        task_support.Task.__init__(self,
                                   log_path_file=log_path_file,
                                   did_path_file=did_path_file) 

    def make_command(self):
        pack_to_domains_database_path_file = os.path.abspath(__file__)
        pack_to_domains_database_path = os.path.dirname(pack_to_domains_database_path_file)
        pack_to_domains_database_sld_path_file = os.path.join(pack_to_domains_database_path, "load_zone_file_pack_to_domains_database_sld.py")
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
        self._load_zone_file_pack_path = None
        self._core_total = None

        # State.
        self._config = None
        self._domains_database_user = None
        self._domains_database_password = None
        self._domains_database_name = None
        self._zone_file_tld = None
        self._zone_file_date_obj = None

    def process_arguments(self):
        argument_parser = argparse.ArgumentParser()
        argument_parser.add_argument("--load_zone_file_pack_path",
                                     type=str,
                                     required=True,
                                     help="Load Zone File pack path. "
                                          "Must exist. "
                                          "(Mandatory)")
        argument_parser.add_argument("--core_total",
                            type=int,
                            required=True,
                            help="Number of cores. "
                                 "Must be 1 or more. "
                                 "(Mandatory)")

        namespace = argument_parser.parse_args()
        self._load_zone_file_pack_path = util.make_item_path_exist(namespace.load_zone_file_pack_path)
        self._core_total = util.make_int_ge(namespace.core_total, 1)

    def process_config(self):
        self._config = util.Config(self._load_zone_file_pack_path)
        self._config.read()
        self._domains_database_user = self._config.make_value("domains_database_user")
        self._domains_database_password = self._config.make_value("domains_database_password")
        self._domains_database_name = self._config.make_value("domains_database_name")
        self._zone_file_tld = self._config.make_value("zone_file_tld")
        self._zone_file_date_obj = util.make_item_date_obj(self._config.make_value("zone_file_date_str"))

    def process_slds(self):
        task_manager = task_support.TaskManager("Slds", self._core_total, idle_freq_seconds=5, track_freq_seconds=30)
        file_names = os.listdir(self._load_zone_file_pack_path)
        for file_name in sorted(file_names):
            if file_name.endswith(".sld.txt"):
                sld_path_file = os.path.join(self._load_zone_file_pack_path, file_name)
                task_sld = TaskSld(self._zone_file_tld,
                                   self._zone_file_date_obj,
                                   self._domains_database_user,
                                   self._domains_database_password,
                                   self._domains_database_name,
                                   self._load_zone_file_pack_path,
                                   file_name)
                task_manager.add_task(task_sld)
        task_manager.execute()

    def start(self):
        self.process_arguments()
        self.process_config()
        self.process_slds()

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    main = Main()
    main.start()
