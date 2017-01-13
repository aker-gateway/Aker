FROM docker.io/centos:7
RUN yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
RUN yum install -y python2-paramiko python-configparser python-urwid openssh-server passwd
RUN mkdir -p /bin/aker && mkdir /var/run/sshd
COPY ./*py /bin/aker/
COPY ./aker.ini /etc
RUN chmod 755 /bin/aker/aker.py
RUN ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -N '' 
RUN echo "Match Group *,!root" >> /etc/ssh/sshd_config
RUN echo "    ForceCommand /bin/aker/aker.py" >> /etc/ssh/sshd_config
ENTRYPOINT ["/usr/sbin/sshd", "-D"]
