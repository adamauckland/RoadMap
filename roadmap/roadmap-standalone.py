import wsgiserver
import sys
import site
import os
import django.core.handlers.wsgi

if __name__ == "__main__":

	path = os.path.abspath('..')
	if path not in sys.path:
		sys.path.append(path)

	path = os.path.abspath('.')
	if path not in sys.path:
		sys.path.append(path)

	os.environ['DJANGO_SETTINGS_MODULE'] = 'roadmap.settings'
	server = wsgiserver.CherryPyWSGIServer(
		('0.0.0.0', 9001),
		django.core.handlers.wsgi.WSGIHandler(),
		server_name='roadmap',
		numthreads = 20,
	)
	try:
		print('Starting server on any available IP address, port 9001.\nPress Ctrl-C to stop.')
		server.start()
	except KeyboardInterrupt:
		server.stop()
