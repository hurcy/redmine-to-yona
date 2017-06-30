#-*- coding: utf-8 -*-
from redminelib.resources import *
import os


class Project(object):


    def __init__(self, redmine, attachment_base_dir, user_dict, status_dict, prj_id):
        self.redmine = redmine
        self.user_dict = user_dict
        self.status_dict = status_dict
        self.role_dict = role_dict
        self.prj_id = prj_id
        self.attachment_base_dir = attachment_base_dir
        self.dump_info = {
            "owner": None,
            "projectName": None,
            "projectDescription": None,
            "assignees": [],  # 프로젝트 기준으로 이슈에 한 번이라도 담당자가 된적이 있는 사람들
            "authors": [],  # 이슈나 게시글을 한 번이라도 작성했던 적이 있는 사람
            "memberCount": 0,
            "members": [],  # members 는 해당 프로젝트의 현재 멤버
            "issueCount": 0,
            "issues": [],
            "postCount": 0,
            "posts": [],
            "milestoneCount": 0,
            "milestones": []
        }

        print "Start: ", prj_id

    def dump_all(self):
        self.pull_project_info()
        self.pull_versions()
        self.pull_issues()
        self.pull_members()
        return self.dump_info

    def pull_project_info(self):
        project_info = self.redmine.project.get(self.prj_id)
        self.dump_info['projectName'] = project_info.name
        self.dump_info['projectDescription'] = project_info.description

    def pull_author(self, author):
        author_info = self.user_dict[author.name]
        if not author_info in self.dump_info['authors']:
            self.dump_info['authors'].append(author_info)
        return author_info

    def pull_assignee(self, assignee):
        assignee_info = self.user_dict[assignee.name]
        if not assignee_info in self.dump_info['assignees']:
            self.dump_info['assignees'].append(assignee_info)
        return assignee_info

    def pull_members(self):
        memberships = self.redmine.project_membership.filter(project_id=self.prj_id)
        for each_membership in memberships:
            membership = self.user_dict[each_membership.user.name]
            role_idx = 99
            for each_role in each_membership.roles:
                role_idx = self.role_dict[each_role.name] if self.role_dict[each_role.name] < role_idx else role_idx
            membership['role'] = 'manager' if role_idx == 1 else 'member'

            self.dump_info['members'].append(membership)
            self.dump_info['memberCount'] += 1

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
            issue['author'] = self.pull_author(each_issue.author)
            if dict(each_issue).get('assigned_to', None):
                issue['assignee'] = self.pull_assignee(each_issue.assigned_to)
            else:
                issue['assignee'] = []
            issue['createdAt'] = each_issue.created_on
            issue['updatedAt'] = each_issue.updated_on
            # TODO hurcy
            # issue['attachments'] = self.pull_attachments(each_issue)
            # issue['comments'] = self.pull_comments(each_issue.id)
            self.dump_info['issueCount'] += 1
            self.dump_info['issues'].append(issue)

    def pull_versions(self):
        convert_dict = {
            'id': 'id',
            'name': 'title',
            'status': 'state',
            'description': 'description',
            'due_date': 'due_on'
        }
        versions = self.redmine.version.filter(project_id=self.prj_id)
        for each_version in versions:
            version = dict()
            for idx in convert_dict:
                each_item = dict(each_version).get(idx, False)
                version[convert_dict[idx]] = each_item if each_item else None

            self.dump_info['milestoneCount'] += 1
            self.dump_info['milestones'].append(version)

    def pull_attachments(self, issue):
        savepath = "%s/%s" % (self.attachment_base_dir, issue.id)
        if not os.path.exists(savepath):
            os.mkdir(savepath)

        prop = 'attachments'
        if prop in dir(issue):
            attachments = issue[prop]
            for each in attachments:
                each.download(
                    savepath=savepath,
                    filename=str(each))
            return self.dump_attachments(attachments, issue)

    def get_mimeType(self, attachment):
        return "image/jpeg"

    def get_filesize(self, attachment):
        return 0
    def get_filehash(self, attachment):
        return "e3e501fe54a051bf747fd7d003779645714a9031"

    def dump_attachments(self, issue_attachments, issue):
        # under comments
        # "attachments": [
        #     {
        #       "id": 274,
        #       "name": "1.jpg",
        #       "hash": "e3e501fe54a051bf747fd7d003779645714a9031",
        #       "containerType": "ISSUE_COMMENT",
        #       "mimeType": "image/jpeg",
        #       "size": 51092,
        #       "containerId": "109",
        #       "createdDate": 1479140141000,
        #       "ownerLoginId": "doortts"
        #     }
        #   ]
        attachments = list()
        for a in issue_attachments:
            each = {
                "id": 274, # attachment id
                "name": str(a),
                "hash": self.get_filehash(a),
                "containerType": "ISSUE_COMMENT",
                "mimeType": self.get_mimeType(a),
                "size": self.get_filesize(a),
                "containerId": "109", # parent id
                "createdDate": issue.created_on,
                "ownerLoginId": issue.author
              }
            attachments.append(each)
        return attachments

    def dump_comments(self, journals):
        # journals =
        # created_on: 작성날짜
        # details: 변경이력
        # id: 식별자
        # notes: 코멘트
        # user: 작성자
        comments = list()
        for j in journals:
            # save only comments
            if 'notes' in dir(j):
                each = {
                    'id': j.id,
                    'type': 'ISSUE_COMMENT',
                    'authorId': j.user,
                    'created_at': j.created_on,
                    'body': j.notes.encode('utf-8')
                }
                comments.append(each)
        return comments

    def pull_comments(self, issue_id):
        prop = 'journals'
        issue = self.redmine.issue.get(issue_id, include=prop)
        if prop in dir(issue):
            journals = issue[prop]
            return self.dump_comments(journals)
