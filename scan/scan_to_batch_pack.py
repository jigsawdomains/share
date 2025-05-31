# Setup
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "common"))

# Internal
import argparse
import itertools

# Local
import task_support
import util

#-------------------------------------------------------------------------------

class Main():

    L = "L"
    LETTERS = []
    N = "N"
    NUMBERS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

    def __init__(self):
        # Arguments.
        self._scan_key_values = None
        self._scan_format = None
        self._check_pack_path = None

    def process_arguments(self):
        argument_parser = argparse.ArgumentParser()

        argument_parser.add_argument("--scan_key_value",
                                     type=str,
                                     nargs='+',
                                     action='append',
                                     help="Declare scan <KEY> and then its ordered <VALUES>. "
                                          "Multiple occurances permitted. "
                                          "Example: N 0 1 2 3 4 5 6 7 8 9 "
                                          "Example: L a b c d e f g h i j k l m n o p q r s t u v w x y z "
                                          "(Optional)")
        argument_parser.add_argument("--scan_format",
                            type=str,
                            required=True,
                            help="Scan format. "
                                 "Every <KEY> is expanded to its <VALUES>. "
                                 "Must expand to legal domain name. "
                                 "Example: theLL.com "
                                 "(Mandatory)")
        argument_parser.add_argument("--part_size",
                                     type=int,
                                     required=True,
                                     help="Part size. "
                                          "Must be 1 or more. "
                                          "(Mandatory)")
        argument_parser.add_argument("--scan_pack_path",
                                     type=str,
                                     required=True,
                                     help="Scan pack path. "
                                          "Must exist and must be empty. "
                                          "(Mandatory)")
        namespace = argument_parser.parse_args()
        self._scan_key_values = namespace.scan_key_value
        self._scan_format = namespace.scan_format
        for scan_key_value in self._scan_key_values:
            if len(scan_key_value) < 2:
                msg = f"KEY without following VALUES: {scan_key_value}\n"
                util.stop(msg)
        self._part_size = util.make_int_ge(namespace.part_size, 1)
        self._scan_pack_path = util.make_item_path_exist_empty(namespace.scan_pack_path)

    def expand_scan(self):
        # Replace each KEY with its VALUES list
        scan_parts = [self._scan_format]
        for scan_key_value in self._scan_key_values:
            key = scan_key_value[0]
            values = scan_key_value[1:]
            update_scan_parts = []
            for scan_part in scan_parts:
                if type(scan_part) == type([]):
                    update_scan_parts.append(scan_part)
                else:
                    elements = scan_part.split(key)
                    for element in elements[0:-1]:
                        if element != "":
                            update_scan_parts.append(element)
                        update_scan_parts.append(values)
                    if elements[-1] != "":
                        update_scan_parts.append(elements[-1])
            scan_parts = update_scan_parts

        # Replace each word as its own values list
        update_scan_parts = []
        for scan_part in scan_parts:
            if type(scan_part) == type([]):
                update_scan_parts.append(scan_part)
            else:
                update_scan_parts.append([scan_part])
        scan_parts = update_scan_parts

        # Retain
        self._scan_parts = scan_parts

    def generate(self):
        scan_product = itertools.product(*self._scan_parts)

        part_number = 0
        current_part_size = 0
        check_handle = None
        for parts in scan_product:
            if current_part_size == self._part_size:
                check_handle.close()
                check_handle = None
            if check_handle is None:
                part_number = part_number + 1
                check_file_name = f"{part_number:06}.check.txt"
                check_path_file = os.path.join(self._scan_pack_path, check_file_name)
                check_handle = open(check_path_file, "w")
                current_part_size = 0
            domain = "".join(parts)
            check_handle.write(f"{domain}\n")
            current_part_size = current_part_size + 1
        check_handle.close()

    def start(self):
        self.process_arguments()
        self.expand_scan()
        self.generate()

if __name__ == '__main__':
    main = Main()
    main.start()
