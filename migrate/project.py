#-*- coding: utf-8 -*-
from redminelib.resources import *

class Project(object):

    dump_info = {
        "owner": None,
        "projectName": None,
        "projectDescription": None,
        "assignees": [], # 프로젝트 기준으로 이슈에 한 번이라도 담당자가 된적이 있는 사람들
        "authors": [], # 이슈나 게시글을 한 번이라도 작성했던 적이 있는 사람
        "memberCount": 0,
        "members": [], # members 는 해당 프로젝트의 현재 멤버
        "issueCount": 0,
        "issues": [],
        "postCount": 0,
        "posts": [],
        "milestoneCount": 0,
        "milestones": []
    }

    def __init__(self, redmine, user_dict, status_dict, prj_id):
        self.redmine = redmine
        self.user_dict = user_dict
        self.status_dict = status_dict
        self.prj_id = prj_id


    def dump_all(self):
        self.pull_project_info()
        self.pull_issues()


    def pull_project_info(self):
        project_info = self.redmine.project.get(self.prj_id)
        self.dump_info['projectName'] = project_info.name
        self.dump_info['projectDescription'] = project_info.description


    def pull_issues(self):
        issues = self.redmine.issue.filter(
            project_id=self.prj_id,
            status_id='*',
            subproject_id='!*',
            sort='id:asc'
        )
        # [u'attachments', u'author', u'changesets', u'children',
        # u'created_on', u'description', u'done_ratio', u'id',
        # u'journals', u'priority', u'project', u'relations',
        # u'start_date', u'status', u'subject', u'time_entries',
        # u'tracker', u'updated_on', u'watchers']
        #
        for each_issue in issues:

            issue = dict()
            issue['number'] = each_issue.id
            issue['id'] = each_issue.id
            issue['title'] = each_issue.subject
            issue['body'] = each_issue.description
            issue['author'] = self.user_dict[each_issue.author.name]
            issue['assignee'] = self.user_dict[each_issue.assigned_to.name]
            issue['createdAt'] = each_issue.created_on
            issue['updatedAt'] = each_issue.updated_on

            self.issueCount += 1
            self.issues.append(issue)

