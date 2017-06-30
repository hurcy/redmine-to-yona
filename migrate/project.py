#-*- coding: utf-8 -*-
from redminelib.resources import *
import os
from util import *


class Project(object):

    def __init__(self, redmine, attachment_base_dir, user_dict, status_dict, prj_id):
        self.redmine = redmine
        self.user_dict = user_dict
        self.status_dict = status_dict
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

    def dump_attachment(self, savepath, attachment, parent):
        filepath = os.path.join(savepath, attachment['filename'])
        each = {
            "id": attachment['id'],  # attachment id
            "name": attachment['filename'],
            "hash": get_filehash(filepath),
            "containerType": "ISSUE_COMMENT",
            "mimeType": attachment['content_type'],
            "size": attachment['filesize'],
            "containerId": parent.id,
            "createdDate": unix_time_millis(attachment['created_on']),
        }
        if 'author' in dir(parent):
            each['ownerLoginId'] = self.user_dict[
                parent.author.name]['login_id']
        elif 'user' in dir(parent):
            each['ownerLoginId'] = self.user_dict[parent.user.name]['login_id']
        return each

    def pull_attachment(self, aid, parent):
        savepath = "%s/%s" % (self.attachment_base_dir, aid)
        if not os.path.exists(savepath):
            os.mkdir(savepath)
        attachment = self.redmine.attachment.get(aid)
        attachment.download(savepath=savepath,
                            filename=str(attachment))
        each = self.dump_attachment(savepath, attachment, parent)
        return each

    def pull_attachments(self, parent):
        attachments = list()
        if isinstance(parent, standard.IssueJournal):
            for each in parent['details']:
                if each['property'] == 'attachment':
                    attachments.append(
                        self.pull_attachment(each['name'], parent))

            return attachments
        elif isinstance(parent, standard.Issue):
            if 'attachments' in dir(parent):
                for each in parent['attachments']:
                    attachments.append(
                        self.pull_attachment(each['id'], parent))
            return attachments
        else:
            return None

    def dump_comments(self, journals):
        comments = list()
        for j in journals:
            each = dict()
            each['id'] = j.id
            each['type'] = 'ISSUE_COMMENT'
            each['authorId'] = self.user_dict[j.user.name]['login_id']
            each['authorName'] = self.user_dict[j.user.name]['name']
            each['created_at'] = unix_time_millis(j.created_on)
            each['body'] = j.notes.encode('utf-8')
            attachments = self.pull_attachments(j)
            if attachments:
                each['attachments'] = attachments
            comments.append(each)
        return comments

    def pull_comments(self, issue_id):
        prop = 'journals'
        issue = self.redmine.issue.get(issue_id, include=prop)
        if prop in dir(issue):
            journals = issue[prop]
            return self.dump_comments(journals)
