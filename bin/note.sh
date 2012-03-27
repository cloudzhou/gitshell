#!/bin/bash

apt-get install:
    automake build-essential flex git libmysqlclient-dev libpcre3 libpcre3-dev libpython2.7 libssl0.9.8 libssl-dev libtool libzip1 libzip-dev mysql mysql-client mysql-server pip python-dev python-pip python-pyasn1 libcurl4-openssl-dev tcl8.5 

**run env**
haproxy:
    make TARGET=linux26 && sudo make install    
    /usr/local/sbin/haproxy
    create /etc/haproxy.cfg
openssh-gitshell-patch:
    add libcurl support, auth and distributed
    sudo useradd sshd -m -s /sbin/nologin -d /var/empty/sshd
    make && rm -rf /opt/gitshell/run/openssh && make install && \
    sed -i 's/#Port 22/Port 222/' /opt/gitshell/run/openssh/etc/sshd_config && \
    sudo  /opt/gitshell/run/openssh/sbin/sshd  -dddd
nginx:
    --without-mail_pop3_module --without-mail_imap_module --without-mail_smtp_module --prefix=/opt/gitshell/run/nginx \
    --with-http_gzip_static_module --with-http_stub_status_module --with-http_ssl_module
uwsgi:
    make && cp 
redis:
    two redist instances, 1) for sql select cache, 2) for object cache
    make && make test 
    cd ./utils/ && sudo ./install_server.sh
    edit /etc/redis/6379.conf and change db dir to /opt/gitshell/run/redis/6379
django:
    python setup.py install
mysql:
    as ubuntu default, apt get install

**web app**
gitshell:
    main web app for front user
gitshell-rpc
    rpc for back end used, do curl request
gitshell-standalone
    gitshell standalone consume mysql trigger
