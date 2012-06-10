import datetime

from django.db import models
from django.contrib.auth.models import User, Group, UserManager
from django.utils.safestring import mark_safe
from django.template.defaultfilters import slugify
from django.db.models import Q
from django.http import QueryDict
import urlparse

class TestSuite(models.Model):
	name = models.CharField(max_length = 1000)
	status = models.CharField(max_length = 20)
	data = models.CharField(max_length = 1000)
	proxy_id = models.IntegerField()

	def test_sessions(self):
		return TestSession.objects.filter(test_suite = self)

	def activities(self):
		return Activity.objects.filter(test_suite = self)

	# Create your models here.
class Activity(models.Model):
	date_time = models.DateTimeField(default = datetime.datetime.now())
	ip_address = models.CharField(max_length = 20)
	method = models.CharField(max_length = 20)
	uri = models.TextField()
	post_data = models.TextField()
	headers = models.TextField()
	response = models.TextField()
	response_headers = models.TextField()
	activity_type = models.CharField(max_length = 20)
	test_suite = models.ForeignKey(TestSuite)
	referrer = models.TextField()

	def broken_uri(self):
		url_parse = urlparse.urlparse(self.uri)
		return url_parse

	def assert_text(self):
		result = ''
		result_dict = QueryDict(self.post_data)
		if result_dict.has_key('data'):
			result = result_dict['data']
		return result

	def assert_parent_text(self):
		result = ''
		result_dict = QueryDict(self.post_data)
		if result_dict.has_key('parentData'):
			result = result_dict['parentData']
		return result

	def headers_unpacked(self):
		return eval(self.headers)

	def response_headers_unpacked(self):
		return eval(self.response_headers)


class TestSession(models.Model):
	test_suite = models.ForeignKey(TestSuite)
	cookies = models.TextField()

	def test_results(self):
		return TestResult.objects.filter(test_session = self)

	def test_activities(self):
		return Activity.objects.filter(test_suite = self.test_suite,  activity_type = 'user')

	def test_asserts(self):
		return Activity.objects.filter(test_suite = self.test_suite,  activity_type = 'assert')

class TestResult(models.Model):
	test_session = models.ForeignKey(TestSession)
	activity = models.ForeignKey(Activity)

	response = models.TextField()
	response_headers = models.TextField()

	result = models.TextField()