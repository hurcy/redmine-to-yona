#-*- coding: utf-8 -*-
import yaml, os, requests

from redminelib import Redmine
from redminelib.resources import *

from project import Project

class Exporter(object):
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.yml')
    def __init__(self):
        self.m_config = dict()
        with open(Exporter.config_file) as stream:
            try:
                self.m_config = yaml.load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        self.redmine = Redmine(self.m_config['REDMINE']['URL'], key=self.m_config['REDMINE']['USER_TOKEN'])
        self.attachment_base_dir = self.m_config['REDMINE']['ATTACHMENTS_DIR']

    def dump_users(self, offset=0):
        user_dict = dict()
        users = self.redmine.user.all(offset=offset)
        for each_user in users:
            each_info = dict()
            each_info['name'] = each_user.firstname + ' ' + each_user.lastname
            each_info['login_id'] = each_user.login
            each_info['email'] = each_user.mail
            user_dict[each_user.firstname + ' ' + each_user.lastname] = each_info
        return user_dict


    def dump_status(self):
        convert_state = lambda x: 'closed' if x else 'open'
        status_dict = dict()
        statuses = self.redmine.issue_status.all()
        for each in statuses:
            status_dict[each.name] = convert_state(dict(each).get('is_closed', False))
        return status_dict


    def pull_projects(self):
        projects = self.redmine.project.all(offset=0, limit=100)
        ids = list()
        for project in projects:
            ids.append(project.identifier)
        # print ids, len(ids)
        return ids


    def runner(self):
        user_dict = self.dump_users(offset=1)
        status_dict = self.dump_status()
        project_list = self.pull_projects()

        for each_project in project_list:
            project = Project(self.redmine, self.attachment_base_dir, user_dict, status_dict, each_project)
            output = project.dump_all()

