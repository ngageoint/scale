echo "CREATE USER scaleuser WITH PASSWORD 'scalepassword';" > /tmp/user.sql
echo "CREATE DATABASE scaledb;" >> /tmp/user.sql
echo "GRANT ALL PRIVILEGES ON DATABASE scaledb to scaleuser;" >> /tmp/user.sql

su postgres -c "/usr/bin/psql -f /tmp/user.sql"

su postgres -c "/usr/bin/psql -d scaledb -f /usr/share/pgsql/contrib/postgis-64.sql"
su postgres -c "/usr/bin/psql -d scaledb -f /usr/share/pgsql/contrib/postgis-2.0/spatial_ref_sys.sql"
su postgres -c "/usr/bin/psql -d scaledb -f /usr/share/pgsql/contrib/postgis-2.0/postgis_comments.sql"
su postgres -c "/usr/bin/psql -d scaledb -f /usr/share/pgsql/contrib/postgis-2.0/rtpostgis.sql"
su postgres -c "/usr/bin/psql -d scaledb -f /usr/share/pgsql/contrib/postgis-2.0/raster_comments.sql"
su postgres -c "/usr/bin/psql -d scaledb -f /usr/share/pgsql/contrib/postgis-2.0/topology.sql"
su postgres -c "/usr/bin/psql -d scaledb -f /usr/share/pgsql/contrib/postgis-2.0/topology_comments.sql"
su postgres -c "/usr/bin/psql -d scaledb -f /usr/share/pgsql/contrib/postgis-2.0/legacy.sql"

