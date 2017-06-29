#-*- coding: utf-8 -*-

from migrate import project
from migrate.exporter import Exporter
# from push import yona_project
def test_prj():
    pass
    #prj_id = 'horai'
    #issues = project.pull_issues(prj_id)
    #project.push_issue(prj_id, issues[0])

def test_export():
    exporter = Exporter()
    exporter.runner()

