Infrastructure for a minimal domain database.

Dependencies:
See common DEPENDENCIES.txt

Purpose:
Provide a basic view of whether or nor a domain name is registered, retaining
only its earliest (start) and latest (until) known registration dates. While
basic, this provides expedient (time and space efficient) lookup for whether
or not a domain name is registered.

Setup:
See SETUP.txt

Usage:
python3 -m venv $HOME/virtpython

First, from a zone file, create a load zone file pack:
python zone_file_to_load_zone_file_pack.py --help

Second, transfer the load zone file pack into the domains database:
python load_zone_file_pack_to_domains_database.py --help
