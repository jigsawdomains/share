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

    def __init__(self):
        # Arguments.
        self._scan_key_values = None
        self._scan_formats = None
        self._inspect_date_obj = None
        self._zero_sources_use_rdap = None
        self._part_size = None
        self._batch_pack_path = None


### configure . txt
### configure . txt
### configure . txt

### control  . txt
### config . txt


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
                                     action='append',
                                     required=True,
                                     help="Scan format. "
                                          "Every <KEY> is expanded to its <VALUES>. "
                                          "Multiple occurances permitted. "
                                          "Must expand to legal domain name. "
                                          "Example: theLL.com "
                                          "(Mandatory)")
        argument_parser.add_argument("--inspect_date_str",
                                     type=str,
                                     required=True,
                                     help="Inspect date (YYYY-MM-DD). "
                                          "(Mandatory)")
        argument_parser.add_argument("--zero_sources_use_rdap",
                                     default=False,
                                     action="store_true",
                                     help="If a FQDN has zero sources, use RDAP. "
                                          "(Mandatory)")
        argument_parser.add_argument("--part_size",
                                     type=int,
                                     required=True,
                                     help="Part size. "
                                          "Must be 1 or more. "
                                          "(Mandatory)")
        argument_parser.add_argument("--batch_pack_path",
                                     type=str,
                                     required=True,
                                     help="Batch pack path. "
                                          "Must exist and must be empty. "
                                          "(Mandatory)")

        namespace = argument_parser.parse_args()
        self._scan_key_values = namespace.scan_key_value
        for scan_key_value in self._scan_key_values:
            if len(scan_key_value) < 2:
                msg = f"KEY without following VALUES: {scan_key_value}\n"
                util.stop(msg)
        self._scan_formats = namespace.scan_format
        self._part_size = util.make_int_ge(namespace.part_size, 1)
        self._batch_pack_path = util.make_item_path_exist_empty(namespace.batch_pack_path)

    def make_scan_parts(self, scan_format):
        # Replace each KEY with its VALUES list
        scan_parts = [scan_format]
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
        return scan_parts

    def generate(self):
        # Scan Products.
        scan_products = []
        for scan_format in self._scan_formats:
            scan_parts = self.make_scan_parts(scan_format)
            scan_product = itertools.product(*scan_parts)
            scan_products.append(scan_product)

        # Expand.
        part_number = 0
        current_part_size = 0
        fqdn_handle = None
        for scan_product in scan_products:
            for parts in scan_product:
                if fqdn_handle is not None:
                    if current_part_size == self._part_size:
                        fqdn_handle.close()
                        fqdn_handle = None
                if fqdn_handle is None:
                    part_number = part_number + 1
                    fqdn_file_name = f"{part_number:06}.fqdn.txt"
                    fqdn_path_file = os.path.join(self._batch_pack_path, fqdn_file_name)
                    fqdn_handle = open(fqdn_path_file, "w")
                    current_part_size = 0

                domain = "".join(parts)
                fqdn_handle.write(f"{domain}\n")
                current_part_size = current_part_size + 1
        fqdn_handle.close()

    def start(self):
        self.process_arguments()
        self.generate()

if __name__ == '__main__':
    main = Main()
    main.start()
