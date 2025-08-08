# Share

Suite of tools to support domain name related investigations. Developed
alongside [Jigsaw Domains](https://www.jigsawdomains.com). Deliberately framed
as a set of distinct interacting command line tools, to permit and encourage a
range of experiments and investigations. Interesting use cases, general
commentary, or simply defect reports, are all welcome!

## Dependencies

### Operating System

Linux, and to a lesser extent, Debian 12, is assumed throughout.

### Packages

Install package dependencies as follows:

```
sudo apt-get update
sudo apt-get install python3
sudo apt-get install python3-venv
sudo apt-get install python3-dev
sudo apt-get install gcc
sudo apt-get install mariadb-server
sudo apt-get install mariadb-client
sudo apt-get install rdap
```

### Virtual Python

Install and configure Virtual Python as follows:

```
python3 -m venv $HOME/virtpython
$HOME/virtpython/bin/pip install mariadb
```

## Database

The mariadb (Maria Database) is assumed. 

### Setup

The following setup is adopted. The expectation is that the database will be
for local use only (not Internet facing), and thus simple credentials are
adopted.

```
sudo mysql_secure_installation 

Enter current password for root (enter for none): <enter>
Switch to unix_socket authentication [Y/n] n
Change the root password? [Y/n] Y
maria
maria
Remove anonymous users? [Y/n] Y
Disallow root login remotely? [Y/n] Y
Remove test database and access to it? [Y/n] Y
Reload privilege tables now? [Y/n] Y
```

### Configure

The database is configured through the following file:

```
/etc/mysql/mariadb.conf.d/50-server.cnf
```

Consider adjusting to use of larger portion of your system RAM. Select a value
that best fits your system and expected usage.

```
[mysqld]
innodb_buffer_pool_size = 16G
```

### Database

Within a clone of this repository, execute the following, to launch a root
database session:

```
mariadb --user root --password=maria
```

A single local user account is used throughout, with username as `jd` and
password as `jd1234`. Within the root database session, create the local user
account as follows:

```
source ./common/user.sql
```

A small set of database schemas are used throughout. Within the root database
session, create these database schemas as follows:

```
source ./common/domains.sql
```

## Tools

Each tool is a standalone python program. The tools make use of common
capabilities, and share the same operational style. Most tools operate with a
path, known as a pack, which holds its associated structured data.

## download_zone_file_to_zone_files_pack

The ICANN CZDS (Centralized Zone Data Service) is defined within
[ICANN_CZDS_api.pdf](https://github.com/icann/czds-api-client-java/blob/master/docs/ICANN_CZDS_api.pdf).
Those with an ICANN account may use the ICANN CZDS to download Zone Files for
a set of TLDs (Top Level Domains).

This tool uses the ICANN CZDS, to download the current Zone File for a
selected TLD. The download is achieved through distinct chunks, executed on
separate cores, for performance, and efficient recovery.

For usage:

```
source $HOME/virtpython/bin/activate
python download_zone_file_to_zone_files_pack.py --help
```




## load_zone_file_pack_to_domains_database




## rdap_batch_pack
## scan_to_batch_pack
## zone_file_to_load_zone_file_pack

