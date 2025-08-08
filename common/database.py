# Internal
import os
import sys
import datetime

# External
import mariadb

# Local
import util

#-------------------------------------------------------------------------------

def make_none_date_sql(item_none_date):
    if item_none_date is None:
        none_date_sql = None
    else:
        none_date_sql = item_none_date.isoformat()
    return none_date_sql

#-------------------------------------------------------------------------------

class DomainsDB():

    # Sources
    ZONE_FILE="ZONE_FILE"
    RDAP="RDAP"

    def __init__(self,
                 database_user,
                 database_password):
        try:
            self._con = mariadb.connect(user=database_user,
                                        password=database_password,
                                        database="domains")
        except mariadb.Error as e:
            msg=f"Error connecting to database: {e}\n"
            util.stop(msg)
        self._con.autocommit = False
        self._cur = self._con.cursor()
        self._tld_label_to_tld_id = {}
        self._tld_id_to_captures = {}
        self._update_tld_label_to_tld_id()

    def _update_tld_label_to_tld_id(self):
        self._tld_label_to_tld_id = {}
        self._cur.execute("SELECT tld.tld_label, tld.tld_id "
                          "FROM tld;")
        self._con.commit()
        result_tuples = list(self._cur)
        for result_tuple in result_tuples:
            tld_label = result_tuple[0]
            tld_id = result_tuple[1]
            self._tld_label_to_tld_id[tld_label] = tld_id 

    def _update_tld_id_to_captures(self):
        self._tld_id_to_captures = {}
        self._cur.execute("SELECT zone_file.tld_id, zone_file.capture "
                          "FROM zone_file;")
        self._con.commit()
        result_tuples = list(self._cur)
        for result_tuple in result_tuples:
            tld_id = result_tuple[0]
            capture_date = result_tuple[1]
            if 

            self._tld_label_to_tld_id[tld_label] = tld_id 


    def _find_none_sld_id(self, req_sld_label):
        self._cur.execute("SELECT sld.sld_id "
                          "FROM sld "
                          "WHERE sld.sld_label=?;",
                          (req_sld_label,))
        self._con.commit()
        result_tuples = list(self._cur)
        if len(result_tuples) == 0:
            sld_id = None
        elif len(result_tuples) == 1:
            sld_id = result_tuples[0][0]
        else:
            msg = f"SQL: Unexpected result: {result_tuples}\n"
            util.stop(msg)
        return sld_id

    def _make_sld_id(self, req_sld_label):
        sld_id = self._find_none_sld_id(req_sld_label)
        if sld_id is None:
            self._cur.execute("INSERT INTO sld (sld.sld_label) "
                              "VALUES (?);",
                              (req_sld_label,))
            self._con.commit()
            sld_id = self._cur.lastrowid
        return sld_id

    def _find_tld_id(self, req_tld_label):
        if req_tld_label in self._tld_label_to_tld_id.keys():
            tld_id = self._tld_label_to_tld_id[req_tld_label]
        else:
            tld_id = None
        return tld_id

    def _make_tld_id(self, req_tld_label):
        if req_tld_label not in self._tld_label_to_tld_id.keys():
            self._cur.execute("INSERT INTO tld (tld.tld_label) "
                              "VALUES (?);",
                              (req_tld_label,))
            self._con.commit()
            self._update_tld_label_to_tld_id()
        return self._tld_label_to_tld_id[req_tld_label]

    def inspect_fqdn(self,
                     req_sld_label,
                     req_tld_label):
        tld_id = self._find_tld_id(req_tld_label)
        if tld_id is None:
            msg = f"No id for tld: {req_tld_label}\n"
            util.stop(msg)

        # Achieve via single select for performance.
        self._cur.execute("SELECT fqdn.sources, fqdn.start, fqdn.until "
                          "FROM fqdn "
                          "INNER JOIN sld "
                          "ON fqdn.sld_id = sld.sld_id "
                          "WHERE sld.sld_label=? AND fqdn.tld_id=?;",
                          (req_sld_label, tld_id))
        self._con.commit()
        result_tuples = list(self._cur)
        if len(result_tuples) == 0:
            result = None
        elif len(result_tuples) == 1:
            now_sources = result_tuples[0][0].split(",")
            now_start_none_date = result_tuples[0][1]
            now_until_none_date = result_tuples[0][2]
            result = (now_sources, now_start_none_date, now_until_none_date)
        return result

    def update_fqdn(self,
                    req_source,
                    req_sld_label,
                    req_tld_label,
                    req_start_none_date,
                    req_until_none_date):
        sld_id = self._make_sld_id(req_sld_label)
        tld_id = self._make_tld_id(req_tld_label)
        self._cur.execute("SELECT fqdn.sources, fqdn.start, fqdn.until "
                          "FROM fqdn "
                          "WHERE fqdn.sld_id=? AND fqdn.tld_id=?;",
                          (sld_id, tld_id))
        self._con.commit()
        result_tuples = list(self._cur)
        if len(result_tuples) == 0:
            # Mandate: Update.
            self._cur.execute("INSERT INTO fqdn (fqdn.sld_id, fqdn.tld_id, fqdn.sources, fqdn.start, fqdn.until) "
                              "VALUES (?, ?, ?, ?, ?);",
                              (sld_id,
                               tld_id,
                               req_source,
                               make_none_date_sql(req_start_none_date),
                               make_none_date_sql(req_until_none_date)))
            self._con.commit()
        elif len(result_tuples) == 1:
            now_sources = result_tuples[0][0].split(",")
            now_start_none_date = result_tuples[0][1]
            now_until_none_date = result_tuples[0][2]
            update = False

            # Assess: Sources.
            if req_source in now_sources:
                sources = now_sources 
            else:
                sources = now_sources + [req_source]
                update = True

            # Assess: Start to Until.
            (start_none_date, until_none_date) = util.make_start_until_none_date_tuple([req_start_none_date,
                                                                                        req_until_none_date,
                                                                                        now_start_none_date,
                                                                                        now_until_none_date])
            if ((start_none_date != now_start_none_date) or
                (until_none_date != now_until_none_date)):
                update = True

            # Potential: Update.
            if update:
                self._cur.execute("UPDATE fqdn "
                                  "SET fqdn.sources=?, fqdn.start=?, fqdn.until=? "
                                  "WHERE fqdn.sld_id=? AND fqdn.tld_id=?;",
                                  (",".join(sources),
                                   make_none_date_sql(start_none_date),
                                   make_none_date_sql(until_none_date),
                                   sld_id,
                                   tld_id))
                self._con.commit()
        else:
            msg = f"SQL: Unexpected result: {result_tuples}\n"
            util.stop(msg)
