# Internal
import datetime
import os
import shlex
import subprocess
import sys
import time

# Local
import util

#-------------------------------------------------------------------------------

class Task():

    # Level.
    INIT = "INIT"
    WAIT = "WAIT"
    BUSY = "BUSY"
    DONE = "DONE"

    LEVELS = [INIT, WAIT, BUSY, DONE]

    def __init__(self,
                 log_path_file=None,
                 did_path_file=None):
        self._log_path_file = log_path_file 
        self._did_path_file = did_path_file 
        self._level = Task.INIT
        self._popen_command = None
        self._popen_code = None
        self._popen_stdout = None
        self._popen_stderr = None
        self._popen = None

    def get_level(self):
        return self._level 

    def get_popen_command(self):
        return self._popen_command 

    def get_popen_code(self):
        return self._popen_code 

    def get_popen_stdout(self):
        return self._popen_stdout 

    def get_popen_stderr(self):
        return self._popen_stderr 

    def present_popen_command(self):
        present = ""
        for part in self._popen_command:
            if present != "":
                present = present + " "
            present = present + shlex.quote(part)
        return present

    def _process_did_path_file(self):
        if self._did_path_file is not None:
            did_handle = open(self._did_path_file, "w")
            did_handle.write(f"Did: {datetime.datetime.now().isoformat()}\n")
            did_handle.close()

    def _process_log_path_file(self):
        if self._log_path_file is not None:
            log_handle = open(self._log_path_file, "w")
            log_handle.write(f"popen_command:\n")
            log_handle.write(f"{self.present_popen_command()}\n")
            log_handle.write(f"popen_code:\n")
            log_handle.write(f"{self._popen_code}\n")
            log_handle.write(f"make_result:\n")
            log_handle.write(f"{self.make_result()}\n")
            log_handle.write(f"stdout:\n")
            log_handle.write(self._popen_stdout)
            log_handle.write(f"stderr:\n")
            log_handle.write(self._popen_stderr)
            log_handle.close()

    def update(self):
        if self._level == Task.INIT:
            if self._did_path_file is None:
                self._level = Task.WAIT
            else:
                if os.path.isfile(self._did_path_file):
                    self._level = Task.DONE
                else:
                    self._level = Task.WAIT
        elif self._level == Task.BUSY:
            popen_code = self._popen.poll()
            if popen_code is not None:
                self._level = Task.DONE
                self._popen_code = popen_code
                self._popen_stdout = self._popen.stdout.read().decode(encoding="latin1")
                self._popen_stderr = self._popen.stderr.read().decode(encoding="latin1")
                self._popen = None
                self._process_log_path_file()
                if self.make_result():
                    self.make_outcome()
                    self._process_did_path_file()
                else:
                    msg = ""
                    msg = msg + "Unexpected Failure:"
                    msg = msg + f" Command: {self.present_popen_command()}"
                    msg = msg + f" Code: {self._popen_code}"
                    if self._log_path_file is not None:
                        msg = msg + f" Log: {self._log_path_file}"
                    msg = msg + "\n"
                    util.stop(msg)

    def launch(self):
        self._popen_command = self.make_command()
        self._popen = subprocess.Popen(self._popen_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._level = Task.BUSY

    # Override as required:

    def make_command(self):
        raise NotImplementedError

    def make_result(self):
        return self._popen_code == 0

    def make_outcome(self):
        pass

#-------------------------------------------------------------------------------

class Snapshot():

    def __init__(self, tasks):
        self._level_to_total = {}
        for level in Task.LEVELS:
            self._level_to_total[level] = 0
        for task in tasks:
            self._level_to_total[task.get_level()] = self._level_to_total[task.get_level()] + 1
        self._snap_datetime = datetime.datetime.now()

    def get_snap_datetime(self):
        return self._snap_datetime 

    def get_wait_task_total(self):
        return self._level_to_total[Task.WAIT]

    def get_busy_task_total(self):
        return self._level_to_total[Task.BUSY]

    def get_left_task_total(self):
        return (self._level_to_total[Task.INIT] +
                self._level_to_total[Task.WAIT] +
                self._level_to_total[Task.BUSY])

    def get_done_task_total(self):
        return self._level_to_total[Task.DONE]

    def get_full_task_total(self):
        return (self.get_left_task_total() + self.get_done_task_total())

    def get_percent(self):
        return (100 - int((self.get_left_task_total() / self.get_full_task_total()) * 100))

#-------------------------------------------------------------------------------

class Direction():

    def __init__(self,
                 core_total,
                 head_snapshot,
                 tail_snapshot):
        self._core_total = core_total
        self._head_snapshot = head_snapshot
        self._tail_snapshot = tail_snapshot
        self._duration = (self._tail_snapshot.get_snap_datetime() -
                          self._head_snapshot.get_snap_datetime())
        self._achieved = (self._tail_snapshot.get_done_task_total() -
                          self._head_snapshot.get_done_task_total())
        if self._achieved >= self._core_total:
            avg_task_duration = self._duration / self._achieved 
            self._est_duration = self._tail_snapshot.get_left_task_total() * avg_task_duration 
            self._est_complete = self._tail_snapshot.get_snap_datetime() + self._est_duration 
        else:
            self._est_duration = None
            self._est_complete = None

    def get_est_duration(self):
        return self._est_duration

    def get_est_duration(self):
        return self._est_complete

    def get_summary(self):
        per = self._tail_snapshot.get_percent()
        done = self._tail_snapshot.get_done_task_total()
        full = self._tail_snapshot.get_full_task_total()

        busy = self._tail_snapshot.get_busy_task_total()
        core = self._core_total

        if ((self._est_duration is None) or (self._est_complete is None)):
            edu = "Calculating"
            eco = "Calculating"
        else:
            edu = str(self._est_duration).rstrip("0123456789").rstrip(".")
            eco = str(self._est_complete).rstrip("0123456789").rstrip(".")
        summary = f"{per}% Task: [{done} of {full}] Core: [{busy} of {core}] Duration: {edu} Complete: {eco}"
        return summary

#-------------------------------------------------------------------------------

class TaskManager():

    def __init__(self,
                 label=None,
                 core_total=1,
                 idle_freq_seconds=1,
                 track_freq_seconds=None):
        self._label = label
        self._core_total = core_total
        self._idle_freq_seconds = idle_freq_seconds
        self._track_freq_seconds = track_freq_seconds
        self._tasks = []

    def add_task(self, task):
        self._tasks.append(task)

    def get_tasks(self):
        return self._tasks 

    def launch_task(self):
        wait_tasks = []
        for task in self._tasks:
            if task.get_level() == Task.WAIT:
                wait_tasks.append(task)
        if len(wait_tasks) > 0:
            wait_task = wait_tasks[0]
            wait_task.launch()
        else:
            msg = "Unable to launch as no waiting task\n"
            util.stop(msg)

    def update(self):
        for task in self._tasks:
            task.update()

    def execute(self):
        if self._label is not None:
            util.info(f"Start: {self._label}\n")
        track_datetime = None
        if self._track_freq_seconds is None:
            track_duration = None
        else:
            track_duration = datetime.timedelta(seconds=self._track_freq_seconds)

        self.update()
        head_snapshot = Snapshot(self._tasks)
        remain = True
        while remain:
            self.update()
            tail_snapshot = Snapshot(self._tasks)

            # Complete when no left tasks.
            if tail_snapshot.get_left_task_total() == 0:
                remain = False
 
            # Launch if core available and task waiting.
            if tail_snapshot.get_busy_task_total() < self._core_total:
                if tail_snapshot.get_wait_task_total() > 0:
                    self.launch_task()
       
            # Track as requested.
            if track_duration is not None:
                act = False
                if track_datetime is None:
                    act = True
                else:
                    elapsed_duration = (datetime.datetime.now() - track_datetime)
                    if  elapsed_duration > track_duration:
                        act = True
                if act:
                    track_datetime = datetime.datetime.now()
                    direction = Direction(self._core_total, head_snapshot, tail_snapshot)
                    summary = direction.get_summary()
                    util.info(f"{summary}\n")

            # Idle.
            time.sleep(self._idle_freq_seconds)
        if self._label is not None:
            util.info(f"Finish: {self._label}\n")
