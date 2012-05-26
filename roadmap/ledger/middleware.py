import re
import datetime

class MultipleProxyMiddleware(object):
	FORWARDED_FOR_FIELDS = [
		'HTTP_X_FORWARDED_FOR',
		'HTTP_X_FORWARDED_HOST',
		'HTTP_X_FORWARDED_SERVER',
	]

	def process_request(self, request):
		"""
		Rewrites the proxy headers so that only the most
		recent proxy is used.
		"""
		for field in self.FORWARDED_FOR_FIELDS:
			if field in request.META:
				if ',' in request.META[field]:
					parts = request.META[field].split(',')
					request.META[field] = parts[-1].strip()

	def process_response(self, request, response):
		"""
		Sends expires headers for certain files
		"""
		if request.path.startswith('/media/'):
			new_time = (datetime.datetime.today()+datetime.timedelta(minutes=330)).strftime('%a, %d %b %Y %H:%M:%S')
			response['Expires'] = '%s GMT' % (new_time)
			response['Cache-Control'] = 'max-age=330'
		return response


class MediaCacheHeaders(object):
	def process_request(self, request):
		print('test')

	def process_response(self, request, response):
		"""
		Sends expires headers for certain files
		"""
		print('cache headers')
		if request.path.startswith('/media/'):
			new_time = (datetime.datetime.today()+datetime.timedelta(minutes=330)).strftime('%H:%M:%S-%a/%d/%b/%Y')
			print('new time %s ' % new_time)
			response['Expires'] = 'Expires: %s' % (new_time)
			response['Cache-Control'] = 'public, max-age=330'
		return response
