#!/bin/bash

set -e 

if [ -z "${LDAP_SYNC_INTERVAL}" ]; then
  echo "LDAP_SYNC_INTERVAL not set, defaulting to 60 seconds!"
  LDAP_SYNC_INTERVAL=60
fi

while /bin/true; do
  /srv/taiga/taiga-back/ldap-sync.py
  sleep ${LDAP_SYNC_INTERVAL}
done
