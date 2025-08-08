# Setup
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "common"))

# Internal
import argparse

# Local
import distribute
import util

#-------------------------------------------------------------------------------

class TaskFqdn(distribute.Task):

    def __init__(self, 
                 domains_database_user,
                 domains_database_password,
                 inspect_date,
                 batch_pack_path,
                 fqdn_file_name):
        self._domains_database_user = domains_database_user
        self._domains_database_password = domains_database_password
        self._inspect_date = inspect_date
        self._fqdn_path_file = os.path.join(batch_pack_path, fqdn_file_name)
        self._report_path_file = os.path.join(batch_pack_path, fqdn_file_name.replace(".fqdn.txt", ".report.txt"))
        log_path_file = os.path.join(batch_pack_path, fqdn_file_name.replace(".fqdn.txt", ".log.txt"))
        did_path_file = os.path.join(batch_pack_path, fqdn_file_name.replace(".fqdn.txt", ".did.txt"))
        distribute.Task.__init__(self,
                                 log_path_file=log_path_file,
                                 did_path_file=did_path_file) 

    def make_command(self):
        script_path_file = os.path.abspath(__file__)
        script_path = os.path.dirname(script_path_file)
        fqdn_py_path_file = os.path.join(script_path, "check_batch_pack_fqdn.py")
        command = [sys.executable,
                   fqdn_py_path_file,
                   "--domains_database_user", self._domains_database_user,
                   "--domains_database_password", self._domains_database_password, 
                   "--inspect_date", self._inspect_date.isoformat(),
                   "--fqdn_path_file", self._fqdn_path_file,
                   "--report_path_file", self._report_path_file]
        return command

#-------------------------------------------------------------------------------

class Main():

    def __init__(self):
        # Arguments.
        self._batch_pack_path = None
        self._core_total = None

        # State.
        self._domains_database_user = None
        self._domains_database_password = None
        self._inspect_date = None

    def process_arguments(self):
        argument_parser = argparse.ArgumentParser()
        argument_parser.add_argument("--batch_pack_path",
                                     type=str,
                                     required=True,
                                     help="Batch pack path. "
                                          "Must exist. "
                                          "(Mandatory)")
        argument_parser.add_argument("--core_total",
                            type=int,
                            required=True,
                            help="Number of cores. "
                                 "Must be 1 or more. "
                                 "(Mandatory)")

        namespace = argument_parser.parse_args()
        self._batch_pack_path = util.make_item_path_exist(namespace.batch_pack_path)
        self._core_total = util.make_int_ge(namespace.core_total, 1)

    def process_config(self):
        self._config = util.Config(self._batch_pack_path)
        self._config.read()
        self._domains_database_user = self._config.get_value("domains_database_user")
        self._domains_database_password = self._config.get_value("domains_database_password")
        self._inspect_date = self._config.get_value("inspect_date")

    def process_fqdns(self):
        task_manager = distribute.TaskManager(label="FQDNS",
                                              core_total=self._core_total,
                                              idle_freq_seconds=5,
                                              track_freq_seconds=30)
        file_names = os.listdir(self._batch_pack_path)
        for file_name in sorted(file_names):
            if file_name.endswith(".fqdn.txt"):
                fqdn_path_file = os.path.join(self._batch_pack_path, file_name)
                task_fqdn = TaskFqdn(self._domains_database_user,
                                     self._domains_database_password,
                                     self._inspect_date,
                                     self._batch_pack_path,
                                     file_name)
                task_manager.add_task(task_fqdn)
        task_manager.execute()

    def start(self):
        self.process_arguments()
        self.process_config()
        self.process_fqdns()

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    main = Main()
    main.start()
