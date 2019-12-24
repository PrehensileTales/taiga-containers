# Taiga container with optional LDAP synchronization.

[![Docker Repository on Quay.io](https://quay.io/repository/tmm/taiga/status "Docker Repository on Quay.io")](https://quay.io/repository/tmm/taiga)

This container runs Taiga from Github release tags on Fedora 31. The container contains the OpenID plugin out of the box, but it's only enabled if an OpenID configuration exists in the environment. There's also an LDAP synchronization that can be ran in a separate container. This is also an optional feature.

The container is used in production by Prehensile Tales running in Podman.

## Running

The container is build by Quay.io at `quay.io/tmm/taiga`. The container has all of the services installed so the container needs to be ran once for each service. The container implements the following commands:

* app - Run Taiga front and back. Without configuration of Celery, events, or LDAP sync this is all that's necessary to get a working Taiga installation. The default command.
* celery - Run the Taiga celery worker. It is only necessary to run this container if `TAIGA_CELERY_ENABLED=True` is set.
* events - Run the Taiga events service. It is only necessary to run this container if `TAIGA_EVENTS_HOST` is set.
* ldap-sync - Runs the LDAP sync plugin. Configuration of this service is explained later in this document.

See the included `env.example` for an example.

An example to run a full stack using podman:

```
podman pod create -n taiga -p 8080:8080
podman run -dt --pod taiga --rm --env-file=env postgres
podman run -dt --pod taiga --rm --env-file=env rabbitmq
podman run -dt --pod taiga --rm --env-file=env redis

podman run -dt --pod taiga --rm -v /home/hp/tmp/taiga-media/:/srv/taiga/media --env-file=env quay.io/tmm/taiga:latest app
podman run -dt --pod taiga --rm -v /home/hp/tmp/taiga-media/:/srv/taiga/media --env-file=env quay.io/tmm/taiga:latest events
podman run -dt --pod taiga --rm -v /home/hp/tmp/taiga-media/:/srv/taiga/media --env-file=env quay.io/tmm/taiga:latest celery
podman run -dt --pod taiga --rm -v /home/hp/tmp/taiga-media/:/srv/taiga/media --env-file=env quay.io/tmm/taiga:latest ldap-sync
```

## Configuration

### Database

The container expects the `postgres` user to exist, and `POSTGRES_PASSWORD` to be set to this password. The container will use these credentials to create the `DJANGO_DB_NAME` database and the `DJANGO_DB_USER` user.

* `POSTGRES_PASSWORD` - Superuser password for the `postgres` user.
* `DJANGO_DB_NAME` - Name of the Postgres database to user
* `DJANGO_DB_USER`
* `DJANGO_DB_PASSWORD`
* `DJANGO_DB_HOST`
* `DJANGO_DB_PORT`
* `DJANGO_DB_TIMEOUT`

### RabbitMQ

If Celery or Events is going to be used it is necessary to configure a RabbitMQ message queue. 

* `RABBITMQ_SERVER`
* `RABBITMQ_DEFAULT_PASS`
* `RABBITMQ_DEFAULT_USER`
* `RABBITMQ_DEFAULT_VHOST`

### Redis

If Celery is going to be used it is necessary to configure a Redis server.

* `REDIS_SERVER`

### Taiga

* `TAIGA_HOSTNAME` - External hostname that the Taiga host is exposed at
* `TAIGA_PUBLIC_REGISTER_ENABLED`
* `TAIGA_SSL` - Taiga is exposed over SSL, requires a SSL proxy like Nginx or Apache in front of the container.
* `TAIGA_GDPR_URL`
* `TAIGA_SUPPORT_URL`
* `TAIGA_PRIVACY_POLICY_URL`
* `TAIGA_TOS_URL`
* `TAIGA_DEFAULT_LANGUAGE`
* `TAIGA_DEFAULT_THEME`
* `TAIGA_THEMES` - Themes to expose in the user interface. Comma separated (taiga,taiga-fresh,material-design,high-contrast)
* `TAIGA_GRAVATAR` - Enable gravatar support (True/False)
* `TAIGA_FEEDBACK_ENABLED`
* `TAIGA_FEEDBACK_EMAIL`
* `TAIGA_MAX_UPLOAD_FILE_SIZE`
* `TAIGA_CELERY_ENABLED` - When enabled expect the Celery service to be running (True/False)
* `TAIGA_CELERY_PROCESSES` - Number of Celery processes to run in the Celery container.
* `TAIGA_EVENTS_HOST` - Hostname/ip of where the Events service runs. When enabled the Events container needs to run also
* `TAIGA_EVENTS_PORT`

### OpenID plugin

When OpenID settings are present the OpenID plugins will be loaded. When no settings exist the plugin will not be activated.

* `OPENID_USER_URL` - When set enables all OpenID plugins.
* `OPENID_TOKEN_URL`
* `OPENID_AUTH_URL`
* `OPENID_CLIENT_ID`
* `OPENID_CLIENT_SECRET`
* `OPENID_LOGIN_NAME` - Name of the backend as it appears in the frontend

### LDAP synchronization

The container contains an LDAP synchronization plugin. This is a service that runs periodically and creates users in Taiga, and assigns project memberships based on group memberships. The plugin makes no attempt to set passwords in Taiga so this plugin is primarily useful when combined with the OpenID plugin. The plugin will not allow an LDAP user to have a password in the backend.

The LDAP synchronization service requires the `memberOf` attribute to exist in the LDAP backend. Active Directory and 386DS/Redhat Directory have this by default. For OpenLDAP (as used by Prehensile Tales) the `memberof` overlay needs to be installed.

Users are synchronized only if they are a member of the `LDAP_USER_GROUP` group in LDAP. Users not a member of this group are ignored.

Project memberships are based on groupname and project slug. If a group is called `backend` then any user member of that group will be added to any Taiga project that has a slug that starts with `backend`. This way a single group membership can control multiple projects. User memberships will not be maintained for any project for which no corresponding LDAP group exists.

* `LDAP_URL`
* `LDAP_BASEDN`
* `LDAP_ADMIN_GROUP` - Members of this group will be made Taiga admin.
* `LDAP_BINDDN`
* `LDAP_BINDPASSWORD`
* `LDAP_GROUP_BASE`
* `LDAP_GROUP_MEMBER_ATTRIBUTE`
* `LDAP_GROUP_NAME_ATTRIBUTE`
* `LDAP_USER_BASE`
* `LDAP_USER_GROUP` - Members of this group will be created in Taiga.
* `LDAP_USER_OBJECTCLASS`
* `LDAP_USER_USERNAME_ATTRIBUTE`
* `LDAP_USER_EMAIL_ATTRIBUTE`
* `LDAP_USER_FULLNAME_ATTRIBUTE`
* `LDAP_USER_PHOTO_ATTRIBUTE`
* `LDAP_SYNC_INTERVAL`

