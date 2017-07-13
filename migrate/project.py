#-*- coding: utf-8 -*-
import urllib2, xmltodict, re, os

from redminelib.resources import *
from redminelib.exceptions import *
from util import *       
import json
import sys  
import io

reload(sys)  
sys.setdefaultencoding('utf8')

class Project(object):

    def __init__(self, redmine, user_dict, status_dict, role_dict, prj_id, m_config):
        self.redmine = redmine
        self.user_dict = user_dict
        self.status_dict = status_dict
        self.role_dict = role_dict
        self.prj_id = prj_id
        self.m_config = m_config
        self.attachment_base_dir = m_config['REDMINE']['ATTACHMENTS_DIR']
        self.dump_info = {
            "owner": self.m_config['YONA']['OWNER_NAME'],
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
            "milestones": [],
            "labels": [],
        }
        self.alter_users = m_config['REDMINE']['ALTER_USERS']

        exportpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
            '..', self.m_config['REDMINE']['EXPORT_BASE_DIR'], self.m_config['YONA']['OWNER_NAME'])
        if not os.path.exists(exportpath):
            os.mkdir(exportpath)

        self.prjfilepath = os.path.join(exportpath, self.prj_id)
        if not os.path.exists(self.prjfilepath):
            os.mkdir(self.prjfilepath)
        self.prjjson = os.path.join(exportpath, '%s.json' % self.prj_id)

        print "Start: ", prj_id

    def dump_all(self):
        self.pull_project_info()
        self.pull_versions()
        self.pull_issues()
        self.pull_members()
        return self.dump_info

    def init_project_info(self, projectName):
        self.dump_info['projectName'] = projectName

    def pull_project_info(self):
        project_info = self.redmine.project.get(self.prj_id)
        self.dump_info['projectName'] = project_info.name
        self.dump_info['projectDescription'] = project_info.description

    def _handle_user_dict(self, name):
        try:
            return self.user_dict[name]
        except KeyError:
            for k, v in self.alter_users.iteritems():
                if name == 'k':
                    return self.user_dict[v]

    def pull_author(self, author):
        author_info = self._handle_user_dict(author.name)
        if not author_info in self.dump_info['authors']:
            self.dump_info['authors'].append(author_info)
        return author_info

    def pull_assignee(self, assignee):
        # FIXME: remove exception part
        assignee_info = self._handle_user_dict(assignee.name)
            
        if not assignee_info in self.dump_info['assignees']:
            self.dump_info['assignees'].append(assignee_info)
        return assignee_info

    def pull_members(self):
        memberships = self.redmine.project_membership.filter(project_id=self.prj_id)
        for each_membership in memberships:
            membership = self._handle_user_dict(each_membership.user.name)
            role_idx = 99
            for each_role in each_membership.roles:
                role_idx = self.role_dict[each_role.name] if self.role_dict[each_role.name] < role_idx else role_idx
            membership['role'] = 'manager' if role_idx == 1 else 'member'

            self.dump_info['members'].append(membership)
            self.dump_info['memberCount'] += 1

    def pull_board_comment(self, parent_post_idx, entry):
        comment = dict()
        comment['id'] = 1
        comment['type'] = "NONISSUE_COMMENT"
        comment['author'] = self._handle_user_dict(entry['author']['name'])
        comment['createdAt'] = yona_timeformat(entry['updated'])
        comment['body'] = entry['content']

        for each_post in self.dump_info['posts']:
            if each_post['id'] == parent_post_idx:
                if 'comments' in each_post:
                    for each_comment in each_post['comments']:
                        comment['id'] = each_comment['id'] + 1
                else:
                    each_post['comments'] = []
                each_post.append(comment)
                break

    def pull_board(self, board_idx):
        comments_re = re.compile(self.m_config['REDMINE']['URL'].replace('/','\/')+'\/boards\/'+board_idx+'\/topics\/(\d+)\?r=\d+')

        url = self.m_config['REDMINE']['URL']+'/projects/'+self.prj_id+'/boards/'+board_idx+'.atom?key='+self.m_config['REDMINE']['ATOM_TOKEN']
        data = xmltodict.parse(urllib2.urlopen(url).read())

        for each_entry in data['feed']['entry']:
            parent_post_idx = comments_re.findall(each_entry['id'])
            if parent_post_idx:
                self.pull_board_comment(parent_post_idx, each_entry)
            else:
                post = dict()
                post['number'] = each_entry['id'].split('/')[-1]
                post['id'] = each_entry['id'].split('/')[-1]
                post['title'] = each_entry['title'].encode('utf-8')
                post['type'] = 'BOARD_POST'
                post['author'] = self._handle_user_dict(each_entry['author']['name'])
                post['createdAt'] = yona_timeformat(each_entry['updated'])
                post['updatedAt'] = yona_timeformat(each_entry['updated'])
                post['body'] = each_entry['content']

                self.dump_info['posts'].append(post)
                self.dump_info['postCount'] += 1

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
            issue = self.dump_issue(each_issue)
            self.dump_info['issueCount'] += 1
            self.dump_info['issues'].append(issue)

    def dump_issue(self, each_issue):
        print 'issue', each_issue.id
        issue = dict()
        issue['number'] = self.dump_info['issueCount'] + 1
        issue['id'] = each_issue.id
        issue['title'] = each_issue.subject.encode('utf-8')
        issue['type'] = "ISSUE_POST"
        try:
            issue['body'] = each_issue.description.encode('utf-8')
        except ResourceAttrError:
            issue['body'] = ''
        issue['author'] = self.pull_author(each_issue.author)
        if dict(each_issue).get('assigned_to', None):
            issue['assignee'] = self.pull_assignee(each_issue.assigned_to)
        else:
            issue['assignee'] = []
        issue['createdAt'] = yona_timeformat(each_issue.created_on)
        issue['updatedAt'] = yona_timeformat(each_issue.updated_on)
        issue['attachments'] = self.pull_attachments(each_issue)
        issue['comments'] = self.pull_comments(each_issue.id)
        return issue

    def pull_versions(self):
        convert_dict = {
            'id': 'id',
            'name': 'title',
            'status': 'state',
            'description': 'description',
            'due_date': 'dueDate'
        }
        versions = self.redmine.version.filter(project_id=self.prj_id)
        for each_version in versions:
            version = dict()
            for idx in convert_dict:
                each_item = dict(each_version).get(idx, False)
                version[convert_dict[idx]] = each_item if each_item else None
            if version['dueDate']:
                version['dueDate'] = yona_timeformat(version['dueDate'], '%Y-%m-%d')

            self.dump_info['milestoneCount'] += 1
            self.dump_info['milestones'].append(version)

    def dump_attachment(self, savepath, attachment, parent):

        attachmentpath = "%s/%s" % (savepath, attachment['id'])
        if not os.path.exists(attachmentpath):
            os.mkdir(attachmentpath)

        filename = attachment['filename'].encode('utf-8')
        filepath = os.path.join(attachmentpath, filename)
        attachment.download(savepath=attachmentpath,
                            filename=filename)
        each = dict()
        each["id"] = attachment['id']  # attachment id
        each["name"] = attachment['filename'].encode('utf-8')
        each["hash"] = get_filehash(filepath)
        each["containerType"] = "ISSUE_COMMENT"
        each["mimeType"] = get_mimeType(attachment)
        each["size"] = attachment['filesize']
        each["containerId"] = str(parent.id)
        each["createdDate"] = yona_timeformat(attachment['created_on'])
        
        if 'author' in dir(parent):
            each['ownerLoginId'] = self._handle_user_dict(
                parent.author['name'])['loginId']
        elif 'user' in dir(parent):
            each['ownerLoginId'] = self._handle_user_dict(
                parent.user['name'])['loginId']
        return each

    def pull_attachment(self, aid, parent):
        try:
            attachment = self.redmine.attachment.get(aid)
            
            savepath = "%s/%s" % (self.prjfilepath, 'files')
            if not os.path.exists(savepath):
                os.mkdir(savepath)

            return self.dump_attachment(savepath, attachment, parent)
        except ResourceNotFoundError:
            return None

    def pull_attachments(self, parent):
        attachments = list()
        if isinstance(parent, standard.IssueJournal):
            for each in parent['details']:
                if each['property'] == 'attachment':
                    el = self.pull_attachment(each['name'], parent)
                    if el:
                        attachments.append(el)

            return attachments
        elif isinstance(parent, standard.Issue):
            if 'attachments' in dir(parent):
                for each in parent['attachments']:
                    try:
                        el = self.pull_attachment(each['name'], parent)
                        if el:
                            attachments.append(el)
                    except ResourceAttrError:
                        print 'attachment is not found'
            return attachments
        else:
            return None

    def dump_comments(self, journals):
        comments = list()
        for j in journals:
            if 'notes' in dir(j):
                each = dict()
                each['id'] = j.id
                each['type'] = 'ISSUE_COMMENT'
                each['author'] = self._handle_user_dict(j.user.name)
                each['createdAt'] = yona_timeformat(j.created_on)
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

    def dump(self):
        with io.open(self.prjjson, 'w', encoding='utf8') as outfile:
            data = json.dumps(self.dump_info, indent=4, ensure_ascii=False)
            outfile.write(unicode(data))
            # TODO: check json schema using jsonschema (yona-export.schema)
            # from jsonschema import validate
            # validate({"name" : "Eggs", "price" : 34.99}, schema)