# Setup
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "common"))

# Internal
import argparse
import time
import random

# Local
import distribute
import database
import util
import lookup

#-------------------------------------------------------------------------------

class Main():

    def __init__(self):
        # Arguments.
        self._domains_database_user = None
        self._domains_database_password = None
        self._zone_file_tld = None
        self._inspect_date = None

        # State.
        self._domains_db = None
        self._rdap = None

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
        argument_parser.add_argument("--zone_file_tld",
                                     type=str,
                                     required=True,
                                     help="Zone File TLD. "
                                          "Must exist. "
                                          "(Mandatory)")
        argument_parser.add_argument("--inspect_date",
                                     type=str,
                                     required=True,
                                     help="Inspect date (YYYY-MM-DD). "
                                          "(Mandatory)")

        namespace = argument_parser.parse_args()
        self._domains_database_user = namespace.domains_database_user
        self._domains_database_password = namespace.domains_database_password
        self._zone_file_tld = namespace.zone_file_tld
        self._inspect_date = util.make_item_date(namespace.inspect_date)
        self._domains_db = database.DomainsDB(self._domains_database_user,
                                              self._domains_database_password)
        self._rdap = lookup.RDAP("/tmp", self._domains_database_user, self._domains_database_password)


    def check(self, sld_label, tld_label):
        free = True
        result = self._domains_db.inspect_fqdn(sld_label, tld_label)

        if result is not None:

            free = False

            (sources, start_none_date, until_none_date) = result
            if ((start_none_date is not None) and (until_none_date is not None)):
                if ((start_none_date <= self._inspect_date) and (self._inspect_date <= until_none_date)):
                    free = False
        return free

    def check2(self, sld_label, tld_label):
        free = True
        result = self._domains_db.inspect_fqdn(sld_label, tld_label)
        print(result)
        #time.sleep(random.uniform(1, 2))
        #result = self._domains_db.inspect_fqdn(sld_label, tld_label)
        #print(result)
        #time.sleep(random.uniform(1, 2))
        #result = self._domains_db.inspect_fqdn(sld_label, tld_label)
        #print(result)
        #time.sleep(random.uniform(1, 2))
        #result = self._domains_db.inspect_fqdn(sld_label, tld_label)
        #print(result)
        #time.sleep(random.uniform(1, 2))


        if result is not None:
            (sources, start_none_date, until_none_date) = result
            if ((start_none_date is not None) and (until_none_date is not None)):
                if ((start_none_date <= self._inspect_date) and (self._inspect_date <= until_none_date)):
                    free = False
        return free

    def search(self):
        tld_label = self._zone_file_tld 

        # Begin with two digits, 10, as most registers prevent single
        # character domain names.
        number = 100222

        free = False
        while not free:
            free = True
            sld_label = str(number)
            print(sld_label)
            free = self.check(sld_label, tld_label)

            if free:
                print("RDAPPING")
                self._rdap.request(sld_label, tld_label)
                print("RDAPPING done")

                print("eeeeeeeeeeeeeeeeeeeee")
                free = self.check2(sld_label, tld_label)
                print(free)

            # print(sld_label)
            # result = self._domains_db.inspect_fqdn(sld_label, tld_label)
            # if result is not None:
            #     (sources, start_none_date, until_none_date) = result
            #     if ((start_none_date is not None) and (until_none_date is not None)):
            #         if ((start_none_date <= self._inspect_date) and (self._inspect_date <= until_none_date)):
            #             free = False




            number = number + 1
#
#
#
#        task_manager = distribute.TaskManager(label="FQDNS",
#                                              core_total=self._core_total,
#                                              idle_freq_seconds=5,
#                                              track_freq_seconds=30)
#        file_names = os.listdir(self._batch_pack_path)
#        for file_name in sorted(file_names):
#            if file_name.endswith(".fqdn.txt"):
#                fqdn_path_file = os.path.join(self._batch_pack_path, file_name)
#                task_fqdn = TaskFqdn(self._domains_database_user,
#                                     self._domains_database_password,
#                                     self._inspect_date,
#                                     self._batch_pack_path,
#                                     file_name)
#                task_manager.add_task(task_fqdn)
#        task_manager.execute()

    def start(self):
        self.process_arguments()
        self.search()

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    main = Main()
    main.start()
