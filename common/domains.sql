CREATE DATABASE domains;
USE domains;

CREATE TABLE zone_file (
    tld_id TINYINT UNSIGNED NOT NULL,
    capture DATE NOT NULL,
    PRIMARY KEY (tld_id, capture)
);

CREATE TABLE sld (
    sld_label VARCHAR(63) NOT NULL,
    sld_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    PRIMARY KEY (sld_label),
    UNIQUE KEY (sld_id)
);

CREATE TABLE tld (
    tld_label VARCHAR(63) NOT NULL,
    tld_id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    PRIMARY KEY (tld_label),
    UNIQUE KEY (tld_id)
);

# oldest: Earliest observed registered date. May be NULL.
# newest: Latest observed registered date. May be NULL.
CREATE TABLE fqdn (
    sld_id INT UNSIGNED NOT NULL,
    tld_id TINYINT UNSIGNED NOT NULL,
    sources SET('ZONE_FILE', 'RDAP') NOT NULL,
    oldest DATE NULL,
    newest DATE NULL,
    PRIMARY KEY (sld_id, tld_id)
);

EXIT;
