Script to create a scan file (an algorithmically generated list of domain
names). Further scripts may be used to process the scan file.

Dependencies:
See common DEPENDENCIES.txt

Purpose:
A scan file may be used to measure the domains database. It is generally
understood that every LLLL.com is registered, and thus any detected
unregistered LLLL.com is likely a deficiency of the database.

Usage:
source $HOME/virtpython/bin/activate
python download_zone_file_to_pack.py --help

