# The builder image
## From official Debian 12 Bookworm image pinned by its name bookworm-slim
FROM debian:bookworm-slim AS build

# noske source versions
ARG MANATEE_OPEN_VERSION=2.225.8
ARG BONITO_OPEN_VERSION=5.71.15
ARG GDEX_VERSION=4.13.2
ARG CRYSTAL_OPEN_VERSION=2.166.4

# Install noske dependencies
## deb packages
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        libltdl-dev \
        libpcre3-dev \
        bison \
        libsass-dev \
        python3-dev \
        python3-setuptools \
        libcap-dev \
        file \
        swig \
        debmake \
        javahelper \
        autoconf-archive \
        dh-python && \
    rm -rf /var/lib/apt/lists/*

# Install noske components
WORKDIR /tmp/noske_files/

### NOTE: ADDing *.tar.gz files automatically extracts them, we then overlay our changes 
###        Native (-n) debmake will then ignore the missing *.tar.gz source archive.

## Manatee
ADD noske_files/manatee-open-${MANATEE_OPEN_VERSION}.tar.gz /tmp/noske_files/
### HACKs + overrides (fixes)
COPY noske_files/manatee-open-${MANATEE_OPEN_VERSION}/. /tmp/noske_files/manatee-open-${MANATEE_OPEN_VERSION}/
RUN cd manatee* && \
    debmake -n && \
    EDITOR=/bin/true dpkg-source -q --commit . fix_build && \
    echo -e 'override_dh_auto_configure:\n\tdh_auto_configure -- \\\n\t\t--with-pcre' >> ./debian/rules && \
    debuild -d -us -uc

## Bonito
ADD noske_files/bonito-open-${BONITO_OPEN_VERSION}.tar.gz /tmp/noske_files/
### HACKs + overrides for auth
COPY noske_files/bonito-open-${BONITO_OPEN_VERSION}/. /tmp/noske_files/bonito-open-${BONITO_OPEN_VERSION}/
RUN cd bonito* && \
    debmake -n -b":python3" && \
    touch AUTHORS ChangeLog NEWS && \
    echo -e '#!/bin/bash\n#DEBHELPER#\n' > debian/postinst && \
    echo '/usr/bin/setupbonito /var/www/bonito /var/lib/bonito' >> debian/postinst && \
    echo 'chown -R www-data:www-data /var/lib/bonito' >> debian/postinst && \
    echo '# Remove unnecessary files, create symlink for utility command, and create dummy auth (login) folder' >> debian/postinst && \
    echo 'rm -rf /var/www/bonito/.htaccess' >> debian/postinst && \
    echo 'ln -sf /usr/bin/htpasswd /usr/local/bin/htpasswd' >> debian/postinst && \
    echo 'mkdir /var/www/auth' >> debian/postinst && \
    debuild -d -us -uc

## GDEX
ADD noske_files/gdex-${GDEX_VERSION}.tar.gz /tmp/noske_files/
RUN cd gdex* && \
    debmake -n -b":python3" && \
    sed -i "s/<version>/${GDEX_VERSION}/g" setup.py && \
    EDITOR=/bin/true dpkg-source -q --commit . fix_build && \
    echo -e 'override_dh_auto_test:\n\techo "Disabled autotest"' >> debian/rules && \
    debuild -d -us -uc

## Crystal
ADD noske_files/crystal-open-${CRYSTAL_OPEN_VERSION}.tar.gz /tmp/noske_files/
### HACKs + overrides (auth, UI, ...)
COPY noske_files/crystal-open-${CRYSTAL_OPEN_VERSION}/. /tmp/noske_files/crystal-open-${CRYSTAL_OPEN_VERSION}/
RUN cd crystal-* && \
    debmake -n && \
    touch debian/changelog && \
    sed -e 's/npm install/npm install --unsafe-perm=true/' \
        -e 's/VERSION ?= `git describe --tags --always`/VERSION='"${CRYSTAL_OPEN_VERSION}"'/' \
        -i Makefile && \
    EDITOR=/bin/true dpkg-source -q --commit . fix_build && \
    debuild -d -us -uc


# ---------------------------------------------------------------------------
# The actual image
## From official Debian 12 Bookworm image pinned by its name bookworm-slim
FROM debian:bookworm-slim AS run

## Install noske dependencies
### deb packages
RUN apt-get update && \
    apt-get install -y \
        apache2 \
        python3-prctl \
        python3-openpyxl && \
    rm -rf /var/lib/apt/lists/*

## Enable apache CGI and mod_rewrite
RUN a2enmod cgi rewrite headers

## Copy deb packages built in the previous step
COPY --from=build /tmp/noske_files/*.deb /tmp/noske_files/

## Install noske packages
RUN apt-get update && \
    apt-get install -y /tmp/noske_files/*.deb && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/noske_files/*

# Copy config files (These files contain placeholders replaced in entrypoint.sh according to environment variables)
COPY conf/*.sh /usr/local/bin/
COPY conf/run.cgi /var/www/bonito/run.cgi
COPY conf/robots.txt /var/www/robots.txt
COPY conf/000-default.conf /etc/apache2/sites-enabled/000-default.conf

### This file should be updated through docker volume mappings
# but uncommenting the line below enable creation of a custom image with secrets included
# COPY secrets/htpasswd /var/lib/bonito/htpasswd

### HACKx: Link site-packages to dist-packages to help Python find these packages
#          (e.g. creating subcorpus and keywords on it -> calls mkstats with popen which calls manatee internally)
#         TODO Seems to be a bug in the build system as manatee should be in .../site-packages/manatee folder
RUN ln -s /usr/lib/python3.11/site-packages/manatee.py  /usr/lib/python3/dist-packages/manatee.py && \
    ln -s /usr/lib/python3.11/site-packages/_manatee.so /usr/lib/python3/dist-packages/_manatee.so && \
    ln -s /usr/lib/python3.11/site-packages/_manatee.a  /usr/lib/python3/dist-packages/_manatee.a && \
    ln -s /usr/lib/python3.11/site-packages/_manatee.la /usr/lib/python3/dist-packages/_manatee.la

# Start the container
ENTRYPOINT ["/usr/local/bin/entrypoint.sh", "$@"]
EXPOSE 80
