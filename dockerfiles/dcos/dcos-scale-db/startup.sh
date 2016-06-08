usermod -u $NFS_POSTGRES_UID postgres
groupmod -g $NFS_POSTGRES_GID postgres

chown postgres:postgres /var/lib/pgsql/data

/usr/bin/postgresql-setup initdb
chown -R postgres:postgres /var/run/postgresql

sed -i 's/scaledb/'$SCALE_DB_NAME'/g'  /postgres_init.sh
sed -i 's/scaleuser/'$SCALE_DB_USER'/g'  /postgres_init.sh
sed -i 's/scalepassword/'$SCALE_DB_PASS'/g'  /postgres_init.sh

chown -R postgres:postgres /var/lib/pgsql/data/* &> /dev/null
chown -R postgres /var/lib/pgsql/data/* &> /dev/null

su postgres -c '/usr/bin/postgres -D /var/lib/pgsql/data -p 5432 &'

#Set up Database
sleep 2
chmod +x /postgres_init.sh
/postgres_init.sh

sed -i 's/localhost/0.0.0.0/' /var/lib/pgsql/data/postgresql.conf
sed -i 's/#listen_addresses/listen_addresses/' /var/lib/pgsql/data/postgresql.conf
sed -i '/ident/d' /var/lib/pgsql/data/pg_hba.conf
grep -q '0.0.0.0' /var/lib/pgsql/data/pg_hba.conf && echo 'Already Added' || echo "host    all             all             0.0.0.0/0               md5" >> /var/lib/pgsql/data/pg_hba.conf

kill -9 $(ps -ef | grep 5432 | egrep -v grep | awk '{ print $2 }')

su postgres -c '/usr/bin/postgres -D /var/lib/pgsql/data -p 5432'

#touch /var/lib/pgsql/initdb.log
#tail -f /var/lib/pgsql/initdb.log
