#-*- coding: utf-8 -*-

from migrate.exporter import Exporter
from migrate.project import Project
from migrate.util import kprint
import pytest

skip = pytest.mark.skip

@pytest.fixture
def exporter():
    return Exporter()

@pytest.fixture
def project(exporter):
	project = Project(exporter.redmine,
		exporter.dump_users(offset=1),
		exporter.dump_status(), 
		exporter.dump_roles(),
		'horai',
		exporter.m_config
		)
	return project

@skip
def test_pull_attachments(project):
    issue_id = '1510'
    issue = project.redmine.issue.get(issue_id)
    # assert len (project.pull_attachments(issue))>0

@skip
def test_pull_comments(project):
    issue_id = '1510'
    # assert len( project.pull_comments(issue_id))>0

@skip
def test_download(project):
	download = project.redmine.attachment.get(314)
	assert download is not None

@skip
def test_pull_issue(exporter):
	issue = exporter.redmine.issue.get(1056)
	# kprint(issue.description.encode('utf-8'))

def test_dump(exporter):
 	exporter.runner()
