#
# Standard Library imports
#
import base64
import calendar
import datetime, time
from decimal import Decimal
import hashlib
import os, os.path
from poplib import *
import shutil
import urllib2
import uuid
import pickle
import hotshot
from operator import itemgetter, attrgetter
import urlparse
import subprocess
import sys
import signal
import cookielib
import difflib
#import importlib

#
# Django imports
#
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core import serializers
from django.utils import simplejson
from django.core.urlresolvers import reverse
from django.db import connection, transaction
from django.db.models import Sum, Count
from django.db.models import Q
from django.forms import ModelForm, Form
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404, render_to_response
from django.template import loader, RequestContext
#from django.contrib.csrf.middleware import csrf_exempt
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import escape
from django.db import connection
from django.forms.extras.widgets import SelectDateWidget
from django.template.defaultfilters import slugify
#
# GreenLight imports
#
from greenlight.interface.models import *
import greenlight.settings




def home(request):
	activity = Activity.objects.filter(activity_type = 'user')

	for loop_item in activity:
		loop_item.uri_parse = urlparse.urlparse(loop_item.uri)

	return render_to_response(
		'interface/home.html',
		{
			'activity': activity,
		},
		context_instance = RequestContext(request),
	)




def read_log(request, suite_id):
	log_file = os.path.join(greenlight.settings.SITE_ROOT, 'proxy_log', ('%s.log' % suite_id))

	while not os.path.exists(log_file):
		time.sleep(1)

	with open(log_file, 'rt') as read_log:
		log = read_log.read()

	return render_to_response(
		'interface/read_log.html',
		{
			'log': log,
			'suite_id': suite_id,
		},
		context_instance = RequestContext(request),
	)




def start_learning(request, suite_id):
	log_file = os.path.join(greenlight.settings.SITE_ROOT, 'proxy_log', ('%s.log' % suite_id))

	if os.path.exists(log_file):
		os.remove(log_file)

	start_proxy(suite_id)

	return HttpResponseRedirect(reverse('greenlight.interface.views.read_log', kwargs ={ 'suite_id' : suite_id})) #list_suite(request)# HttpResponseRedirect(reverse('greenlight.interface.views.list_suite'))



def suite_details(request, suite_id):
	if request.method == 'POST':
		if request.POST.get('delete', '') != '':
			for loop_key, value in request.POST.iteritems():
				print value
				if loop_key.startswith('select') and value != '':
					search_id = int(loop_key.split('_')[1])
					item = Activity.objects.get(id = search_id)
					item.delete()
		if request.POST.get('deleteAllImages', '') != '':
			activities = Activity.objects.filter(test_suite__id = suite_id)
			for loop_activity in activities:
				lower_uri = loop_activity.uri.lower()
				remove_items = ['jpg', 'jpeg', 'gif', 'png']
				for check in remove_items:
					if lower_uri.endswith(check):
						loop_activity.delete()
						next

	suite = TestSuite.objects.get(id = suite_id)
	return render_to_response(
		'interface/suite_details.html',
		{
			'suite': suite,
		},
		context_instance = RequestContext(request),
	)



def activity_details(request, activity_id):
	activity = Activity.objects.get(id = activity_id)
	return render_to_response(
		'interface/activity_details.html',
		{
			'activity': activity,
		},
		context_instance = RequestContext(request),
	)



def start_proxy(suite_id):
	new_pid = os.fork()
	if new_pid == 0:
		proxy_process_id = os.getpid()

		proxy_path = os.path.join(greenlight.settings.SITE_ROOT, 'proxy.py')
		sub_process = subprocess.Popen([sys.executable, proxy_path, str(suite_id)])
		process_id = sub_process.pid

		suite = TestSuite.objects.get(id = suite_id)
		suite.status = 'learning'
		suite.proxy_id = process_id
		suite.save()

		#os._exit(0)
	else:
		pass



def stop_learning(request, suite_id):
	suite = TestSuite.objects.get(id = suite_id)

	os.kill(suite.proxy_id,  signal.SIGTERM)

	suite.status = ''
	suite.proxy_id = 0
	suite.save()

	return HttpResponseRedirect(reverse('greenlight.interface.views.list_suite'))



def start_suite(request, suite_id):
	new_pid = os.fork()
	if new_pid == 0:
		activate_test_suite(request, suite_id)
		os._exit(0)
	else:
		return HttpResponseRedirect(reverse('greenlight.interface.views.list_suite'))




def activate_test_suite(request, suite_id):
	suite = TestSuite.objects.get(id = suite_id)
	session = TestSession()
	session.test_suite = suite
	session.cookies = ''
	session.save()

	cookie_jar = cookielib.LWPCookieJar()

	cookie_dir = os.path.join(greenlight.settings.SITE_ROOT, 'cookies')
	if not os.path.exists(cookie_dir):
		os.mkdir(cookie_dir)

	cookie_file = os.path.join(cookie_dir, str(session.id))
	if os.path.exists(cookie_file):
		os.remove(cookie_file)

	page_buffer = {}

	activity = Activity.objects.filter(test_suite = suite).order_by()
	for loop_activity in activity:
		if loop_activity.activity_type == 'assert':
			result = TestResult()
			result.activity = loop_activity
			result.test_session = session
			result.response = ''
			result.response_headers = ''
			log = []

			referrer_uri = loop_activity.referrer
			if page_buffer.has_key(referrer_uri):
				if loop_activity.assert_text() != '':
					if page_buffer[referrer_uri].find(loop_activity.assert_text()) != -1:
						log.append('found assert')
					else:
						log.append('found assert failed')

				if loop_activity.assert_parent_text() != '':
					if page_buffer[referrer_uri].find(loop_activity.assert_parent_text()) != -1:
						log.append('found parent assert')
					else:
						log.append('found parent assert failed')
			else:
				log.append('could not find page in buffer')
			result.result = '\n'.join(log)
			result.save()

		if loop_activity.activity_type == 'user':
			print(loop_activity.uri)

			if os.path.exists(cookie_file):
				cookie_jar.load(cookie_file)
				opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
			else:
				opener = urllib2.build_opener()

			#
			# get the page
			#
			opener.addheaders.append(
				('Cookie', session.cookies),
			)
			error = None
			if loop_activity.method == 'POST':
				headers_object = eval(loop_activity.headers)
				headers_list = []
				#print headers_object
				#for loop_key, loop_value in headers_object:
				#	headers_list.append('%s: %s' % (loop_key, loop_value))

				#data = '\n'.join(headers_list)
				data = loop_activity.post_data
				try:
					url_open = opener.open(loop_activity.uri, data)
				except Exception, ex:
					error = ex
			else:
				try:
					url_open = opener.open(loop_activity.uri)
				except Exception, ex:
					error = ex

			if not error:
				cookie = ''
				cookie_jar.save(cookie_file)

				info = str(url_open.info())
				response_headers = info
				response = url_open.read().decode('latin-1')
				url_open.close()

				result = TestResult()
				result.activity = loop_activity
				result.test_session = session
				result.response = response
				result.response_headers = response_headers
				result.result = 'downloaded'
				result.save()

				page_buffer[loop_activity.uri] = response

				#
				# store cookie
				#
				session.cookies = cookie
				session.save()
			else:
				result = TestResult()
				result.activity = loop_activity
				result.test_session = session
				result.response = ''
				result.response_headers = ''
				result.result = 'error %s' % error
				result.save()

			time.sleep(1)





def examine_session(request, session_id):
	session = TestSession.objects.get(id = session_id)
	results = TestResult.objects.filter(test_session = session).order_by('id')
	#for result in results:
	#	pass
	#	if result.response != result.activity.response:
	#		difference= []
	#		for loop_diff in difflib.unified_diff(result.response.split('\n'), result.activity.response.split('\n')):
	#			difference.append(loop_diff)
	#		result.difference_data = '\n'.join(difference)
	#		result.difference = 'different'
	#	else:
	#		result.difference = 'match'

	return render_to_response(
		'interface/results.html',
		{
			'results': results,
		},
		context_instance = RequestContext(request),
	)



def list_suite(request):
	if request.method == 'POST':
		new_suite = TestSuite()
		new_suite.name = request.POST.get('name')
		new_suite.status = 'new'
		new_suite.data = ''
		new_suite.proxy_id = 0
		new_suite.save()

	test_suite = TestSuite.objects.all()

	for loop_item in test_suite:
		if loop_item.status == 'learning':
			if os.path.exists('/proc/%s' % loop_item.proxy_id):
				loop_item.process_running = True

			else:
				loop_item.status = ''
				loop_item.proxy_id = 0
				loop_item.save()

	return render_to_response(
		'interface/suite.html',
		{
			'test_suite': test_suite,
		},
		context_instance = RequestContext(request),
	)



def test(request):
	activity = Activity.objects.filter(activity_type = 'user').order_by('id')

	for loop_item in activity:
		pass

	return render_to_response(
		'interface/results.html',
		{
			'activity': activity,
		},
		context_instance = RequestContext(request),
	)