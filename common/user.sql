CREATE USER "jd"@"localhost" IDENTIFIED BY "jd1234";
GRANT CREATE ON *.* TO "jd"@"localhost";
GRANT INSERT ON *.* TO "jd"@"localhost";
GRANT SELECT ON *.* TO "jd"@"localhost";
GRANT UPDATE ON *.* TO "jd"@"localhost";
FLUSH PRIVILEGES;
EXIT;
