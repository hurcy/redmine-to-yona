#-*- coding: utf-8 -*-

from migrate import project
# from push import yona_project
def test_prj():
	prj_id = 'horai'
	issues = project.pull_issues(prj_id)
	project.push_issue(prj_id, issues[0])