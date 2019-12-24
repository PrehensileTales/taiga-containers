FROM fedora:31 as stage0

ARG taiga_back_version=5.0.2
ARG taiga_front_version=5.0.4

RUN dnf -y install python3-virtualenvwrapper python3-pip python3-devel libxml2-devel libxslt-devel openssl-devel libffi-devel git gcc freetype-devel libjpeg-turbo-devel libpng-devel zlib-devel openldap-devel npm && \
    mkdir /srv/taiga && cd /srv/taiga && \
    git clone --single-branch --branch ${taiga_back_version} https://github.com/taigaio/taiga-back.git taiga-back && \
    cd /srv/taiga/taiga-back && \
    rm -rf .git && \
    virtualenv -p /usr/bin/python3 taiga && \
    source taiga/bin/activate && \
    pip install -r requirements.txt && \
    pip install django-environ && \
    pip install python-ldap && \
    cd /srv/taiga && \
    git clone --single-branch --branch ${taiga_front_version}-stable https://github.com/taigaio/taiga-front-dist.git taiga-front && \
    rm -rf taiga-front/.git && \
    cd /srv/taiga/ && \
    git clone https://github.com/robrotheram/taiga-contrib-openid-auth.git taiga-contrib-openid-auth && \
    cd taiga-contrib-openid-auth && \
    git checkout ce3a0ac && \
    cd back && \
    pip install -e . && \
    cd ../front && \
    npm install -e gulp && \
    npm install && \
    node_modules/gulp/bin/gulp.js build && \
    mkdir -p /srv/taiga/taiga-front/dist/plugins && \
    mv dist /srv/taiga/taiga-front/dist/plugins/openid-auth && \
    cd .. && \
    rm -rf front && \
    cd /srv/taiga/ && \
    git clone https://github.com/taigaio/taiga-events.git taiga-events && \
    cd taiga-events && \
    git checkout 2de073c && \
    rm -rf .git && \
    npm install

FROM fedora:31
RUN dnf -y install python3-virtualenvwrapper libxml2 libxslt openssl-libs libffi freetype libjpeg-turbo libpng zlib nc postgresql gettext httpd python3-mod_wsgi openldap npm libxcrypt-compat && dnf clean all && \
    rm /etc/httpd/conf.d/*.conf && \
    mkdir -p /srv/taiga/media 
COPY --from=stage0 /srv/taiga/ /srv/taiga/
COPY local.py /srv/taiga/taiga-back/settings
COPY celery.py /srv/taiga/taiga-back/settings
COPY wsgi.py /srv/taiga/taiga-back/taiga
COPY ldap-sync.py /srv/taiga/taiga-back
COPY generate-frontend-config.py /srv/taiga
COPY apache-conf /etc/httpd/conf.d/00taiga.conf

RUN cd /srv/taiga/taiga-back && \
    source taiga/bin/activate && \
    export DJANGO_SECRET_KEY=secret && \
    export DJANGO_DB_NAME=unset && \
    export DJANGO_DB_USER=unset && \
    unset TAIGA_CELERY_ENABLED && \
    python manage.py compilemessages && \
    python manage.py collectstatic --noinput

VOLUME /srv/taiga/media
EXPOSE 8080/tcp

ENV DEBUG=False \
    DJANGO_DB_NAME=taiga \
    DJANGO_DB_USER=taiga \
    DJANGO_DB_PASSWORD=taiga \
    DJANGO_DB_HOST=localhost \
    DJANGO_DB_PORT=5432 \
    DJANGO_DB_TIMEOUT=30 \
    DJANGO_SECRET_KEY=secret \
    DJANGO_ALLOWED_HOSTS=* \
    TAIGA_HOSTNAME=localhost:8080 \
    TAIGA_PUBLIC_REGISTER_ENABLED=False \
    TAIGA_SSL=False \
    TAIGA_GDPR_URL= \
    TAIGA_SUPPORT_URL= \
    TAIGA_PRIVACY_POLICY_URL= \
    TAIGA_TOS_URL= \
    TAIGA_EVENTS_URL= \
    TAIGA_EVENTS_HOST= \
    TAIGA_DEFAULT_LANGUAGE=en \
    TAIGA_DEFAULT_THEME=taiga \
    TAIGA_GRAVATAR=False \
    TAIGA_FEEDBACK_ENABLED=False \
    TAIGA_MAX_UPLOAD_FILE_SIZE= \
    LDAP_URL=ldap://localhost \
    LDAP_BASEDN=dc=example,dc=com \
    LDAP_ADMIN_GROUP=cn=taiga-admin,ou=groups \
    LDAP_BINDDN= \
    LDAP_BINDPASSWORD= \
    LDAP_GROUP_BASE=ou=groups \
    LDAP_GROUP_MEMBER_ATTRIBUTE=member \
    LDAP_GROUP_NAME_ATTRIBUTE=cn \
    LDAP_USER_BASE=ou=users \
    LDAP_USER_GROUP=cn=taiga,ou=apps,ou=groups \
    LDAP_USER_OBJECTCLASS=inetOrgPerson \
    LDAP_USER_USERNAME_ATTRIBUTE=uid \
    LDAP_USER_EMAIL_ATTRIBUTE=mail \
    LDAP_USER_FULLNAME_ATTRIBUTE=cn \
    LDAP_USER_PHOTO_ATTRIBUTE=jpegPhoto \
    LDAP_SYNC_INTERVAL=60 \
    OPENID_USER_URL=https://keyclaok/auth/realms/master/protocol/openid-connect/userinfo \
    OPENID_TOKEN_URL=https://keycloak/auth/realms/master/protocol/openid-connect/token \
    OPENID_AUTH_URL=https://keycloak/auth/realms/master/protocol/openid-connect/auth \
    OPENID_CLIENT_ID=taiga \
    OPENID_CLIENT_SECRET=verysecret \
    OPENID_LOGIN_NAME=sso

COPY entrypoint.sh /srv/taiga
COPY start-app.sh /srv/taiga
COPY start-celery.sh /srv/taiga
COPY start-events.sh /srv/taiga
COPY start-ldap-sync.sh /srv/taiga

ENTRYPOINT ["/srv/taiga/entrypoint.sh"]
CMD ["app"]
