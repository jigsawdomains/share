import datetime
import os
import subprocess
import sys
import time

class Task():

    # Level.
    INIT = "INIT"
    WAIT = "WAIT"
    BUSY = "BUSY"
    DONE_OKAY = "DONE_OKAY"
    DONE_FAIL = "DONE_FAIL"

    LEVELS = [INIT,
              WAIT,
              BUSY,
              DONE_OKAY,
              DONE_FAIL]

    def __init__(self, did_path_file=None):
        self._did_path_file = did_path_file 
        self._level = Task.INIT
        self._popen_command = None
        self._popen_code = None
        self._popen = None

    def get_level(self):
        return self._level 

    def get_popen_command(self):
        return self._popen_command 

    def get_popen_code(self):
        return self._popen_code 

    def make_command(self):
        raise NotImplementedError

    def update(self):
        if self._level == Task.INIT:
            if self._did_path_file is None:
                self._level = Task.WAIT
            else:
                if os.path.isfile(self._did_path_file):
                    self._level = Task.DONE_OKAY
                else:
                    self._level = Task.WAIT
        elif self._level == Task.BUSY:
            popen_code = self._popen.poll()
            if popen_code is not None:
                self._popen_code = popen_code
                self._popen = None
                if self._popen_code == 0:
                    self._level = Task.DONE_OKAY
                    if self._did_path_file is not None:
                        did_handle = open(self._did_path_file, "w")
                        did_handle.write(f"Did: {datetime.datetime.now().isoformat()}\n")
                        did_handle.flush()
                        did_handle.close()
                else:
                    self._level = Task.DONE_FAIL

    def get_level(self):
        return self._level

    def launch(self):
        self._popen_command = self.get_command()
        self._popen = subprocess.Popen(self._popen_command)
        self._level = Task.BUSY

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
        return (self._level_to_total[Task.DONE_OKAY] +
                self._level_to_total[Task.DONE_FAIL])

    def get_both_task_total(self):
        return (self.get_left_task_total() + self.get_done_task_total())

    def get_percent(self):
        return int((self.get_left_task_total() / self.get_both_task_total()) * 100)

class Direction():

    def __init__(self,
                 head_snapshot,
                 tail_snapshot):
        self._head_snapshot = head_snapshot
        self._tail_snapshot = tail_snapshot
        self._duration = (self._tail_snapshot.get_snap_datetime() -
                          self._head_snapshot.get_snap_datetime())
        self._achieved = (self._tail_snapshot.get_done_task_total() -
                          self._head_snapshot.get_done_task_total())
        if self._achieved > 0:
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
        both = self._tail_snapshot.get_both_task_total()
        if ((self._est_duration is None) or (self._est_complete is None)):
            edu = "Calculating"
            eco = "Calculating"
        else:
            edu = str(self._est_duration).rstrip("0123456789").rstrip(".")
            eco = str(self._est_complete).rstrip("0123456789").rstrip(".")
        summary = f"{per}% ({done} of {both}) Duration: {edu} Complete: {eco}"
        return summary

class TaskManager():

    def __init__(self,
                 core_total,
                 track_freq_seconds=None):
        self._core_total = core_total
        self._track_freq_seconds = track_freq_seconds
        self._tasks = []

    def stop(self, msg):
        sys.stdout.write(msg)
        sys.exit(1)

    def add_task(self, task):
        self._tasks.append(task)

    def stop_if_done_fail_tasks(self):
        done_fail_tasks = []
        for task in self._tasks:
            if task.get_level() == Task.DONE_FAIL:
                done_fail_tasks.append(task)
        if len(done_fail_tasks) > 0:
            msg = "The following tasks had non zero code:\n"
            for task in done_fail_tasks:
                msg = msg + "Command: {task.get_popen_command()} Code: {task.get_popen_code()}\n"
                self.stop(msg)

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
            self.stop(msg)

    def update(self):
        for task in self._tasks:
            task.update()

    def execute(self):
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

            # Stop on any failure.
            self.stop_if_done_fail_tasks()
 
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
                    direction = Direction(head_snapshot, tail_snapshot)
                    summary = direction.get_summary()
                    sys.stdout.write(f"{summary}\n")
                    sys.stdout.flush()

            # Idle.
            time.sleep(5)
