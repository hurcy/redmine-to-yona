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
		exporter.attachment_base_dir,
		exporter.dump_users(offset=1),
		exporter.dump_status(), 
		exporter.pull_projects())
	return project


def test_pull_attachments(project):
    issue_id = '1401'
    issue = project.redmine.issue.get(issue_id)
    kprint (project.pull_attachments(issue))


def test_pull_comments(project):
    issue_id = '1510'
    kprint( project.pull_comments(issue_id))


def test_download(project):
	print 'download'
	download = project.redmine.attachment.get(314)
	print dir(download)
