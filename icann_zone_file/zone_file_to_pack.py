import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "common"))

import argparse
import datetime
import json

import task_support
import util

#-------------------------------------------------------------------------------

class TaskAuthentication(task_support.Task):

    def __init__(self, 
                 icann_user,
                 icann_password):
        self._icann_user = icann_user 
        self._icann_password = icann_password
        self._access_token = None
        task_support.Task.__init__(self) 

    def get_access_token(self):
        return self._access_token

    def make_command(self):
        data = json.dumps({"username": self._icann_user, "password": self._icann_password})
        command = ["curl",
                   "--request", "POST",
                   "--header", "Accept: application/json",
                   "--header", "Content-Type: application/json",
                   "--data", data,
                   "https://account-api.icann.org/api/authenticate"]
        return command

    def make_outcome(self):
        data = json.loads(self.get_popen_stdout())
        if "accessToken" in data.keys():
            self._access_token = data["accessToken"]
        else:
            msg = "Unexpected data format: {data}\n"
            util.stop(msg)

#-------------------------------------------------------------------------------

class TaskLink(task_support.Task):

    def __init__(self, 
                 access_token,
                 tld):
        self._access_token = access_token 
        self._tld = tld 
        self._link = None
        task_support.Task.__init__(self) 

    def get_link(self):
        return self._link

    def make_command(self):
        command = ["curl",
                   "--request", "GET",
                   "--header", "Accept: application/json",
                   "--header", "Content-Type: application/json",
                   "--header", f"Authorization: Bearer {self._access_token}",
                   "https://czds-api.icann.org/czds/downloads/links"]
        return command

    def make_outcome(self):
        data = json.loads(self.get_popen_stdout())
        for link in data:
            if link.endswith(f"{self._tld}.zone"):
                if self._link is None:
                    self._link = link
                else:
                    msg = "Unexpected duplicate links for: {self._tld}\n"
                    util.stop(msg)
        if self._link is None:
            msg = "Unexpected no link for: {self._tld}\n"
            util.stop(msg)

#-------------------------------------------------------------------------------

class TaskProbe(task_support.Task):

    def __init__(self, 
                 access_token,
                 link):
        self._access_token = access_token 
        self._link = link 
        self._last_modified_date_obj = None
        self._content_length = None
        task_support.Task.__init__(self) 

    def get_last_modified_date_str(self):
        return self._last_modified_date_obj.isoformat()

    def get_content_length(self):
        return self._content_length

    def make_command(self):
        command = ["curl",
                   "--head",
                   "--header", f"Authorization: Bearer {self._access_token}",
                   self._link]
        return command

    def make_outcome(self):
        lines = self.get_popen_stdout().split("\n")
        for line in lines:
            line = line.strip()
            key = "Last-Modified: "
            if line.startswith(key):
                self._last_modified_date_obj = datetime.datetime.strptime(line.replace(key,""), "%a, %d %b %Y %H:%M:%S %Z").date()
            key = "Content-Length: "
            if line.startswith(key):
                self._content_length = int(line.replace(key,""))
        if self._last_modified_date_obj is None:
            msg = "Absent: last_modified_date_obj\n"
            util.stop(msg)
        if self._content_length is None:
            msg = "Absent: content_length\n"
            util.stop(msg)

#-------------------------------------------------------------------------------

class TaskPart(task_support.Task):

    RETRY_TOTAL = 3

    def __init__(self, 
                 access_token,
                 link,
                 tld,
                 last_modified_date_str,
                 part_count,
                 head_index,
                 tail_index,
                 pack_path):
        self._access_token = access_token 
        self._link = link 
        self._tld = tld
        self._last_modified_date_str = last_modified_date_str
        self._part_count = part_count
        self._head_index = head_index
        self._tail_index = tail_index
        self._pack_path = pack_path 
        part_prefix = f"{self._tld}#{self._last_modified_date_str}#{self._part_count:06}"
        dat_file_name = f"{part_prefix}#part.dat.bin"
        did_file_name = f"{part_prefix}#part.did.txt"
        log_file_name = f"{part_prefix}#part.log.txt"
        self._dat_path_file = os.path.join(self._pack_path, dat_file_name)
        self._did_path_file = os.path.join(self._pack_path, did_file_name)
        self._log_path_file = os.path.join(self._pack_path, log_file_name)
        task_support.Task.__init__(self, did_path_file=self._did_path_file) 

    def get_dat_path_file(self):
        return self._dat_path_file

    def make_command(self):
        command = ["curl",
                   "--no-progress-meter",
                   "--retry", str(TaskPart.RETRY_TOTAL),
                   "--request", "GET",
                   "--header", f"Authorization: Bearer {self._access_token}",
                   "--range", f"{self._head_index}-{self._tail_index}",
                   "--stderr", self._log_path_file,
                   "--output", self._dat_path_file,
                   self._link]
        return command

    def tidy(self):
        os.remove(self._dat_path_file)
        os.remove(self._did_path_file)
        os.remove(self._log_path_file)

#-------------------------------------------------------------------------------

class TaskCheck(task_support.Task):

    def __init__(self, 
                 full_path_file):
        self._full_path_file = full_path_file 
        task_support.Task.__init__(self) 

    def make_command(self):
        command = ["gunzip",
                   "--test", self._full_path_file]
        return command

#-------------------------------------------------------------------------------

class Main():

    BLOCK_SIZE = 1024 * 64

    def __init__(self):
        # Arguments.
        self._icann_user = None
        self._icann_password = None
        self._tld = None
        self._pack_path = None
        self._core_total = None

        # State.
        self._access_token = None
        self._link = None
        self._last_modified_date_str = None
        self._content_length = None
        self._full_path_file = None
        self._part_tasks = None

    def stop(self, msg):
        sys.stdout.write(msg)
        sys.exit(1)

    def process_arguments(self):
        argument_parser = argparse.ArgumentParser()

        argument_parser.add_argument("--icann_user",
                            type=str,
                            required=True,
                            help="ICANN user. "
                                 "(Mandatory)")
        argument_parser.add_argument("--icann_password",
                            type=str,
                            required=True,
                            help="ICANN password. "
                                 "(Mandatory)")
        argument_parser.add_argument("--tld",
                                     type=str,
                                     required=True,
                                     help="TLD. "
                                          "Must be available in the ICANN account. "
                                          "(Mandatory)")
        argument_parser.add_argument("--pack_path",
                                     type=str,
                                     required=True,
                                     help="Pack path. "
                                          "Must exist. "
                                          "(Mandatory)")
        argument_parser.add_argument("--part_size",
                                     type=int,
                                     required=True,
                                     help="Part size. Perhaps: 52428800 (50 MiB). "
                                          "(Mandatory)")
        argument_parser.add_argument("--core_total",
                            type=int,
                            required=True,
                            help="Number of cores. "
                                 "(Mandatory)")

        namespace = argument_parser.parse_args()
        self._icann_user = namespace.icann_user 
        self._icann_password = namespace.icann_password 
        self._tld = namespace.tld 
        self._pack_path = util.make_item_path_exist(namespace.pack_path)
        self._part_size = namespace.part_size
        self._core_total = namespace.core_total

    def authentication(self):
        task_authentication = TaskAuthentication(self._icann_user, self._icann_password)
        task_manager = task_support.TaskManager("Authentication", self._core_total, idle_freq_seconds=1)
        task_manager.add_task(task_authentication)
        task_manager.execute()
        self._access_token = task_authentication.get_access_token()

    def link(self):
        task_link = TaskLink(self._access_token, self._tld)
        task_manager = task_support.TaskManager("Link", self._core_total, idle_freq_seconds=1)
        task_manager.add_task(task_link)
        task_manager.execute()
        self._link = task_link.get_link()
        sys.stdout.write(f"Link: {self._link}\n")
        sys.stdout.flush()

    def probe(self):
        task_probe = TaskProbe(self._access_token, self._link)
        task_manager = task_support.TaskManager("Probe", self._core_total, idle_freq_seconds=1)
        task_manager.add_task(task_probe)
        task_manager.execute()
        self._last_modified_date_str = task_probe.get_last_modified_date_str()
        self._content_length = task_probe.get_content_length()
        full_file_name = f"{self._tld}#{self._last_modified_date_str}#full.txt.gz"
        self._full_path_file = os.path.join(self._pack_path, full_file_name)
        sys.stdout.write(f"Last modified date: {self._last_modified_date_str}\n")
        sys.stdout.write(f"Content length: {self._content_length}\n")
        sys.stdout.flush()

    def acquire(self):
        task_manager = task_support.TaskManager("Parts", self._core_total, idle_freq_seconds=5, track_freq_seconds=30)
        part_count = 1
        head_index = 0
        while head_index < self._content_length:
            tail_index = head_index + (self._part_size - 1)
            if tail_index >= self._content_length:
                tail_index = self._content_length - 1
            task_part = TaskPart(self._access_token,
                                 self._link,
                                 self._tld,
                                 self._last_modified_date_str,
                                 part_count,
                                 head_index,
                                 tail_index,
                                 self._pack_path)
            task_manager.add_task(task_part)
            head_index = tail_index + 1
            part_count = part_count + 1
        task_manager.execute()
        self._part_tasks = task_manager.get_tasks()

    def assemble(self):
        full_handle = open(self._full_path_file, "wb")
        for part_task in self._part_tasks:
            dat_handle = open(part_task.get_dat_path_file(), "rb")
            remain = True
            while remain:
                block_octets = dat_handle.read(Main.BLOCK_SIZE)
                if len(block_octets) == 0:
                    remain = False
                else:
                    full_handle.write(block_octets)
            dat_handle.close()
        full_handle.close()

    def check(self):
        task_manager = task_support.TaskManager("Check", self._core_total, idle_freq_seconds=1)
        task_check = TaskCheck(self._full_path_file)
        task_manager.add_task(task_check)
        task_manager.execute()

    def tidy(self):
        for part_task in self._part_tasks:
            part_task.tidy()

    def start(self):
        self.process_arguments()
        self.authentication()
        self.link()
        self.probe()
        if not os.path.isfile(self._full_path_file):
            self.acquire()
            self.assemble()
            self.check()
            self.tidy()
        sys.stdout.write(f"Archive: {self._full_path_file}\n")
        sys.stdout.flush()

if __name__ == '__main__':
    main = Main()
    main.start()
