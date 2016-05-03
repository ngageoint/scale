FROM centos
MAINTAINER Daniel E. Roessner <droessne@ball.com>

RUN rpm -ivh https://download.postgresql.org/pub/repos/yum/9.2/redhat/rhel-7-x86_64/pgdg-centos92-9.2-2.noarch.rpm https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

RUN yum -y --nogpgcheck install postgresql postgis postgresql-server

VOLUME /var/lib/pgsql/data

EXPOSE 5432

ENV SCALE_DB_NAME='scale' \
    SCALE_DB_USER='scale' \
    SCALE_DB_PASS='scale' \
    NFS_POSTGRES_UID='26' \
    NFS_POSTGRES_GID='26'

RUN sed -i 's/PGDATA=`systemctl.*/PGDATA="\/var\/lib\/pgsql\/data"/' /usr/bin/postgresql-setup \
 && sed -i 's/PGPORT=`systemctl.*/PGPORT="5432"/' /usr/bin/postgresql-setup \
 && sed -i "/\ sed\ /d"  /usr/bin/postgresql-setup 

ADD startup.sh /startup.sh 
ADD postgres_init.sh /postgres_init.sh
RUN chmod +x /startup.sh /postgres_init.sh

CMD /startup.sh
