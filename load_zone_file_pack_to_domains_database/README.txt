Overview:
Transfer a load zone file pack into a domains database.

Dependencies:
See common DEPENDENCIES.txt

Purpose:
Update the minimal domain database, based on a provided zone file pack.

Setup:
See SETUP.txt

Usage:
python3 -m venv $HOME/virtpython

First, from a zone file, create a load zone file pack:
python zone_file_to_load_zone_file_pack.py --help

Second, transfer the load zone file pack into the domains database:
python load_zone_file_pack_to_domains_database.py --help
