# From official Debian 11 Bullseye image pinned by its name bullseye-slim
FROM debian:bullseye-slim

# noske versions
ARG MANATEE_OPEN_VERSION=2.223.6
ARG BONITO_OPEN_VERSION=5.63.9
ARG GDEX_VERSION=4.12
ARG CRYSTAL_OPEN_VERSION=2.142


# Install noske dependencies
## deb packages
RUN apt-get update && \
    apt-get install -y \
        apache2 \
        build-essential \
        libltdl-dev \
        libpcre++-dev \
        bison \
        libsass-dev \
        python3-dev \
        python3-pip \
        python3-setuptools \
        libcap-dev \
        file \
        swig && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install python-prctl openpyxl


# Enable apache CGI and mod_rewrite
RUN a2enmod cgi rewrite


# Install noske components
WORKDIR /tmp/noske_files/

## Manatee
ADD noske_files/manatee-open-${MANATEE_OPEN_VERSION}.tar.gz /tmp/noske_files/
RUN cd manatee* && \
    ./configure --with-pcre && \
    make && \
    make install

## Bonito
ADD noske_files/bonito-open-${BONITO_OPEN_VERSION}.tar.gz /tmp/noske_files/
### HACKs + overrides for auth
COPY noske_files/bonito-open-${BONITO_OPEN_VERSION}/. /tmp/noske_files/bonito-open-${BONITO_OPEN_VERSION}/
RUN cd bonito* && \
    ./configure && \
    make && \
    make install && \
    ./setupbonito /var/www/bonito /var/lib/bonito && \
    chown -R www-data:www-data /var/lib/bonito

## GDEX
ADD noske_files/gdex-${GDEX_VERSION}.tar.gz /tmp/noske_files/
RUN cd gdex* && \
    sed -i "s/<version>/${GDEX_VERSION}/g" setup.py && \
    ./setup.py build && \
    ./setup.py install

## Crystal
ADD noske_files/crystal-open-${CRYSTAL_OPEN_VERSION}.tar.gz /tmp/noske_files/
### HACKs + overrides (auth, UI, ...)
COPY noske_files/crystal-open-${CRYSTAL_OPEN_VERSION}/. /tmp/noske_files/crystal-open-${CRYSTAL_OPEN_VERSION}/
RUN cd crystal-* && \
    make && \
    make install VERSION=${CRYSTAL_OPEN_VERSION}


# Remove unnecessary files and create symlink for utility command
RUN rm -rf /var/www/bonito/.htaccess /tmp/noske_files/* && \
    ln -sf /usr/bin/htpasswd /usr/local/bin/htpasswd


# Copy config files (These files contain placeholders replaced in entrypoint.sh according to environment variables)
COPY conf/*.sh /usr/local/bin/
COPY conf/run.cgi /var/www/bonito/run.cgi
COPY conf/000-default.conf /etc/apache2/sites-enabled/000-default.conf


### These files should be updated through environment variables (HTACCESS,HTPASSWD,PUBLIC_KEY,PRIVATE_KEY)
# but uncommenting the lines below enable creation of a custom image with secrets included
# COPY secrets/htaccess /var/www/.htaccess
# COPY secrets/htpasswd /var/lib/bonito/htpasswd

### HACK4: Link site-packages to dist-packages to help Python find these packages
#          (e.g. creating subcorpus and keywords on it -> calls mkstats with popen which calls manatee internally)
RUN ln -s /usr/local/lib/python3.9/site-packages/ /usr/lib/python3/dist-packages/bonito && \
    ln -s /usr/local/lib/python3.9/site-packages/manatee.py /usr/lib/python3/dist-packages/manatee.py && \
    ln -s /usr/local/lib/python3.9/site-packages/_manatee.so /usr/lib/python3/dist-packages/_manatee.so && \
    ln -s /usr/local/lib/python3.9/site-packages/_manatee.a /usr/lib/python3/dist-packages/_manatee.a && \
    ln -s /usr/local/lib/python3.9/site-packages/_manatee.la /usr/lib/python3/dist-packages/_manatee.la

# Start the container
ENTRYPOINT ["/usr/local/bin/entrypoint.sh", "$@"]
EXPOSE 80
