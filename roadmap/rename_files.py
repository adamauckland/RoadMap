import os
import sys

def rename_dir(file_path):
	for loop_file in os.listdir(file_path):
		file_name = os.path.join(file_path, loop_file)

		if os.path.isdir(file_name):
			rename_dir(file_name)
		if os.path.isfile(file_name):
			#print('checking file %s' % file_name)
			#checks = (
			#	('project', 'binder'),
			#	('Project', 'Binder')
			#)
			checks = (
				('milestone', 'project'),
				('Milestone', 'Project'),
			)
			for loop_pair in checks:
				if loop_file.find(loop_pair[0]) != -1:
					new_file = loop_file.replace(loop_pair[0], loop_pair[1])

					do_it = True
					for loop_item in sys.argv:
						if loop_item == '/t':
							do_it = False
					if do_it:
						print '\tRenaming to %s' % new_file
						os.rename(file_name, os.path.join(file_path, new_file))
						print('\tDone.')
					else:
						print '\tTEST: Renaming to %s' % new_file

if __name__ == '__main__':
	rename_dir(sys.argv[1])