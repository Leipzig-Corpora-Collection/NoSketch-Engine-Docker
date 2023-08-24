#!/bin/bash

# If no params then start the server,
# else run the specified command from /usr/local/bin
if [ $# -eq 1 ]; then
    # Shibboleth requires these to be set properly!
    SERVER_NAME=${SERVER_NAME:="https://cql.wortschatz-leipzig.de/"}
    SERVER_ALIAS=${SERVER_ALIAS:="cql.wortschatz-leipzig.de"}
    CITATION_LINK=${CITATION_LINK:="https://wortschatz-leipzig.de/"}
    echo "Starting server with name (${SERVER_NAME}) and alias (${SERVER_ALIAS})."
    echo 'You can override these values with ${SERVER_NAME} and ${SERVER_ALIAS} environment variables.'
    sed -i "s#SERVER_NAME_PLACEHOLDER#${SERVER_NAME}#" /etc/apache2/sites-enabled/000-default.conf
    sed -i "s#SERVER_ALIAS_PLACEHOLDER#${SERVER_ALIAS}#" /etc/apache2/sites-enabled/000-default.conf
    sed -i "s#CITATION_LINK_PLACEHOLDER#${CITATION_LINK}#" /var/www/crystal/bundle.js
    #
    chown -R www-data:www-data /var/lib/bonito/cache
    # run apache
    /usr/sbin/apache2ctl -D FOREGROUND
else
    shift
    /usr/local/bin/$@
fi
