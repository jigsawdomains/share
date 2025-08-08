Overview:
Parse a zone file into a load zone file pack, ready for transfer to database.

Dependencies:
See common DEPENDENCIES.txt

Purpose:
Parse a zone file, to identify all its unique contained domain names, and
present as a load zone file pack. The load zone file pack format supports the
transfer to a database in multiple parts via multiple cores.

Setup:
See SETUP.txt

Usage:
python3 -m venv $HOME/virtpython
python zone_file_to_load_zone_file_pack.py --help
