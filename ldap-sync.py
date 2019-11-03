#!/usr/bin/env python3

python_home = '/srv/taiga/taiga-back/taiga'

activate_this = python_home + '/bin/activate_this.py'
exec(open(activate_this).read(), {'__file__': activate_this})

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

import django
django.setup()

import environ
import ldap
import hashlib

from django.contrib.auth import get_user_model
from django.core.files import File
from easy_thumbnails.files import generate_all_aliases, get_thumbnailer
from tempfile import NamedTemporaryFile

from taiga.projects import models as project_models

env = environ.Env()

stats = {
  'created': 0,
  'updated': 0,
  'project_add': 0,
  'project_remove': 0
}

class LdapConnection:
    def __init__(self):
        self.url = env('LDAP_URL')
        self.binddn = env('LDAP_BINDDN', default='')
        self.bindpassword = env('LDAP_BINDPASSWORD', default='')

        self.basedn = env('LDAP_BASEDN')

        self.group_base = env('LDAP_GROUP_BASE')
        self.group_name_attribute = env('LDAP_GROUP_NAME_ATTRIBUTE')
        self.admin_group = env('LDAP_ADMIN_GROUP', default=None)

        self.user_base = env('LDAP_USER_BASE')
        self.user_group = env('LDAP_USER_GROUP', default=None)
        self.user_objectclass = env('LDAP_USER_OBJECTCLASS')
        self.user_username_attribute = env('LDAP_USER_USERNAME_ATTRIBUTE')
        self.user_fullname_attribute = env('LDAP_USER_FULLNAME_ATTRIBUTE')
        self.user_email_attribute = env('LDAP_USER_EMAIL_ATTRIBUTE')
        self.user_photo_attribute = env('LDAP_USER_PHOTO_ATTRIBUTE', default=None)

        self.user_attributes = [ "memberOf", self.user_username_attribute, self.user_fullname_attribute, self.user_email_attribute ]
        if self.user_photo_attribute:
             self.user_attributes.append(self.user_photo_attribute)

        self.con = ldap.initialize(self.url)
        self.con.simple_bind_s(self.binddn, self.bindpassword)

    def get_groups(self):
        search_base = f"{self.group_base},{self.basedn}"
        search_filter=f"(objectClass=groupOfNames)"

        res = self.con.search(search_base, ldap.SCOPE_SUBTREE, search_filter, ['cn'])
        result_set = []
        while True:
            result_type, result_data = self.con.result(res, 0)
            if (result_data == []):
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(self.get_group_name(result_data[0][0]).lower())

        return result_set

    def get_group_name(self, dn):
        res = self.con.search(dn, ldap.SCOPE_BASE, None, [self.group_name_attribute])
        result_type, result_data = self.con.result(res, 0)
        if result_type == ldap.RES_SEARCH_ENTRY:
            return result_data[0][1][self.group_name_attribute][0].decode()

    def get_users(self):
        search_base = f"{self.user_base},{self.basedn}"
        search_filter = ""
        
        if self.user_group:
            search_filter=f"(&(objectClass={self.user_objectclass})(memberof={self.user_group},{self.basedn}))"
        else:
            search_filter=f"(objectClass={self.user_objectclass})"
          
        res = self.con.search(search_base, ldap.SCOPE_SUBTREE, search_filter, self.user_attributes)
        result_set = {}
        while True:
            result_type, result_data = self.con.result(res, 0)
            if (result_data == []):
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    ldap_data = {}
                    data = {}
                    for attribute in result_data[0][1]:
                        if attribute == self.user_photo_attribute:
                            ldap_data[attribute] = result_data[0][1][attribute]
                        else:
                            ldap_data[attribute] = [ val.decode() for val in result_data[0][1][attribute] ]

                    try:
                        data['dn'] = result_data[0][0]
                        data['username'] = ldap_data[self.user_username_attribute][0]
                        data['full_name'] = ldap_data[self.user_fullname_attribute][0]
                        data['email'] = ldap_data[self.user_email_attribute][0]
                        try:
                            data['photo'] = ldap_data[self.user_photo_attribute][0]
                            data['photo_hash'] = hashlib.md5(data['photo']).digest()
                        except KeyError:
                            data['photo'] = None
                        data['is_superuser'] = f"{self.admin_group},{self.basedn}" in ldap_data['memberOf']
                        data['groups'] = []

                        for group in ldap_data['memberOf']:
                            if group.endswith(f"{self.group_base},{self.basedn}"):
                                data['groups'].append(self.get_group_name(group).lower())
                        result_set[data['username']] = data
                    except KeyError as e:
                        print(f"Skipping Ldap object {result_data[0][0]}, missing attribute {e}.")
        return result_set

def set_taiga_user_photo(user, photo):
    print(f"Setting avatar for Taiga user {user.username}")

    with NamedTemporaryFile(delete=True) as avatar:
        avatar.write(photo)
        avatar.seek(0)
        user.photo = File(avatar)
        user.save()
        generate_all_aliases(user.photo, include_global=True)

def create_taiga_user(ldap_user):
    print(f"Creating new Taiga user {ldap_user['username']}")
    stats['created'] += 1
    
    user = get_user_model().objects.create(
        username = ldap_user['username'],
        full_name = ldap_user['full_name'],
        email = ldap_user['email'],
        is_superuser = ldap_user['is_superuser'],
    )

    if ldap_user['photo']:
        set_taiga_user_photo(user, ldap_user['photo'])
    else:
        user.save()

def update_taiga_user(ldap_user):
    updated = False
    user = get_user_model().objects.get(username = ldap_user['username'])

    if user.full_name != ldap_user['full_name']:
        updated = True
        user.full_name = ldap_user['full_name']

    if user.email != ldap_user['email']:
        updated = True
        user.email = ldap_user['email']

    if user.is_superuser != ldap_user['is_superuser']:
        updated = True
        user.is_superuser = ldap_user['is_superuser']

    if user.password != '':
        updated = True
        user.password = ''

    should_sync_photo = False
    if ldap_user['photo']:
        taiga_photo_hash = ""
        if user.photo:
            try:
                with open(user.photo.path, "rb") as avatar:
                    taiga_photo_hash = hashlib.md5(avatar.read()).digest()
            except FileNotFoundError:
                should_sync_photo = True

            if ldap_user['photo_hash'] != taiga_photo_hash:
                should_sync_photo = True
        else:
            should_sync_photo = True
    else:
        user.photo = None

    if should_sync_photo:
        updated = True
        set_taiga_user_photo(user, ldap_user['photo'])
    else:
        if updated:
            print(f"Updated Taiga user {ldap_user['username']}")
            stats['updated'] += 1
            user.save()

def update_user_memberships(projects, ldap_user):
    user = get_user_model().objects.get(username = ldap_user['username'])

    for project in projects:
        is_in_project = user in project.members.all()
        should_be_in_project = False
        roles = project.get_roles()

        for group in ldap_user['groups']:
            if project.slug.startswith(group):
                should_be_in_project = True
                break;

        if should_be_in_project and not is_in_project:
            print(f"Added Taiga user {ldap_user['username']} to project {project.name}")
            stats['project_add'] += 1
            
            membership = project_models.Membership.objects.create(
                user = user,
                project = project,
                email = user.email,
                role = roles[0],
                is_admin = ldap_user['is_superuser'],
            )
            membership.save()

        if not should_be_in_project and is_in_project:
            print(f"Removing Taiga user {ldap_user['username']} from project {project.name}")
            stats['project_remove'] += 1

            membership = project_models.Membership.objects.get(user = user, project = project)
            membership.delete()

        if should_be_in_project and is_in_project:
            membership = project_models.Membership.objects.get(user = user, project = project)
            if membership.is_admin != ldap_user['is_superuser']:
                if ldap_user['is_superuser']:
                    print(f"Granting Taiga user {ldap_user['username']} admin on {project.name}")
                else:
                    print(f"Revoking Taiga user {ldap_user['username']} admin on {project.name}")
                membership.is_admin = ldap_user['is_superuser']
                membership.save()
    
def ldap_sync():
    print("Fetching users from LDAP")
    ldap = LdapConnection()
    ldap_users = ldap.get_users()

    print("Fetching users from Taiga")
    taiga_username_list = []
    for user in get_user_model().objects.all():
        taiga_username_list.append(user.username)

    ldap_username_list = ldap_users.keys()

    print("Sorting users")
    not_in_taiga = []
    in_taiga = []
    for ldap_username in ldap_username_list:
        if ldap_username in taiga_username_list:
           in_taiga.append(ldap_username)
        else:
           not_in_taiga.append(ldap_username)

    print("Processing projects")
    projects = []
    groups = ldap.get_groups()
    taiga_projects = project_models.Project.objects.all()
    for project in taiga_projects:
        for group in groups:
            if project.slug.startswith(group):
                projects.append(project)

    print("Processing users")
    for user in not_in_taiga:
        create_taiga_user(ldap_users[user])

    for user in in_taiga:
        update_taiga_user(ldap_users[user])

    for username, user in ldap_users.items():
        update_user_memberships(projects, user)

    print()
    print(f"Total users considered: {len(ldap_username_list)}")
    print(f"Total projects considered: {len(projects)}")
    print(f"Created {stats['created']}")
    print(f"Updated {stats['updated']}")
    print(f"Project memberships added: {stats['project_add']}")
    print(f"Project memberships removed: {stats['project_remove']}")

if __name__ == "__main__":
    ldap_sync()
