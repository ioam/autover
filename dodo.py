# TODO:
# - tmp dirs


import shutil
import os

import doit
from doit import action

from pyct import *


example = {
    'name':'example',
    'long':'example',
    'type':str,
    'default':'pkg_depend'
}

from distutils.dir_util import copy_tree

def task_copy_example_project():
    def copy_example(example):
        from_ = os.path.join(doit.get_initial_workdir(), "examples", example)
        copy_tree(from_,'.')

    return {
        'params':[example],
        'actions':[(copy_example,),]
    }


def task_git_init():
    return {
        'actions':[
            action.CmdAction('git init && git add . && git commit -m "init" && git tag -a v0.0.1 -m "one" && echo two > two && git add two && git commit -m "two"')
        ]
    }


def task_get_git_version():
    return {'actions': [action.CmdAction('git describe --long',save_out='git_version')]}


# TODO: this task - like develop install below - should be done in a
# throwaway environment. Should probably just use tox here too.

def task_verify_installed_version():
    return {
        'getargs': {'git_version': ('get_git_version','git_version')},
        'uptodate': [False],
        'params': [example],
        'actions':[
            action.CmdAction('mkdir /tmp/9k && cd /tmp/9k && tmpverify %(example)s %(git_version)s'),
        ]
    }


# TODO: split up
def task_original_script():
    shared_packages = os.path.join(doit.get_initial_workdir(), "dist")
    env1 = os.environ.copy()
    env1['SHARED_PACKAGES'] = shared_packages

    env2 = os.environ.copy()
    env2['PYTHONPATH'] = os.getcwd() # TODO win

    return {
        'getargs': {'git_version': ('get_git_version','git_version')},
        'params': [example],
        'actions':[
            # 1. verify package generation & installation
            action.CmdAction('tox -e py -- %(git_version)s',env=env1),
            # 2. verify in git repo
            action.CmdAction('python %(example)s/tests/__init__.py %(example)s',env=env2),
            # 3. verify develop install
            action.CmdAction('pip install -f ' + shared_packages + ' -e . && mkdir /tmp/9k && cd /tmp/9k && tmpverify %(example)s %(git_version)s',env=env2),
            # TODO: should be some kind of clean up option
            action.CmdAction('pip uninstall -y %(example)s')
        ]
    }

def task_build_param_package():
    shared_packages = os.path.join(doit.get_initial_workdir(), "dist")    
    return {'actions': ['git clone https://github.com/ioam/param.git && cd param && python setup.py bdist_wheel -d %s'%shared_packages]}

def task_check_dirty_detection():
    # TODO: test should be less bash
    return {'actions':[
        'echo "#dirty" >> setup.py',
        '! python setup.py sdist > test-dirty-check 2>&1',
        'grep "AssertionError: Repository is in a dirty state." test-dirty-check'
    ]}

        
