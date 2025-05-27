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
                 database_user,
                 database_password,
                 database_name,
                 pack_path,
                 sld_file_name):
        self._zone_file_tld = zone_file_tld 
        self._zone_file_date_obj = zone_file_date_obj
        self._database_user = database_user
        self._database_password = database_password
        self._database_name = database_name
        self._sld_path_file = os.path.join(pack_path, sld_file_name)
        log_path_file = os.path.join(pack_path, sld_file_name.replace(".sld.txt", ".log.txt"))
        did_path_file = os.path.join(pack_path, sld_file_name.replace(".sld.txt", ".did.txt"))
        task_support.Task.__init__(self,
                                   log_path_file=log_path_file,
                                   did_path_file=did_path_file) 

    def make_command(self):
        pack_to_database_path_file = os.path.abspath(__file__)
        pack_to_database_path = os.path.dirname(pack_to_database_path_file)
        pack_to_database_sld_path_file = os.path.join(pack_to_database_path, "pack_to_database_sld.py")
        command = [sys.executable,
                   pack_to_database_sld_path_file,
                   "--zone_file_tld", self._zone_file_tld,
                   "--zone_file_date_str", self._zone_file_date_obj.isoformat(),
                   "--database_user", self._database_user,
                   "--database_password", self._database_password, 
                   "--database_name", self._database_name,
                   "--sld_path_file", self._sld_path_file]
        return command

#-------------------------------------------------------------------------------

class Main():

    def __init__(self):
        # Arguments.
        self._pack_path = None
        self._database_user = None
        self._database_password = None
        self._database_name = None
        self._core_total = None

        # State.
        self._zone_file_tld = None
        self._zone_file_date_obj = None

    def process_arguments(self):
        argument_parser = argparse.ArgumentParser()
        argument_parser.add_argument("--pack_path",
                                     type=str,
                                     required=True,
                                     help="Transfer pack path. "
                                          "Must exist. "
                                          "(Mandatory)")
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
        argument_parser.add_argument("--core_total",
                            type=int,
                            required=True,
                            help="Number of cores. "
                                 "(Mandatory)")

        namespace = argument_parser.parse_args()
        self._pack_path = util.make_item_path_exist(namespace.pack_path)
        self._database_user = namespace.database_user
        self._database_password = namespace.database_password
        self._database_name = namespace.database_name
        self._core_total = namespace.core_total

    def process_tld(self):
        tld_file_name = f"tld.txt"
        tld_path_file = os.path.join(self._pack_path, tld_file_name)
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

    def process_sld(self):
        task_manager = task_support.TaskManager("Slds", self._core_total, idle_freq_seconds=5, track_freq_seconds=30)
        file_names = os.listdir(self._pack_path)
        for file_name in sorted(file_names):
            if file_name.endswith(".sld.txt"):
                sld_path_file = os.path.join(self._pack_path, file_name)
                task_sld = TaskSld(self._zone_file_tld,
                                   self._zone_file_date_obj,
                                   self._database_user,
                                   self._database_password,
                                   self._database_name,
                                   self._pack_path,
                                   file_name)
                task_manager.add_task(task_sld)
        task_manager.execute()

    def start(self):
        self.process_arguments()
        self.process_tld()
        self.process_sld()

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    main = Main()
    main.start()
