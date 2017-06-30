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
            each_info['loginId'] = each_user.login
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


    def dump_roles(self):
        role_dict = dict()
        roles = self.redmine.role.all()
        for each in roles:
            if each.name in self.m_config['REDMINE']['PROJECT_ADMIN']:
                role_dict[each.name] = 1 #'manager'
            else:
                role_dict[each.name] = 2 #'member'
        return role_dict

    def pull_projects(self):
        projects = self.redmine.project.all(offset=0, limit=100)
        ids = list()
        for project in projects:
            ids.append(project.identifier)
        return ids

    def runner(self):
        user_dict = self.dump_users(offset=1)
        status_dict = self.dump_status()
        role_dict = self.dump_roles()

        project_list = self.pull_projects()
        dump_projects = {}

        for each_project in project_list:
            project = Project(self.redmine, self.attachment_base_dir, user_dict, status_dict, role_dict, each_project, self.m_config)
            dump_projects[each_project] = project

        for each_project in self.m_config['REDMINE']['BOARD_LIST']:
            for board_meta in self.m_config['REDMINE']['BOARD_LIST'][each_project]:
                print board_meta
                if board_meta[1] in dump_projects:
                    dump_projects[board_meta[1]].pull_board(board_meta[0])
                else:
                    project = Project(self.redmine, user_dict, status_dict, role_dict, each_project, self.m_config)
                    project.init_project_info(board_meta[1])
                    project.pull_board(board_meta[0])
                    dump_projects[board_meta[0]] = project
