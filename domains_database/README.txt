Infrastructure for a minimal domain database.

Dependencies:
See common DEPENDENCIES.txt

Purpose:
Provide a basic view of whether or nor a domain name is registered, retaining
only its earliest and latest known registration dates. While basic, this
provides expedient (time and space efficient) lookup for whether or not a
domain name is registered.

Setup:
See SETUP.txt

Usage:
python3 -m venv $HOME/virtpython

First, from a zone file, create a pack:
python zone_file_to_pack.py --help

Second, transfer that pack into the database:
python pack_to_database.py --help
