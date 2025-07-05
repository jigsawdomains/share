# Internal
import datetime
import fcntl
import json
import os
import random
import time

# Local
import task_support
import database
import util

#-------------------------------------------------------------------------------

class TaskRDAP(task_support.Task):

    def __init__(self, sld_label, tld_label):
        self._sld_label = sld_label 
        self._tld_label = tld_label 
        task_support.Task.__init__(self) 
        self._found = None
        self._data = None

    def get_found(self):
        return self._found

    def get_data(self):
        return self._data

    def make_command(self):
        command = ["rdap",
                   "--raw",
                   "--type", "domain",
                   f"{self._sld_label}.{self._tld_label}"]
        return command

    def make_result(self):
        result = False
        self._found = False

        # Valid, found.
        if self._popen_code == 0:
            result = True
            self._found = True

        # Valid, not found.
        if self._popen_code == 1:
            if self.get_popen_stderr() == "# Error: RDAP server returned 404, object does not exist.\n":
                result = True

        return result

    def make_outcome(self):
        if self._found:
            self._data = json.loads(self.get_popen_stdout())

#-------------------------------------------------------------------------------

class RDAP():

    #REQUEST_PER_MIN = 30
    REQUEST_PER_MIN = 5

    LOCK_FILE_NAME = "lock.txt"
    STAT_FILE_NAME = "stat.txt"

    # https://www.iana.org/assignments/rdap-json-values/rdap-json-values.xhtml

    EVENT_REGISTRATION = "registration"
    EVENT_REREGISTRATION = "reregistration"
    EVENT_LAST_CHANGED = "last changed"
    EVENT_EXPIRATION = "expiration"
    EVENT_DELETION = "deletion"
    EVENT_REINSTANTIATION = "reinstantiation"
    EVENT_TRANSFER = "transfer"
    EVENT_LOCKED = "locked"
    EVENT_UNLOCKED = "unlocked"
    EVENT_LAST_UPDATE_OF_RDAP_DATABASE = "last update of RDAP database"
    EVENT_REGISTRAR_EXPIRATION = "registrar expiration"
    EVENT_ENUM_VALIDATION_EXPIRATION = "enum validation expiration"

    # Indicate registered dates.
    TAKE_EVENTS = [EVENT_REGISTRATION,
                   EVENT_REREGISTRATION,
                   EVENT_EXPIRATION,
                   EVENT_DELETION,
                   EVENT_REINSTANTIATION]

    # Do not indicate registered dates.
    SKIP_EVENTS = [EVENT_LAST_CHANGED,
                   EVENT_TRANSFER,
                   EVENT_LOCKED,
                   EVENT_UNLOCKED,
                   EVENT_LAST_UPDATE_OF_RDAP_DATABASE,
                   EVENT_REGISTRAR_EXPIRATION,
                   EVENT_ENUM_VALIDATION_EXPIRATION]

    def __init__(self,
                 item_path,
                 domains_database_user,
                 domains_database_password):
        self._item_path = item_path
        self._domains_database_user = domains_database_user
        self._domains_database_password = domains_database_password
        self._domains_db = database.DomainsDB(self._domains_database_user,
                                              self._domains_database_password)
        self._lock_path_file = os.path.join(self._item_path, RDAP.LOCK_FILE_NAME)
        self._lock_handle = None

    def _init_lock(self):
        self._lock_handle = None
        if not os.path.isfile(self._lock_path_file):
            handle = open(self._lock_path_file, "w")
            handle.close()

    def _wait_lock(self):
        self._lock_handle = open(self._lock_path_file, "r")
        remain = True
        while remain:
            try:
                fcntl.flock(self._lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                remain = False
            except BlockingIOError:
                time.sleep(random.uniform(1, 2))

    def _wait_rate(self):
        # Rate: Read.
        handle = open(self._lock_path_file, "r")
        lines = []
        for line in handle:
            lines.append(line.strip())
        handle.close()
        rate_datetimes = []
        for line in lines:
            rate_datetime = util.make_item_datetime(line)
            rate_datetimes.append(rate_datetime)

        # Wait for rate.
        remain = True
        while remain:
            until_datetime = datetime.datetime.now()
            start_datetime = until_datetime - datetime.timedelta(seconds=60)
            total = 0
            for rate_datetime in rate_datetimes:
                if rate_datetime >= start_datetime:
                    total = total + 1
            if total < RDAP.REQUEST_PER_MIN:
                remain = False
            else:
                time.sleep(random.uniform(1, 2))

        # Rate: Write.
        handle = open(self._lock_path_file, "w")
        until_datetime = datetime.datetime.now()
        start_datetime = until_datetime - datetime.timedelta(seconds=60)
        for rate_datetime in rate_datetimes:
            if rate_datetime >= start_datetime:
                handle.write(f"{rate_datetime.isoformat()}\n")
        handle.write(f"{until_datetime.isoformat()}\n")
        handle.close()

    def _cede_lock(self):
        fcntl.flock(self._lock_handle.fileno(), fcntl.LOCK_UN)

    def _action(self, sld_label, tld_label):
        task_rdap = TaskRDAP(sld_label, tld_label)
        task_manager = task_support.TaskManager()
        task_manager.add_task(task_rdap)
        task_manager.execute()

        register_dates = []
        if task_rdap.get_found():
            # https://www.rfc-editor.org/rfc/rfc9083.html#name-events
            data = task_rdap.get_data()
            if "events" in data.keys():
                events = data["events"]
                for event in events:
                    if (("eventAction" in event.keys()) and ("eventDate" in event.keys())):
                        event_action = event["eventAction"]
                        event_date = util.make_item_datetime(event["eventDate"]).date()
                        found = False
                        if event_action in RDAP.TAKE_EVENTS:
                            found = True
                            register_dates.append(event_date)
                        if event_action in RDAP.SKIP_EVENTS:
                            found = True
                        if not found:
                            msg = f"Unexpected event: {event_action}\n"
                            stop(msg)
                    else:
                        msg = f"Unexpected JSON format for event: {event}\n"
                        stop(msg)
            else:
                msg = f"Unexpected JSON format for data: {data}\n"
                stop(msg)

        (start_none_date, until_none_date) = util.make_start_until_none_date_tuple(register_dates)
        req_source = database.DomainsDB.RDAP
        print(register_dates)
        self._domains_db.update_fqdn(req_source,
                                     sld_label,
                                     tld_label,
                                     start_none_date,
                                     until_none_date)

    def request(self, sld_label, tld_label):
        self._init_lock()
        self._wait_lock()
        self._wait_rate()
        print("qqqqqq")
        self._action(sld_label, tld_label)
        print("ddddqqqqqq")
        self._cede_lock()
