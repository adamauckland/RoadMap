from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm
import os
import os.path

def read_tip(project):
	remote_directory = os.path.join('~/repositories/', project)
	with cd(remote_directory):
		response = run('hg id -i -r tip')
		print('OH!')
		print(response)
		return response

def read_log(project):
	remote_directory = os.path.join('~/repositories/', project)
	with cd(remote_directory):
		response = run('hg log')
		return response
