#-*- coding: utf-8 -*-
import yaml
import os
from redminelib import Redmine
import requests
from redminelib.resources import *


m_config = dict()
with open("config.yml") as stream:
    try:
        m_config = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)
print m_config

redmine = Redmine(m_config['REDMINE']['URL'],
                  key=m_config['REDMINE']['USER_TOKEN'])

def pull_projects():
    projects = redmine.project.all(offset=0, limit=100)
    ids = list()
    for project in projects:
        ids.append(project.identifier)
    print ids, len(ids)

    # project = redmine.project.get(ids[0])
    # for issue in project.issues:
    #     print issue
    #     print  dir(issue)


def dump_issue(issue):
    # print issue.id
    savepath = "%s/%s" % (m_config['REDMINE']['ATTACHMENTS_DIR'], issue.id)
    if not os.path.exists(savepath):
        os.mkdir(savepath)
    print dir(issue)

    for prop in dir(issue):
        if isinstance(issue[prop], unicode):
            print '\t', prop, issue[prop].encode('utf-8')
        elif prop == 'attachments':
            issue[prop][0].download(
                savepath=savepath, filename=str(issue[prop][0]))
        else:
            print prop, issue[prop]


def pull_issues(prj_id):
    issues = redmine.issue.filter(
        project_id=prj_id,
        status_id='*',
        # subproject_id='!*',
        # created_on='><2012-03-01|2012-03-07',
        # cf_22='~foo',
        sort='category:desc'
    )
    # [u'attachments', u'author', u'changesets', u'children',
    # u'created_on', u'description', u'done_ratio', u'id',
    # u'journals', u'priority', u'project', u'relations',
    # u'start_date', u'status', u'subject', u'time_entries',
    # u'tracker', u'updated_on', u'watchers']
    #
    for issue in issues:
        dump_issue(issue)
        break
    return issues


def push_issue(prj, issue):
    print '---------------------------'
    url = m_config['YONA']['URL'] + \
    m_config['YONA']['ROOT_CONTEXT'] + \
    '/-_-api/v1/owners/hcinyoung/projects/DummyPrj/issues'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Yona-Token': m_config['YONA']['USER_TOKEN']
    }
    data = {
        'id': issue.id,
        'title': issue.subject,
        'body': issue.description,
        'created': issue.start_date
    }
    print url
    r = requests.post(url, headers=headers, data=data)
    print r.status_code
    # print len(issues)
