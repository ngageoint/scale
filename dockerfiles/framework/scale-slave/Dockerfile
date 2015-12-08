FROM scale:3
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

USER root
RUN rpm -i http://repos.mesosphere.io/el/7/noarch/RPMS/mesosphere-el-repo-7-1.noarch.rpm \
 && yum -y install mesos-0.24.1 docker \
 && yum clean all

CMD ["/usr/sbin/mesos-slave"]

ENV MESOS_WORK_DIR /tmp/mesos
ENV MESOS_CONTAINERIZERS docker,mesos

# https://mesosphere.github.io/marathon/docs/native-docker.html
ENV MESOS_EXECUTOR_REGISTRATION_TIMEOUT 5mins

VOLUME /tmp/mesos

COPY entrypoint.sh /

ENTRYPOINT ["/entrypoint.sh"]
