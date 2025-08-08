Script to create a batch pack, from a scan description.

Dependencies:
See common DEPENDENCIES.txt

Purpose:
A batch pack contains a set of domain names, to be checked for availability
against a provided domains database. The scan description describes a set of
domain names, through a concisely described, algorithmically expanded pattern,
which is used to generate an interesting batch pack for assessment.

Usage:
source $HOME/virtpython/bin/activate
python scan_to_batch_pack.py --help
