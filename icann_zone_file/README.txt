Script to download ICANN zone files.

Dependencies:
See common DEPENDENCIES.txt

Purpose:
The ICANN protocol is defined here:
https://github.com/icann/czds-api-client-java/blob/master/docs/ICANN_CZDS_api.pdf

To help download the data successfully, even when the connection is slow and
unstable, the download is achieved through separate threads, in distinct
chunks, with some logging to assist in any manual recovery.

The expectation is that multiple downloads will be retained and maintained in
a provided target path.

Usage:
python3 -m venv $HOME/virtpython
python zone_file_to_archive_pack.py --help
