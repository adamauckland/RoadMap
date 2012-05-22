from __future__ import with_statement
import fabric
from fabric.contrib.console import confirm
import os
import os.path

class Repository(object):
	"""
	Holds a list of commits
	"""
	def __init__(self):
		self.name = ''

class Commit(object):
	"""
	Parse and format a commit chunk.

	Properties
	 | changeset
	 | branch
	 | user
	 | date
	 | summary
	"""
	def __init__(self):
		self.changeset = ''
		self.branch = ''
		self.user = ''
		self.date = ''
		self.summary = ''

	def parse(self, parse_input):
		splitlines = parse_input.split('\r\n')
		attributes = ['changeset', 'branch', 'user', 'date', 'summary']
		for loop_line in splitlines:
			for loop_attribute in attributes:
				if loop_line.startswith('%s:' % loop_attribute):
					split_line = loop_line.split('%s:' % loop_attribute)
					value = split_line[1].strip()
					setattr(self, loop_attribute, value)

class MercurialReader(object):
	def __init__(self, connectionstring, password, repositorypath):
		"""
		Create a new instance of MercurialReader.

		Required parameters:
		 | connectionstring - the connectionstring to login to the server
		 | repositorypath - the path on the remote server where the repository is stored
		 | password - the password for the user specified in connectionstring
		"""
		self.connectionstring = connectionstring
		self.repositorypath = repositorypath
		self.password = password

	def init_fabric(self):
		"""
		Setup fabric's auth details
		"""
		fabric.api.env.host_string = self.connectionstring
		fabric.api.env.password = self.password
		fabric.api.output.stdout = False

	def get_logs(self, date_from=None, date_to=None, revision_from=None, revision_to=None):
		"""
		Fetches the logs for the binder.

		Returns a list of Commit objects.
		"""
		self.init_fabric()
		remote_directory = self.repositorypath
		command = 'hg log '
		if date_from != None and date_to != None:
			command += ' --date \'%s to %s\' ' % (date_from, date_to)
		if revision_from != None and revision_to != None:
			command += ' -r %s:%s' % (revision_from, revision_to)
		with fabric.api.cd(remote_directory):
			response = fabric.api.run(command)
		batches = response.split('\r\n\r\n')
		logs = []
		for loop_batch in batches:
			batch_item = Commit()
			batch_item.parse(loop_batch)
			logs.append(batch_item)
		return logs

	def get_tip(self):
		"""
		Get the ID of the tip revision.

		Returns a string.
		"""
		self.init_fabric()
		remote_directory = self.repositorypath
		command = 'hg id -i -r tip'
		with fabric.api.cd(remote_directory):
			response = fabric.api.run(command)
		return response


#
# Tests
#
def read_log(binder):
	fabric.api.env.host_string = 'administrator@127.0.0.1:22222'
	remote_directory = os.path.join('~/repositories/', binder)
	with fabric.api.cd(remote_directory):
		response = fabric.api.run('hg log -r 476f2b4c2059:tip')
		return response

def look_for_warnings(scan):
	repositories = [
		'c5',
		#'c5-demo',
		#'c5-demo-installation',
	]
	report = []
	for loop_repository in repositories:
		report.append('')
		report.append('Repository: %s' % loop_repository)
		reader = MercurialReader('administrator@192.168.1.8', 'bh243pl', os.path.join('~/repositories/', loop_repository))
		tip = reader.get_tip()
		logs = reader.get_logs(revision_from = '80762618892a', revision_to = 'tip')
		for loop_log in logs:
			if loop_log.summary.lower().find(scan) != -1:
				report.append(loop_log)
	return report

if __name__ == '__main__':
	report = look_for_warnings('template')
	for item in report:
		if type(item) == str:
			print(item)
		else:
			print('%s %s\n\t%s' % (item.date, item.user, item.summary))
