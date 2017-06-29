#-*- coding: utf-8 -*-

from migrate.exporter import Exporter
# from push import yona_project
def test_prj():
	prj_id = 'horai'
        exporter = Exporter()

	exporter.pull_attachments(prj_id)
#	project.push_issue(prj_id, issues[0])
