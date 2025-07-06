Overview:
Download ICANN zone files into a zone files pack.

Dependencies:
See common DEPENDENCIES.txt

Purpose:
The ICANN protocol is defined here:
https://github.com/icann/czds-api-client-java/blob/master/docs/ICANN_CZDS_api.pdf

To help download the data successfully, even when the connection is slow and
unstable, the download is achieved through separate cores, in distinct chunks,
with logging to assist any manual recovery. The expectation is that multiple
downloads will be retained and maintained in a provided zone files pack.

Usage:
source $HOME/virtpython/bin/activate
python download_zone_file_to_zone_files_pack.py --help
