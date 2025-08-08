Script to check a batch pack for availability against database.

Dependencies:
See common DEPENDENCIES.txt

Purpose:
A batch pack contains a set of domain names, to be checked for availability
against a provided domains database. This script performs the check, through
separate threads, for improved performance.

Usage:
source $HOME/virtpython/bin/activate
python check_batch_pack.py --help
