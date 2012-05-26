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
import urllib
import uuid
import pickle
import hotshot
from operator import itemgetter, attrgetter
import urlparse

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
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import loader, RequestContext
#from django.contrib.csrf.middleware import csrf_exempt
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import escape
from django.db import connection
from django.forms.extras.widgets import SelectDateWidget
from django.template.defaultfilters import slugify

#
# RoadMap imports
#
import settings
from roadmap.ledger.models import *
import roadmap.ledger.constants as constants
from tagging.models import Tag, TaggedItem, TagManager, TaggedItemManager

#
# Additional references
#
from tinymce.widgets import TinyMCE
from reversion.models import Version
#
# find /path/to/searches -mtime +1 -exec rm '{}' \;
#
#
#
# 'csrftoken': '{{ csrf_token }}'

def profile(log_file):
	"""Profile some callable.

	This decorator uses the hotshot profiler to profile some callable (like
	a view function or method) and dumps the profile data somewhere sensible
	for later processing and examination.

	It takes one argument, the profile log name. If it's a relative path, it
	places it under the PROFILE_LOG_BASE. It also inserts a time stamp into the
	file name, such that 'my_view.prof' become 'my_view-20100211T170321.prof',
	where the time stamp is in UTC. This makes it easy to run and compare
	multiple trials.
	"""

	if not os.path.isabs(log_file):
		log_file = os.path.join(settings.PROFILE_LOG_BASE, log_file)

	def _outer(f):
		def _inner(*args, **kwargs):
			# Add a timestamp to the profile output when the callable
			# is actually called.
			(base, ext) = os.path.splitext(log_file)
			base = base + "-" + time.strftime("%Y%m%dT%H%M%S", time.gmtime())
			final_log_file = base + ext

			prof = hotshot.Profile(final_log_file)
			try:
				ret = prof.runcall(f, *args, **kwargs)
			finally:
				prof.close()
			return ret

		return _inner
	return _outer

class calendar_data(object):
	"""
	Holding class for calendar.
	"""
	def __init__(self):
		self.month_name = ''
		self.weeks = []

class day_data(object):
	"""
	Holding class for calendar day.
	"""
	def __init__(self, value):
		self.ccs_class = ''
		self.value = value

def gravatar_queryset(queryset):
	"""
	Generate the Gravatar URL for each USER item in a queryset.
	"""
	default = ''
	size = 48
	for loop_item in queryset:
		url = "http://www.gravatar.com/avatar.php?%s" % urllib.urlencode({
			'gravatar_id': hashlib.md5(loop_item.user.email).hexdigest(),
			'default': default,
			'size': str(size)
		})
		loop_item.user.gravatar = url

def gravatar_list(queryset):
	"""
	Generate the Gravatar URL for each item in a queryset.
	"""
	default = ''
	size = 48
	for loop_item in queryset:
		url = "http://www.gravatar.com/avatar.php?%s" % urllib.urlencode({
			'gravatar_id': hashlib.md5(loop_item.email).hexdigest(),
			'default': default,
			'size': str(size)
		})
		loop_item.gravatar = url
	return queryset

class UserField(forms.CharField):
	def clean(self, value):
		super(UserField, self).clean(value)
		try:
			User.objects.get(username=value)
			raise forms.ValidationError("Someone is already using this username. Please pick another.")
		except User.DoesNotExist:
			return value

class SignupForm(forms.Form):
	"""
	Signup form.

	Attributes:
		| first_name
		| last_name
		| username
		| password
		| password2
		| email
		| email2
	"""
	first_name = forms.CharField(max_length=30)
	last_name = forms.CharField(max_length=30)
	username = UserField(max_length=30)
	password = forms.CharField(widget=forms.PasswordInput())
	password2 = forms.CharField(widget=forms.PasswordInput(), label="Repeat your password")
	email = forms.EmailField()
	email2 = forms.EmailField(label="Repeat your email")

	def clean_email(self):
		if self.data['email'] != self.data['email2']:
			raise forms.ValidationError('Emails are not the same')
		return self.data['email']

	def clean_password(self):
		if self.data['password'] != self.data['password2']:
			raise forms.ValidationError('Passwords are not the same')
		return self.data['password']

	def clean(self,*args, **kwargs):
		self.clean_email()
		self.clean_password()
		return super(SignupForm, self).clean(*args, **kwargs)

class FileForm(forms.Form):
	"""
	File on a form.
	"""
	subject = forms.CharField(label = 'Description', max_length = 2000, required = True)
	file = forms.FileField(required = False, label = "Upload New File")
	tags = forms.CharField(label = 'Tags', max_length = 2000, required = False, widget = forms.widgets.HiddenInput())
	comments = forms.CharField(label = 'Comments', widget = forms.widgets.Textarea(), required = False)

class FileProcess():
	"""
	Process a file
	"""
	def load(self, request, item, linked_item, extra):
		"""
		Return a dict to populate the form with an instance.
		"""
		extra['buttons_update'] = True
		extra['fileitem'] = linked_item

		return {
			'subject' : item.description,
			'tags' : item.tags,
			'name' : linked_item.name,
			'fileitem' : linked_item.file,
		}

	def save(self, request, item, linked_item, linked_item_form):
		"""
		Save the file to disc and store a reference to it.
		"""
		try:
			form_file = request.FILES['file']
			dir_name = str(uuid.uuid1())
			plain_name = dir_name + '/' + form_file.name
			os.makedirs(os.path.join(settings.MEDIA_ROOT, 'documents', dir_name))
			file_name = os.path.join(settings.MEDIA_ROOT, 'documents', plain_name)
			spool = open(file_name, 'wb')
			for chunk in form_file.chunks():
				spool.write(chunk)
			spool.close()
			linked_item.file = plain_name

			linked_item.name = form_file.name
			if linked_item.name.find('.') != -1:
				linked_item.filetype = linked_item.name[linked_item.name.rfind('.'):]
		except:
			pass

		item.description = linked_item_form.cleaned_data['subject']
		item.tags = linked_item_form.cleaned_data['tags']
		item.save()
		linked_item.save()

		#
		# Check for comments and add
		#
		comment_text = linked_item_form.cleaned_data['comments'].strip()
		if comment_text != '':
			post_comment(request, item, comment_text)
			#comment = Comment()
			#comment.user = request.user
			#comment.item = item
			#comment.message = comment_text
			#comment.save()

class ItemForm(ModelForm):
	"""
	Holding class.
	"""
	class Meta:
		model = Item

class IssueForm(forms.Form):
	"""
	Standard Issue form.
	"""
	subject = forms.CharField(label = 'Subject', max_length = 2000, required = True)
	url = forms.CharField(label = 'URL', required = False, max_length = 2000)
	tags = forms.CharField(label = 'Tags', max_length = 2000, required = False)
	comments = forms.CharField(label = 'Comments', widget = forms.widgets.Textarea(), required = False)
	priority_choices = [(item.id, item.name) for item in Priority.objects.all().order_by('-id')]
	priority = forms.ChoiceField(label = 'Priority', choices = priority_choices)
	delivery_notes = forms.CharField(label = 'Delivery Notes', widget = forms.widgets.Textarea(), required = False)

class IssueProcess(object):
	"""
	Process an Issue form.
	"""
	def load(self, request, item, linked_item, extra):
		"""
		Return a dict to populate the form with an instance.
		"""
		extra['buttons_update'] = True
		return {
			'subject' : item.description,
			'tags' : item.tags,
			'url' : linked_item.url,
			'priority' : item.priority.id,
			'delivery_notes' : linked_item.delivery_notes,
		}

	def save(self, request, item, linked_item, linked_item_form):
		"""
		Save the form details into an item and the linked item.
		"""
		#print('called save')
		linked_item.url = linked_item_form.cleaned_data['url']
		item.description = linked_item_form.cleaned_data['subject']
		#item.tags = linked_item_form.cleaned_data['tags'].replace(',', ' ')
		item.priority = Priority.objects.get(id = linked_item_form.cleaned_data['priority'])
		linked_item.delivery_notes = linked_item_form.cleaned_data['delivery_notes']
		#
		# Look for actions other than save
		#
		if request.POST.get('update', '') == 'Completed':
			item.fixed = True
			item.validated = False
		if request.POST.get('update', '') == 'Failed':
			item.fixed = False
			item.validated = True
			item.location = Location.objects.get(name = 'Production')
		if request.POST.get('update', '') == 'Verified':
			item.fixed = True
			item.validated = True

		#print('saving item')
		item.save()
		#print('saving link')
		linked_item.save()

		#
		# Check for comments and add
		#
		comment_text = linked_item_form.cleaned_data['comments'].strip()
		if comment_text != '':
			post_comment(request, item, comment_text)
			#comment = Comment()
			#comment.user = request.user
			#comment.item = item
			#comment.message = comment_text
			#comment.save()

class NoteForm(Form):
	"""
	Note form.
	"""
	subject = forms.CharField(label = 'Subject', max_length = 2000, required = True)
	text = forms.CharField(
		label = 'Notes',
		widget = TinyMCE(
			attrs = { 'cols': 80, 'rows': 30 }
		),
		required = True
	)
	tags = forms.CharField(label = 'Tags', max_length = 2000, required = False)
	comments = forms.CharField(
		label = 'Comments',
		widget = forms.widgets.Textarea(),
		required = False
	)

class NoteProcess(object):
	"""
	Process a Note form.
	"""
	def load(self, request, item, linked_item, extra):
		"""
		Return a dict to populate the form with an instance.
		"""
		extra['buttons_update'] = True
		return {
			'subject' : item.description,
			'tags' : item.tags,
			'text' : linked_item.text,
		}

	def save(self, request, item, linked_item, linked_item_form):
		item.description = linked_item_form.cleaned_data['subject']
		item.tags = linked_item_form.cleaned_data['tags']
		linked_item.text = linked_item_form.cleaned_data['text']
		item.save()
		linked_item.save()

		#
		# Check for comments and add
		#
		comment_text = linked_item_form.cleaned_data['comments'].strip()
		if comment_text != '':
			post_comment(request, item, comment_text)
			#comment = Comment()
			#comment.user = request.user
			#comment.item = item
			#comment.message = comment_text
			#comment.save()

class ChecklistForm(Form):
	"""
	Checklist form.
	"""
	subject = forms.CharField(label = 'Checklist title', max_length = 2000, required = True)
	new_item = forms.CharField(label = 'Add item', max_length = 4000, required = True)

class ChecklistProcess(object):
	"""
	Process checklist form
	"""
	def load(self, request, item, linked_item, extra):
		"""
		Return a dict to populate the form with an instance.
		"""
		extra['buttons_update'] = True
		checklist_items = ChecklistItem.objects.filter(checklist = item).order_by('-order_index')

		extra['checklist_items'] = checklist_items
		return {
			'subject' : item.description,
			'tags' : item.tags,
		}

	def save(self, request, item, linked_item, linked_item_form):
		"""
		Save checklist item.
		"""
		item.description = linked_item_form.cleaned_data['subject']
		item.save()
		checklist_item = ChecklistItem()
		checklist_item.checklist = item
		checklist_item.order_index = 1
		checklist_item.text = linked_item_form.cleaned_data['new_item']
		checklist_item.save()

class BinderForm(Form):
	"""
	Binder form.
	"""
	name = forms.CharField(label = 'Name', max_length = 500, required = True)

class ClientForm(Form):
	"""
	Client form.
	"""
	name = forms.CharField(label = 'Name', max_length = 500, required = True)

class ProjectForm(Form):
	"""
	Project form.
	"""
	name = forms.CharField(label = 'Name', max_length = 500, required = True)

class TargetForm(ModelForm):
	"""
	Target form
	"""
	class Meta:
		model = Target
		fields = (
			'name',
			'deadline',
			'public',
			'active',
		)
	deadline = forms.DateField(widget=SelectDateWidget())

class PasswordForm(Form):
	"""
	Reset password form
	"""
	password = forms.CharField(
		widget = forms.PasswordInput(),
		label = 'Password', max_length = 500, required = True)
	confirm_password = forms.CharField(
		widget = forms.PasswordInput(),
		label = 'Confirm', max_length = 500, required = True)

	def clean_password(self):
		if self.data['password'] != self.data['confirm_password']:
			raise forms.ValidationError('Passwords do not match.')
		return self.data['password']

	def clean_confirm(self):
		return self.data['confirm_password']

	def clean(self,*args, **kwargs):
		self.clean_password()
		self.clean_confirm()
		return super(Form, self).clean(*args, **kwargs)

class RequirementForm(Form):
	"""
	Requirement form
	"""
	subject = forms.CharField(label = 'Requirement For', max_length = 2000, required = True)
	text = forms.CharField(label = 'Additional Details', widget = forms.widgets.Textarea(), required = False)
	tags = forms.CharField(label = 'Tags', max_length = 2000, required = False)
	comments = forms.CharField(label = 'Comments', widget = forms.widgets.Textarea(), required = False)
	priority_choices = [(item.id, item.name) for item in Priority.objects.all()]
	priority = forms.ChoiceField(label = 'Priority', choices = priority_choices)
	delivery_notes = forms.CharField(label = 'Delivery notes', widget = forms.widgets.Textarea(), required = False)

class RequirementProcess(object):
	"""
	Process a requirement form
	"""
	def load(self, request, item, linked_item, extra):
		"""
		Return a dict to populate the form with an instance.
		"""
		fetch_comments = Comment.objects.filter(item = item).order_by('date_time')
		gravatar_queryset(fetch_comments)

		extra['comments'] = fetch_comments
		extra['buttons_update'] = True
		return {
			'subject' : item.description,
			'tags' : item.tags,
			'text' : linked_item.text,
			'priority' : item.priority.id,
			'delivery_notes' : linked_item.delivery_notes,
		}

	def save(self, request, item, linked_item, linked_item_form):
		"""
		Save the Requirement item.
		"""
		item.description = linked_item_form.cleaned_data['subject']
		#item.tags = linked_item_form.cleaned_data['tags']
		linked_item.text = linked_item_form.cleaned_data['text']
		linked_item.delivery_notes = linked_item_form.cleaned_data['delivery_notes']
		item.priority = Priority.objects.get(id = linked_item_form.cleaned_data['priority'])
		#
		# Look for actions other than save
		#
		if request.POST.get('update', '') == 'Completed':
			item.fixed = True
		if request.POST.get('update', '') == 'Failed':
			item.fixed = False
			item.validated = True
		if request.POST.get('update', '') == 'Verified':
			item.fixed = True
			item.validated = True

		item.save()
		linked_item.save()

		#
		# Check for comments and add
		#
		comment_text = linked_item_form.cleaned_data['comments'].strip()
		if comment_text != '':
			post_comment(request, item, comment_text)
			#comment = Comment()
			#comment.user = request.user
			#comment.item = item
			#comment.message = comment_text
			#comment.save()

class EmailForm(ModelForm):
	class Meta:
		model = Email
		#fields = (
		#	'description',
		#)

class EmailProcess(object):
	def load(self, request, item, linked_item, extra):
		read_buffer = self.read_email(str(linked_item.file_id))
		extra['email_body'] = '\n'.join(email_return_body(read_buffer)).replace('=20', '')
		extra['buttons_update'] = False
		return {
		}

	def save(self, request, item, linked_item, linked_item_form):
		pass

	def read_email(self, id):
		email_dir = os.path.join(settings.MEDIA_ROOT, 'emails')
		file_name = os.path.join(email_dir, id)
		if os.path.exists(file_name):
			buffer = open(file_name, 'rt')
			read_buffer = buffer.read()
			buffer.close()
		else:
			read_buffer = ''
		return read_buffer

def login(request):
	#from mobile.sniffer.wurlf.sniffer import WurlfSniffer

	#sniffer = WurlfSniffer()

	return render_to_response(
		'ledger/login.html',
		{

		},
		context_instance = RequestContext(request),
	)

class GridRow(object):
	"""
	Holding item for grids
	"""
	def __init__(self):
		self.name = None
		self.items = []

class GridItem(object):
	"""
	Holding item for grid items
	"""
	def __init__(self):
		self.count = 0
		self.location = ''

class BinderProject(object):
	def __init__(self):
		self.project = None
		self.chart = []
		self.chart_data = {}

class ChartBasicItem(object):
	def __init__(self):
		self.day = None
		self.reported = 0
		self.production = 0
		self.testing = 0
		self.delivered = 0


def latest_updates(request):
	"""
	Return the latest updates
	"""
	#
	# Clicked on a day
	#
	if request.GET.get('day', '') != '':
		feed = Feed.objects.filter(
			user = request.user,
			date_time__gt = datetime.datetime(
				int(request.GET.get('year')),
				int(request.GET.get('month')),
				int(request.GET.get('day')),
				0,
				0,
				0
			),
			date_time__lt = datetime.datetime(
				int(request.GET.get('year')),
				int(request.GET.get('month')),
				int(request.GET.get('day')),
				23,
				59,
				59
			)
		).order_by('-date_time')
		updates_header = request.GET.get('day') + '/' + datetime.date(1900, int(request.GET.get('month')), 1).strftime('%B') + '/' + request.GET.get('year')
	elif request.GET.get('month', '') != '':
		feed =[]
		pass
		feed = Feed.objects.filter(
			user = request.user,
			date_time__gt = datetime.datetime(
				int(request.GET.get('year')),
				int(request.GET.get('month')),
				1,
				0,
				0,
				0
			),
			date_time__lt = datetime.datetime(
				int(request.GET.get('year')),
				int(request.GET.get('month')),
				calendar.monthrange(int(request.GET.get('year')), int(request.GET.get('month')))[1],
				23,
				59,
				59
			)
		).order_by('-date_time')
		updates_header = datetime.date(1900, int(request.GET.get('month')), 1).strftime('%B') + '/' + request.GET.get('year')
	else:
		feed = Feed.objects.filter(
			user = request.user,
			date_time__gt = datetime.datetime.now() - datetime.timedelta(days = 3)
		).order_by('-date_time')
		updates_header = 'Latest Updates'
		if not request.user.is_staff:
			feed = feed.filter(item__assigned_to = request.user)
	return updates_header, feed

def post_comment(request, item, comment_text):
	"""
	Attach a comment to an item.

	Parameters:
		| item - the item to attach the comment to
		| comment_text - free form text from the user

	"""
	fetch_comments = Comment.objects.filter(item = item).order_by('date_time')
	user_set = set()
	for loop_comment in fetch_comments:
		if loop_comment.user not in user_set:
			user_set.add(loop_comment.user)

	for loop_user in user_set:
		feed = Feed()
		feed.description = '<span class="floatRight"><img src="/media/layout/icons/comment.png" /></span>%s %s has commented on <a href="/roadmap/ledger/item/%s">%s</a>' % (
			request.user.first_name, request.user.last_name, item.id, escape(item.description)
		)
		feed.date_time = datetime.datetime.now()
		feed.user = loop_user
		feed.author = request.user
		feed.item = item
		feed.save()
	comment = Comment()
	comment.user = request.user
	comment.item = item
	comment.message = comment_text
	comment.date_time = datetime.datetime.now()
	comment.save()

@login_required
def home(request):
	"""
	Dashboard
	"""
	follow_ups = Item.objects.filter(assigned_to = request.user, follow_up = True)

	location = Location.objects.all()
	for item in location:
		count_items = Item.objects.filter(location = item).count()
		item.count_items = count_items

	grid = []
	client_order = request.session.get('client_order', list())
	order_index = len(client_order)
	project_setting = None
	try:
		project_setting = ProjectSetting.objects.get(const = 'VIEWPREFERENCES_DEFAULT_VIEWSTATE')
	except ProjectSetting.DoesNotExist:
		pass
	for loop_client in Client.objects.all():
		if loop_client.slug == '':
			loop_client.slug = slugify(loop_client.name)
			loop_client.save()
		order_index+=1

		row = GridRow()
		row.client = loop_client

		if loop_client in client_order:
			row.client_order_index = client_order.index(loop_client)
		else:
			row.client_order_index = order_index

		row.projects = []
		include_client = False

		for loop_binder in Binder.objects.filter(client = loop_client, active = True):
			if request.user in loop_binder.all_users():
				for loop_project in Project.objects.filter(binder = loop_binder):

					project_row = GridRow()
					project_row.project = loop_project
					project_row.binder = loop_binder
					project_row.client = loop_binder.client

					items = Item.objects.filter(Q(state = 0, project = loop_project, assigned_to = request.user))
					items = items.exclude(item_type = Type.objects.get(name = 'Email'))
					items = items.exclude(item_type = Type.objects.get(name = 'Note'))
					items = items.exclude(item_type = Type.objects.get(name = 'File'))

					project_row.your_items = items.count()
					#project_row.total_items = items.count()

					#project_row.default_location = default_location

					#
					# Get the viewsettings
					#
					view_settings = ''
					try:
						user_project_setting = UserProjectSetting.objects.get(
							Q(
								project = loop_project,
								user = request.user,
								project_setting = project_setting
							)
						)
						view_settings = user_project_setting.value
					except UserProjectSetting.DoesNotExist:
						pass
					project_row.view_settings = view_settings
				#if project_row.your_items > 0:
					row.projects.append(project_row)
					include_client = True

			if include_client:
				grid.append(row)

	grid = sorted(grid, key=attrgetter('client_order_index'))

	#updates_header, feed = latest_updates(request)
	#gravatar_queryset(feed)

	client_order = request.session.get('client_order', list())

	return render_to_response(
		'ledger/home.html',
		{
			'follow_ups': follow_ups,
			'location': location,
			#'project': project,
			#'feed': feed,
			'settings': settings,
			'grid': grid,
			'calendar_output': mini_calendar(request),
			#'updates_header': updates_header,
			'headernav': 'home',
			'active_items': active_items(request),
			'clients': Client.objects.all().order_by('name'),
			'client_order' : client_order,
		},
		context_instance = RequestContext(request),
	)

@login_required
def add_linked_item_popup(request):
	item = Item.objects.get(id = request.GET.get('id'))
	if user_can_view(request, item):
		project = item.project

		filter_list = Q(project = project, state = 0, item_type = Type.objects.get(name = 'Note'))
		note_items = Item.objects.filter(filter_list).order_by('id')

		filter_list = Q(project = project, state = 0, item_type = Type.objects.get(name = 'File'))
		file_items = Item.objects.filter(filter_list).order_by('id')

		items = Item.objects.filter(
			Q(project = project, state = 0),
			Q(item_type = Type.objects.get(name = 'Issue')) | Q(item_type = Type.objects.get(name = 'Requirement'))
		).order_by('id')
	else:
		items = []

	return render_to_response(
		'ledger/items/add_linked_item.html',
		{
			'items': items,
			'file_items': file_items,
			'note_items': note_items,
			'item': item,
		},
		context_instance = RequestContext(request),
	)

@csrf_exempt
@login_required
def attach_new_file(request):
	item_id = None
	try:
		if request.method == 'POST':
			#
			# Get the main item to copy details from
			#
			item_id = request.POST.get('item_id')
			print('item id %s' % item_id)
			main_item = Item.objects.get(id = item_id)
			#
			# Add the item to the database
			#
			item = Item()
			item.item_type = Type.objects.get(name = 'File')
			item.location = main_item.location
			item.state = 0
			item.project = main_item.project
			item.assigned_to = main_item.assigned_to
			item.priority = main_item.priority

			linked_item = File()
			form_file = request.FILES['file']
			dir_name = str(uuid.uuid1())
			plain_name = dir_name + '/' + form_file.name
			item.description = '%s' % form_file.name
			print('saving item')
			item.save()
			print('new id %s' % item.id)

			os.makedirs(os.path.join(settings.MEDIA_ROOT, 'documents', dir_name))
			file_name = os.path.join(settings.MEDIA_ROOT, 'documents', plain_name)
			spool = open(file_name, 'wb')
			for chunk in form_file.chunks():
				spool.write(chunk)
			spool.close()
			linked_item.file = plain_name
			print('setting file to %s' % plain_name)
			linked_item.name = form_file.name
			print('setting name to %s' % linked_item.name)
			if linked_item.name.find('.') != -1:
				linked_item.filetype = linked_item.name[linked_item.name.rfind('.'):]
				print('setting filetype to %s' % linked_item.filetype)

			#
			# link the linked_item in
			#
			linked_item.item = Item.objects.get(id = item.id)
			print('saving linked item')
			linked_item.save()

			#item.linked_item = linked_item
			print('saving item')
			item.save()

			#
			# Track it. We have to wait until item was saved before we can save the assigned record.
			#
			assigned = Assigned()
			assigned.item = item
			assigned.user = request.user
			assigned.location = item.location
			assigned.comments = "Created"
			assigned.save()

			link_items_process(request, main_item, item)
	except Exception, ex:
		pass
	#	print('%s' % ex)
	#	raise ex
	return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
	return HttpResponseRedirect('/roadmap/ledger/item/%s' % item_id)

@csrf_exempt
@login_required
def item_link_item(request, item = None, linked_item = None):
	if item == None:
		item = request.POST.get('item_id')
	if linked_item == None:
		linked_item = request.POST.get('linked_item_id')

	item = Item.objects.get(id = item)
	linked_item = Item.objects.get(id = linked_item)

	link_items_process(request, item, linked_item)

	return render_to_response(
		'ledger/objects/extra_details.html',
		{
			'item': item,
			'priorities' : Priority.objects.all().order_by('-order'),
			'project' : Project.objects.filter(binder = item.project.binder),
			'users' : item.project.binder.team.all(),
			'location' : Location.objects.all(),
			'targets' : Target.objects.filter(
				Q(project = item.project, user = request.user, public = 0) | Q(project = item.project, public = 1)
			).filter(active = True),
			'related_items' : get_tagged_related_items(item),
		},
		context_instance = RequestContext(request),
	)

def link_items_process(request, item, linked_item):
	if user_can_view(request, item) and user_can_view(request, linked_item):
		item.associated_items.add(linked_item)

		if item.assigned_to != request.user:
			item.unseen = True

		linked_item.associated_items.add(item)
		if linked_item.assigned_to != request.user:
			linked_item.unseen = True

		item.save()
		linked_item.save()

		comment = Comment()
		comment.user = request.user
		comment.item = item
		comment.message = '<img src="/media/layout/icons/%s.png" /> <a href="/roadmap/ledger/item/%s">%s</a>' % (
			linked_item.item_type, linked_item.id, linked_item.description
		)
		comment.date_time = datetime.datetime.now()
		comment.save()

		comment = Comment()
		comment.user = request.user
		comment.item = linked_item
		comment.message = '<img src="/media/layout/icons/%s.png" /> <a href="/roadmap/ledger/item/%s">%s</a>' % (
			item.item_type, item.id, item.description
		)
		comment.date_time = datetime.datetime.now()
		comment.save()

def user_can_view(request, item):
	#
	# work out what type of object this is, and try to get back to the binder
	#
	binder = item

	if type(item) == Item:
		binder = item.project.binder

	if type(item) == Project:
		binder = item.binder

	if request.user == binder.owner:
		return True
	if request.user in binder.reporters.all():
		return True
	if request.user in binder.producers.all():
		return True

def user_for_binder(request, binder):
	"""
	Return a list of all the unique members of the binder.
	"""
	user_set = set()
	user_set.add(binder.owner)
	for loop_user in binder.reporters.all():
		if loop_user not in user_set:
			user_set.add(loop_user)
	for loop_user in binder.producers.all():
		if loop_user not in user_set:
			user_set.add(loop_user)
	return user_set


@login_required
def download(request, filename):
	import mimetypes
	mimetypes.init()

	filename_split = filename.split('/')
	plain_filename = filename_split[len(filename_split) - 1]
	mime_type = mimetypes.guess_type(plain_filename)
	file_name = os.path.join(settings.MEDIA_ROOT, 'documents', filename)
	spool = open(file_name, 'rb')
	buffer = spool.read()
	spool.close()

	response = HttpResponse(buffer, mimetype='%s/%s' % (mime_type[0], mime_type[1]))
	response['Content-Disposition'] = 'attachment; filename=%s' % plain_filename
	return response

def active_items(request):
	active_items = []
	project_setting = None
	try:
		project_setting = ProjectSetting.objects.get(const = 'VIEWPREFERENCES_DEFAULT_VIEWSTATE')
	except ProjectSetting.DoesNotExist:
		pass
	#if request.user:
	for loop_binder in Binder.objects.filter(active = True).order_by('client__name'):
		for loop_project in Project.objects.filter(binder = loop_binder).order_by('name'):
			default_location = None
			if request.user in loop_binder.reporters.all():
				default_location = Location.objects.get(name = 'Testing')
			if request.user in loop_binder.producers.all():
				default_location = Location.objects.get(name = 'Production')
			if request.user == loop_binder.owner:
				default_location = Location.objects.get(name = 'Reported')

			if default_location:
				view_settings = ''
				try:
					user_project_setting = UserProjectSetting.objects.get(
						Q(
							project = loop_project,
							user = request.user,
							project_setting = project_setting
						)
					)
					view_settings = user_project_setting.value
				except UserProjectSetting.DoesNotExist:
					pass
				data = {}
				data['project'] = loop_project.slug
				data['binder'] = loop_binder.slug
				data['location'] = default_location
				data['client'] = loop_binder.client.slug
				data['client_name'] = loop_binder.client
				data['project_name'] = loop_project.name
				data['binder_name'] = loop_binder.name
				data['view_settings'] = view_settings
				active_items.append(data)
	return active_items


@login_required
def selected_items(request):
	selected_items = []
	for loop_item in request.session['selected_items']:
		selected_items.append(loop_item[1:])
	items = Item.objects.filter(Q(id__in = selected_items))

	return render_to_response(
		'ledger/items/selected_items.html',
		{
			'items': items,
			'selected_items': request.session.get('selected_items', []),
			'selected_items_count': len(request.session.get('selected_items',[])),
			'order_by': '',
			'h2text' : 'Selected Items',
			'active_items' : active_items(request),
		},
		context_instance = RequestContext(request),
	)


@login_required
def recently_viewed_items(request):
	items = request.session.get('recently_viewed_items', [])

	return render_to_response(
		'ledger/items/recently_viewed_items.html',
		{
			'items': items,
			'selected_items': [],
			'selected_items_count': 0,
			'order_by': '',
			'h2text' : 'Recently Viewed Items',
			'active_items' : active_items(request),
			'clients': Client.objects.all().order_by('name'),
		},
		context_instance = RequestContext(request),
	)

def get_update_items(request):
	update_items = Item.objects.filter(
		Q(assigned_to = request.user),
		Q(unseen = True) | Q(follow_up = True)
	)
	if request.GET.get('order_by', '') != '':
		update_items = update_items.order_by('project', 'location', request.GET.get('order_by'))
	else:
		update_items = update_items.order_by('project', 'location')
	return update_items


@login_required
def my_items(request):
	items = Item.objects.filter(
		Q(assigned_to = request.user),
		Q(unseen = True) | Q(follow_up = True)
	)

	if request.GET.get('order_by', '') != '':
		items = items.order_by('project', 'location', request.GET.get('order_by'))
	else:
		items = items.order_by('project', 'location')

	location_list = Location.objects.exclude(method = constants.LOCATION_DELETED)

	return render_to_response(
		'ledger/items/my_items.html',
		{
			'items': items,
			'location_list' : location_list,
			'selected_items': [],
			'selected_items_count': 0,
			'order_by': request.GET.get('order_by', ''),
			'h2text' : 'Updated Items',
			'active_items' : active_items(request),
		},
		context_instance = RequestContext(request),
	)

class SearchStructure(object):
	def __init__(self):
		self.name = 'Filter'
		self.assigned_to = []
		self.item_states = []
		self.locations = []
		self.item_target = None
		self.tags = ''
		self.order_by = None
		self.hide_reminders = True
		self.items = []

def parse_querystring_filter(request, search_data):
	#
	# Get querystring data
	#
	if request.GET.get('tags', None) != None:
		search_data.tags = request.GET.get('tags', '').strip()
		search_data.tags = search_data.tags.replace(',', ' ')
		search_data.tags = search_data.tags.lower()
	#
	# Assigned To
	#
	if len(request.GET.getlist('at')) != 0:
		search_data.assigned_to = []
		for loop_value in request.GET.getlist('at'):
			search_data.assigned_to.append(int(loop_value))
	#
	# Item states
	#
	if len(request.GET.getlist('its')) != 0:
		search_data.item_states = []
		for loop_value in request.GET.getlist('its'):
			search_data.item_states.append(int(loop_value))
	#
	# Target
	#
	if request.GET.get('ita', '') != '':
		search_data.item_target = request.GET.get('ita', '')
		if search_data.item_target != '':
			search_data.item_target = int(search_data.item_target)
		else:
			search_data.item_target = None
	#
	# Now order it
	#
	if request.GET.get('order_by', '') != '':
		search_data.order_by = request.GET.get('order_by', '')
	#
	# Reminders
	#
	if request.GET.get('filterReminders', '') != '':
		search_data.hide_reminders = False
	#
	# Locations
	#
	if len(request.GET.getlist('il')) != 0:
		search_data.locations = []
		for loop_value in request.GET.getlist('il'):
			search_data.locations.append(int(loop_value))
	return search_data


def parse_form_filter(request, search_data):
	#
	# Get querystring data
	#
	if request.POST.get('tags', None) != None:
		search_data.tags = request.POST.get('tags', '').strip()
		search_data.tags = search_data.tags.replace(',', ' ')
		search_data.tags = search_data.tags.lower()
	#
	# Assigned To
	#
	if len(request.POST.getlist('at')) != 0:
		search_data.assigned_to = []
		for loop_value in request.POST.getlist('at'):
			search_data.assigned_to.append(int(loop_value))
	#
	# Item states
	#
	if len(request.POST.getlist('its')) != 0:
		search_data.item_states = []
		for loop_value in request.POST.getlist('its'):
			search_data.item_states.append(int(loop_value))
	#
	# Target
	#
	if request.POST.get('ita', '') != '':
		search_data.item_target = request.POST.get('ita', '')
		if search_data.item_target != '':
			search_data.item_target = int(search_data.item_target)
		else:
			search_data.item_target = None
	#
	# Now order it
	#
	if request.POST.get('order_by', '') != '':
		search_data.order_by = request.POST.get('order_by', '')
	#
	# Reminders
	#
	if request.POST.get('filterReminders', '') != '':
		search_data.hide_reminders = False
	#
	# Locations
	#
	if len(request.POST.getlist('il')) != 0:
		search_data.locations = []
		for loop_value in request.POST.getlist('il'):
			search_data.locations.append(int(loop_value))
	return search_data


@login_required
def new_project_filter(request, project_id):
	project = Project.objects.get(id = project_id)

	default_filter = ProjectItemFilter()
	default_filter.name = 'New View'
	default_filter.default = False
	default_filter.search_id = str(uuid.uuid1())
	default_filter.user = request.user
	default_filter.tags = ''
	default_filter.save()

	project.project_filters.add(default_filter)

	return HttpResponseRedirect(
		reverse(
			items,
			kwargs = {
				'project_name': project.slug,
				'binder_name': project.binder.slug,
				'client_name': project.binder.client.slug,
			}
		) + '?searchId=%s' % default_filter.search_id
	)

@login_required
def items(request, client_name = None, binder_name = None, project_name = None, location_name = None, target_name = None):
	"""
	The main items page.

	This function tries to show a list of items depending on the binder_name, project_name, location_name and target_name passed in.
	These are optional.

	Querystring parameters available:
		| moveTo - Update
		| assigned_to - a username
		| location - the location description to filter by
		| selected - show selected items
		| completed - [true|false] show completed items
		| validated - [true|false] show validated items
		| tags - tags to filter by
		| ClearTags - action to clear the tags
		| target - target to filter by
		| reminders - not blank to show the reminder items. Otherwise reminders are hidden
	"""
	if request.GET.get('moveTo', '') == 'Edit':
		return move(request)

	search_list = request.path
	project = None

	if request.GET.get("ClearTags", "") != "":
		search_data.tags = ""
		request.session['selected_items'] = []

	#
	# Get the project
	#
	page = {}
	filters = {}
	filters['state'] = 0
	search = []

	#
	# Project name
	#
	if project_name:
		try:
			project = Project.objects.get(
				Q(
					slug = project_name,
					binder__slug = binder_name
				)
			)
			filters["project"] = project
		except Project.DoesNotExist:
			project_name = "All"
	#
	# Binder Name
	#
	if not project_name and not binder_name:
		try:
			binder = Binder.objects.filter(Q(slug = binder_name))
			project = Project.objects.filter(binder = binder)
			filters["project"] = project
		except Project.DoesNotExist:
			project_name = "All"

	page["project"] = project_name

	search_data = SearchStructure()
	#
	# Get search
	#
	if request.GET.get('searchId', request.POST.get('searchId', '')) != '':
		search_id = request.GET.get('searchId', request.POST.get('searchId', ''))

		if request.POST.get('deleteThisFilter', '') != '':
			delete_candidate = ProjectItemFilter.objects.get(search_id = request.GET.get('searchId'), user = request.user)
			delete_candidate.delete()
			search_id = project.project_filters.get(default = True, user = request.user).search_id

		search_data = load_search(search_id)
		if search_data == None:
			search_data = SearchStructure()
	#
	# No search ID, use the default one
	#
	if request.GET.get('searchId', '') == '':
		user_filters = project.project_filters.filter(default = True, user = request.user)
		#
		# Create a new filter
		#
		if len(user_filters) == 0:
			#
			# Create new filter
			#
			default_filter = ProjectItemFilter()
			default_filter.name = 'Default View'
			default_filter.default = True
			default_filter.search_id = str(uuid.uuid1())
			default_filter.user = request.user
			default_filter.save()

			project.project_filters.add(default_filter)
		#
		# Get the default filter
		#
		search_id = project.project_filters.get(default = True, user = request.user).search_id
		attempt_to_load = load_search(search_id)
		if attempt_to_load != None:
			search_data = attempt_to_load
	#
	# Now try and parse the querystring
	#

	search_data = parse_querystring_filter(request, search_data)
	search_data = parse_form_filter(request, search_data)

	if request.POST.get('filterName', '') != '' and  request.POST.get('deleteThisFilter', '') == '':
		fetch_filter = project.project_filters.get(search_id = search_id)
		fetch_filter.name = request.POST.get('filterName')
		fetch_filter.save()

	#
	# Don't show emails or notes by default
	#
	search_data.tags = search_data.tags.replace(',', ' ')

	if len(search_data.assigned_to) == 0:
		assigned_to_list = project.binder.team.all()
	else:
		assigned_to_list = User.objects.filter(id__in = search_data.assigned_to)
	filters['assigned_to__in'] = assigned_to_list

	if len(search_data.item_states) == 0:
		item_states_list = ItemState.objects.all()
	else:
		item_states_list = ItemState.objects.filter(id__in = search_data.item_states)
	filters['item_state__in'] = item_states_list

	#
	# Locations
	#
	if len(search_data.locations) == 0:
		location_list = Location.objects.filter(project = project).order_by('order')
	else:
		location_list = Location.objects.filter(id__in = search_data.locations).order_by('order')
	filters['location__in'] = location_list

	#
	# If we're searching by tag, use them to retrieve the first resultset, then filter
	#
	if search_data.tags != '':
		tag_split = search_data.tags.split(' ')

		tag_list = []
		ignored_tags = []
		tags_searched = []
		for item in tag_split:
			strip_item = item.strip()
			try:
				tag = Tag.objects.get(name = strip_item)
				tag_list.append(tag)
				tags_searched.append(strip_item)
			except Tag.DoesNotExist:
				if strip_item != '':
					tags.replace(item, '')
					ignored_tags.append(item)
		items = TaggedItem.objects.get_by_model(Item, tag_list)
		items = items.filter(**filters)
	else:
		items = Item.objects.filter(**filters)

	#
	# Filter out any milestone
	#
	if search_data.item_target != None and search_data.item_target != 0:
		items = items.filter(
			Q(targets__id = search_data.item_target, targets__user = request.user, targets__public = 0) |
			Q(targets__id = search_data.item_target, targets__public = 1)
		)

	# don't show files
	items = items.exclude(item_type = Type.objects.get(name = 'File'))
	items = items.exclude(item_type = Type.objects.get(name = 'Email'))
	items = items.exclude(item_type = Type.objects.get(name = 'Note'))
	#items = items.exclude(location__method = constants.LOCATION_DELETED)

	#
	# Reminders
	#
	hidden_reminders = None

	if search_data.hide_reminders:
		hidden_reminders = items.filter(reminder__gt = datetime.datetime.now())
		items = items.exclude(reminder__gt = datetime.datetime.now())

	#
	# Sort the resultset if user's clicked on a heading
	#
	if search_data.order_by != None:
		items = items.order_by('location', 'item_group', search_data.order_by)
	else:
		items = items.order_by('location', 'item_group', )

	if project != None:
		try:
			page['project_id'] = project.id
		except:
			pass
	page['project_item'] = project

	#
	# Limited user can only see their own items
	#
	if request.user in project.binder.reporters.all():
		items = items.filter(assigned_to = request.user)

	if 'selected_items' not in request.session.keys():
		request.session['selected_items'] = []

	#
	# Now save the search
	#
	search_id = save_search(request, items, search_data, search_id)

	#
	# Group the items into locations
	#
	for loop_location in location_list:
		loop_location.items = []
		loop_location.item_count = 0
		loop_location.items = [	loop_item for loop_item in items if loop_item.location == loop_location ]
		loop_location.item_count = len(loop_location.items)

	#
	# Move the client up the homepage
	#
	recently_viewed_client(request, project.binder.client)

	#
	# Find all unique groups
	#
	item_groups = set()
	for loop_item in items:
		if loop_item.item_group != None:
			item_groups.add(loop_item.item_group)

	user_filters = project.project_filters.filter(user = request.user)

	item_count = items.count()
	page["itemcount"] = '%s item' % (item_count)
	if item_count > 1:
		page['itemcount'] += 's'

	return render_to_response(
		'ledger/items/items.html',
		{
			'search_data': search_data,
			'item_states_list2': item_states_list,
			'location': location_name,
			'loop_location': loop_location,
			'page': page,
			'items': items,
			'search': search,
			'hide_reminders': search_data.hide_reminders,
			'search_id': search_id,
			'headernav': 'active',
			'active_items': active_items(request),
			'selected_items': request.session.get('selected_items', []),
			'selected_items_count': len(request.session.get('selected_items',[])),
			'user_filters': user_filters,
			#'show_selected_items': search_data.show_selected,
			'assigned_to': search_data.assigned_to,
			'order_by': search_data.order_by,
			'item_target' : search_data.item_target,
			'targets' : Target.objects.filter(Q(project = project, user = request.user, public = 0) | Q(project = project, public = 1)).filter(active = True),
			'location_list': location_list,
			'locations': Location.objects.filter(project = project).order_by('order'),#.exclude(method = constants.LOCATION_DELETED),
			'item_states': ItemState.objects.all(),
			'hidden_reminders': hidden_reminders,
			'item_groups': item_groups,
			'request': request,
			'assigned_to_list': assigned_to_list,
			#'item_states_list': item_states_list,
		},
		context_instance = RequestContext(request),
	)

@login_required
# url(r'^javascript/show_hide/(?P<project_id>.+)/(?P<location_id>.+)/(?P<show>.+)$', 'views.items_expand_location'),
def items_expand_location(request):
	project_id = request.GET.get('project_id')
	location_id = request.GET.get('location_id')
	show = request.GET.get('show')
	project = Project.objects.get(id=project_id)
	location = Location.objects.get(id=location_id)
	location_expander = request.session.get('location_expander_%s' % (project_id), LocationExpander())
	location_expander.location_expanded[location] = (show == 'show')
	request.session['location_expander_%s' % (project.id)] = location_expander

	return HttpResponse('ok', mimetype='text/plain')


@login_required
def tagged_items(request):
	"""
	List tagged items
	"""
	tags = request.GET.get('tags', '')
	tags = tags.replace(',', ' ')
	tags = tags.lower()
	tag_split = tags.split(' ')
	tag_list = []
	ignored_tags = []
	tags_searched = []
	for item in tag_split:
		strip_item = item.strip()
		try:
			tag = Tag.objects.get(name = strip_item)
			tag_list.append(tag)
			tags_searched.append(strip_item)
		except Tag.DoesNotExist:
			if strip_item != '':
				tags.replace(item, '')
				ignored_tags.append(item)
	items = TaggedItem.objects.get_by_model(Item, tag_list)
	return render_to_response(
		'ledger/items/tagged_items.html',
		{
			'items': items,
			'selected_items': [],
			'selected_items_count': 0,
			'h2text' : 'Tagged Items',
			'active_items' : active_items(request),
			'tags': tags,
			'clients': Client.objects.all().order_by('name'),
		},
		context_instance = RequestContext(request),
	)


@login_required
def active(request, client_name = None, binder_name = None, project_name = None, location_name = None):
	#print('Active %s %s %s %s ' % (client_name, binder_name, project_name, location_name))
	#
	# check for command buttons
	#
	#if request.method == 'POST':
	if request.GET.get('moveTo', '') != '':
		return move(request)

	search_list = request.path

	#
	# My active items list.
	#
	assigned_to = request.GET.get('assigned_to', request.user.username)

	project = None
	if not location_name:
		location_name = request.GET.get("location", "All")
	if not project_name:
		project_name = request.GET.get("project", "All")
		project_id = request.GET.get("project_id", 0)
	else:
		project = Project.objects.get(Q(slug = project_name))
	if not binder_name:
		binder_name = request.GET.get("binder", "All")
	show_selected = False
	if request.GET.get('selected', '') != '':
		show_selected = True

	show_completed = (request.GET.get('completed', 'false').lower() == 'true')
	show_validated = (request.GET.get('validated', 'false').lower() == 'true')

	tags = request.GET.get("tags", "")
	if request.GET.get("ClearTags", "") != "":
		tags = ""
		request.session['selected_items'] = []
		return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
	#
	# Don't show emails or notes by default
	#
	show_emails = request.GET.get('emails', '') != ''
	show_notes = request.GET.get('notes', '') != ''
	target = request.GET.get('target', '')
	tags = tags.replace(',', ' ')
	page = {}
	filters = {}
	filters['state'] = 0
	search = []

	if tags != "":
		#print('1')
		try:
			project = Project.objects.get(Q(slug = project_name, binder=Binder.objects.get(slug=binder_name)))
			page['project'] = project.name
		except Exception,ex:
			#print(ex)
			pass
		tags = tags.lower()
		tag_split = tags.split(' ')
		tag_list = []
		ignored_tags = []
		tags_searched = []
		for item in tag_split:
			strip_item = item.strip()
			try:
				tag = Tag.objects.get(name = strip_item)
				tag_list.append(tag)
				tags_searched.append(strip_item)
			except Tag.DoesNotExist:
				if strip_item != '':
					tags.replace(item, '')
					ignored_tags.append(item)
		page["tags"] = ' '.join(tags_searched)
		page["location"] = "All"

		if location_name:
			try:
				location = Location.objects.get(name = location_name)
				filters["location"] = location
				#print('Location: %s' % location)
			except Location.DoesNotExist:
				location_name = "All"
		page["location"] = location_name

		page["ignoredtags"] = ' '.join(ignored_tags)

		items = TaggedItem.objects.get_by_model(Item, tag_list)
		search = Item.objects.filter(description__icontains = tags)
	else:
		#print('No tags')

		if location_name:
			try:
				location = Location.objects.get(name = location_name)
				filters["location"] = location
				#print('Location: %s' % location)
			except Location.DoesNotExist:
				location_name = "All"
		page["location"] = location_name

		if project_name:
			try:
				project = Project.objects.get(
					Q(
						slug = project_name,
						binder__slug = binder_name
					)
				)
				filters["project"] = project
				#print('Project: %s' % project)
			except Project.DoesNotExist:
				project_name = "All"

		if not project_name and not binder_name:
			try:
				binder = Binder.objects.filter(Q(slug = binder_name))
				project = Project.objects.filter(binder = binder)
				filters["project"] = project
			except Project.DoesNotExist:
				project_name = "All"

		page["project"] = project_name

		if assigned_to == 'all':
			pass
		else:
			filters["assigned_to"] = User.objects.get(username=assigned_to) #request.user

		items = Item.objects.filter(**filters)

	if target != '':
		items = items.filter(
			Q(targets__slug = target, targets__user = request.user, targets__public = 0) |
			Q(targets__slug = target, targets__public = 1)
		)

	try:
#		Target.objects.filter(Q(project = item.project, user = request.user, public = 0) | Q(project = item.project, public = 1)),
		target = Target.objects.get(Q(slug = target, user = request.user, public = 0) | Q(slug = target, public = 1))
		#print('found targegt')
	except Exception, ex:
		#print('Exception %s' % ex)
		target = None
		pass
		#filters['targets__slug'] = target

	if show_selected:
		selected_items = []
		for loop_item in request.session['selected_items']:
			selected_items.append(loop_item[1:])
		items = Item.objects.filter(Q(id__in = selected_items))

	completed_count = None
	validated_count = None
	#
	# Production view, filter completed items
	#
	if request.GET.get('location', '') == 'Production':
		if show_completed:
			pass
		else:
			completed_count = items.filter(fixed = True).count()
			items = items.exclude(fixed  = True)
	#
	# Testing view, filter verified
	#
	if request.GET.get('location', '') == 'Testing':
		if show_validated:
			pass
		else:
			validated_count = items.filter(validated = True).count()
			items = items.exclude(validated = True)

	count_emails = []
	if project != None:
		count_emails = Item.objects.filter(
			item_type = Type.objects.get(name = 'Email'),
			project = project,
			state = 0
		)
	count_notes = Item.objects.filter(
		item_type = Type.objects.get(name = 'Note'),
		project = project,
		state = 0
	)

	# don't show files
	items = items.exclude(item_type = Type.objects.get(name = 'File'))
	if not show_emails:
		items = items.exclude(item_type = Type.objects.get(name = 'Email'))
	else:
		items = items.filter(item_type = Type.objects.get(name = 'Email'))
	if not show_notes:
		items = items.exclude(item_type = Type.objects.get(name = 'Note'))
	else:
		items = items.filter(item_type = Type.objects.get(name = 'Note'))
	#items = items.exclude(location = Location.objects.get(method = constants.LOCATION_DELETED))

	if request.GET.get('order_by', '') != '':
		items = items.order_by(request.GET.get('order_by'))

	#page['count_emails'] = str(count_emails.count())
	#print(page['count_emails'] )
	#page['count_notes'] = str(count_notes.count())
	item_count = items.count()
	page["itemcount"] = '%s item' % (item_count)
	if item_count > 1:
		page['itemcount'] += 's'

	if project != None:
		try:
			page['project_id'] = project.id
		except:
			pass
	page['project_item'] = project

	if 'selected_items' not in request.session.keys():
		request.session['selected_items'] = []


	if not request.user.is_staff:
		items = items.filter(assigned_to = request.user)

	search_id = save_search(request, items)

	location_list = Location.objects.exclude(method = constants.LOCATION_DELETED).exclude(name = location_name)

	return render_to_response(
		'ledger/active.html',
		{
			'page': page,
			'items': items,
			'search': search,
			'completed': show_completed,
			'validated': show_validated,
			'completed_count': completed_count,
			'validated_count': validated_count,
			'search_id': search_id,
			'headernav': 'active',
			'active_items': active_items(request),
			'selected_items': request.session.get('selected_items', []),
			'selected_items_count': len(request.session.get('selected_items',[])),
			'show_selected_items': show_selected,
			'assigned_to': assigned_to,
			'order_by': request.GET.get('order_by', ''),
			'target' : target,
			'locations': location_list,
		},
		context_instance = RequestContext(request),
	)

def queries(request):
	queries = connection.queries
	output = '<br/>\r\n'.join(item['sql'] for item in queries)
	return HttpResponse(output, mimetype='text/plain')

def save_search(request, recordset, search_data, file_id = None):
	if file_id == None:
		file_id = str(uuid.uuid1())

	#try:
	#	searchData['searchUrl'] = request.META.get('PATH_INFO', '')
	#	searchData['searchUrl'] = searchData['searchUrl'] + '?' + request.META.get('QUERY_STRING', '')
	#except:
	#	pass
	search_data.items = [item.id for item in recordset]
	#searchData['ids'] =

	file_path = os.path.join(settings.MEDIA_ROOT, 'searches', file_id)
	output = open(file_path, 'wb')
	pickle.dump(search_data, output)
	output.close()

	return file_id

def load_search(file_id):
	if not os.path.exists(os.path.join(settings.MEDIA_ROOT, 'searches')):
		os.mkdir(os.path.join(settings.MEDIA_ROOT, 'searches'))
	file_name = os.path.join(settings.MEDIA_ROOT, 'searches', file_id)
	if os.path.exists(file_name):
		read_buffer = open(file_name, 'rb')
		search_data = pickle.load(read_buffer)
		read_buffer.close()
		return search_data
	else:
		return None

@login_required
def back_next(request):
	"""
	Move between items in the current search list when viewing an item's details
	"""
	search_id = request.GET.get('search_id')
	current_id = request.GET.get('current_id')
	direction = request.GET.get('direction')

	try:
		search_data = load_search(search_id)
		items = search_data.items
		index = -1
		found = None
		for item in items:
			index+=1
			if str(item) == str(current_id):
				found = index
		if found != None:
			new_index = found + int(direction)
			if new_index < 0:
				new_index = len(items) -1
			if new_index >= len(items):
				new_index = 0
			attempt_item = items[new_index]
			return HttpResponseRedirect('/roadmap/ledger/item/%s?search_id=%s' % (attempt_item, search_id))
	except Exception, ex:
		print(ex)
		pass
	return HttpResponseRedirect('/roadmap/ledger/no_item')

@csrf_exempt
def select_multiple(request):
	"""
	Add the IDs from a POST key 'search_ids' to the selected_items list
	"""
	search_ids = request.POST.get('search_ids')

	selected_items = request.session['selected_items']
	for item in search_ids.split(','):
		item_key = 'k%s' % item
		if item_key not in selected_items:
			selected_items.append(item_key)
	request.session['selected_items'] = selected_items
	return HttpResponse('ok')

@csrf_exempt
@login_required
def selected_to_group(request):
	"""
	Assign the items in the selected_items list to the group name passed in POST key 'name'
	"""
	selected_items = request.session['selected_items']
	name = request.POST.get('name')
	for id in selected_items:
		new_key = id.replace('k', '')
		item = Item.objects.get(id = new_key)
		if user_can_view(request, item):
			item.item_group = name
			item.save()
	return HttpResponse('ok', 'text/plain')

@csrf_exempt
@login_required
def selected_to_remind(request):
	"""
	Assign the items in the selected_items list to remind the user in X days time.

	The number of days is passed in from the form POST 'days'
	"""
	selected_items = request.session['selected_items']
	days = request.POST.get('days')

	if days == 'nextmonth' or days == 'nextweek':
		if days == 'nextmonth':
			now_date = datetime.date.today()
			next_month = now_date.month + 1
			next_year = now_date.year
			if next_month > 12:
				next_month = 1
				next_year = next_year + 1
			new_date = datetime.date(next_year, next_month, 1)
		if days == 'nextweek':
			new_date = datetime.date.today()
			tomorrow = datetime.timedelta(days = 1)
			new_date += tomorrow
			while calendar.weekday(new_date.year, new_date.month, new_date.day) != 0:
				new_date = new_date + tomorrow
	else:
		new_date = datetime.date.today() + datetime.timedelta(days = int(days))

	for id in selected_items:
		new_key = id.replace('k', '')
		item = Item.objects.get(id = new_key)
		comment = request.POST.get('comment')
		comment_text = '%s %s has requested a reminder on %s %s %s. \n\nReason/Comment:\n%s' % (
			request.user.first_name,
			request.user.last_name,
			new_date.day,
			calendar.month_abbr[new_date.month],
			new_date.year,
			comment
		)
		#if user_can_view(request, item):
		if item.assigned_to == request.user:
			item.reminder = new_date
			item.add_comment(request.user, comment_text)
			item.save()
	request.session['selected_items'] = []
	return HttpResponse('ok', 'text/plain')

@login_required
def select_all_click(request):
	"""
	Add all items in the current search list to the selected_items list
	"""
	search_id = request.REQUEST.get('search_id')
	try:
		searchData = load_search(search_id)
		items = search_data.items
		#print('Search Data %s' % items)
		selected_items = request.session['selected_items']
		for item in items:
			item_key = 'k%s' % item
			#print('Item key %s' % item_key)
			if item_key not in selected_items:
				#print('Adding to selected items')
				selected_items.append(item_key)
		request.session['selected_items'] = selected_items
	except:
		pass
	return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def save_view_settings(request):
	"""
	Save the current viewing settings for the user for the project
	"""
	referrer = request.META.get('HTTP_REFERER')
	url_parts = urlparse.urlparse(referrer)
	net_loc = url_parts[2]
	querystring = url_parts[4]
	#
	# net_loc is always of the format /client/binder/project/items/target
	#
	binder_parts = net_loc.split('/')
	project = Project.objects.get(
		Q(
			binder__slug = binder_parts[2],
			binder__client__slug = binder_parts[1],
			slug = binder_parts[3]
		)
	)
	project_setting = ProjectSetting.objects.get(const = 'VIEWPREFERENCES_DEFAULT_VIEWSTATE')
	try:
		user_project_setting = UserProjectSetting.objects.get(
			Q(
				project = project,
				user = request.user,
				project_setting = project_setting
			)
		)
	except UserProjectSetting.DoesNotExist:
		user_project_setting = UserProjectSetting()
		user_project_setting.project = project
		user_project_setting.user = request.user
		user_project_setting.project_setting = project_setting

	user_project_setting.value = querystring
	user_project_setting.save()

	return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def no_item(request):
	return render_to_response(
		'ledger/no_item.html',
		{
			'headernav' : 'notifications',
			'active_items' : active_items(request),
		},
		context_instance = RequestContext(request),
	)

def move_items(request, item_ids, location_id, binder_id, project_id, user_id='', target_id = ''):
	"""
	Batch update the items who's ids are passed into item_ids with the following parameters:
		| location_id
		| binder_id
		| project_id
		| user_id
		| target_id
	"""
	changed_location = False
	notify_users = []
	move_count = 0
	location = Location.objects.get(id = location_id)
	#deleted_location = Location.objects.get(method = constants.LOCATION_DELETED)
	user_object = None
	if user_id != '':
		user_object = User.objects.get(id=user_id)

	if project_id != None:
		if project_id == 'new':
			project = Project()
			project.binder = Binder.objects.get(id = binder_id)
			new_project_name = request.POST.get('newProject', '').strip()
			if new_project_name == "":
				new_project_name = "Unnamed project"
			project.name = new_project_name
			project.save()
		else:
			project = Project.objects.get(id = project_id)
	apply_tag = request.POST.get('tag', '')

	for loop_item in item_ids:
		strip_loop_item = loop_item.strip()
		if strip_loop_item != '':
			# unselect it
			item_key = 'k%s' % strip_loop_item
			selected_items = request.session['selected_items']
			if item_key in selected_items:
				del(selected_items[selected_items.index(item_key)])

			item = Item.objects.get(id = strip_loop_item)
			this_user_object = user_object
			#
			# Check if we're moving to a different location and notify
			#
			if item.location != location:
				changed_location = True
				if location.name == 'Production':
					for loop_user in item.project.binder.producers.all():
						notify = Notification()
						notify.user = loop_user
						notify.item = item
						notify.text = '%s has been moved to Production' % (item.description)
						#notify.save()

				if location.name == 'Testing':
					#
					# Production --> Testing: Reassign to the reporter
					#
					#print('Production -> Testing')
					if item.location.name == 'Production' and this_user_object == None:
						# Have we got a tester already?
						previous_tester = None
						ownership_list = Assigned.objects.filter(item=item)
						ownership_list.order_by('id')
						for loop_owner in ownership_list:
							#print('checking %s' % loop_owner.user)
							if loop_owner.location == location: # has it been in testing before?
								#print('is previous tester')
								previous_tester = loop_owner.user
								break;
							# We want the previous tester to be the first person who reported it
							if loop_owner.user in item.project.binder.reporters.all() or loop_owner == item.project.binder.owner:
								#print('remembering %s' % loop_owner.user)
								previous_tester = loop_owner.user
						#print('previous tester %s' % previous_tester)
						if previous_tester != None:
							#item.assigned_to = previous_tester
							this_user_object = previous_tester
						item.fixed = True

					for loop_user in item.project.binder.reporters.all():
						notify = Notification()
						notify.user = loop_user
						notify.item = item
						notify.text = '%s has been moved to Testing' % (item.description)
						#notify.save()
			#item.fixed = True
			item.location = location

			if apply_tag != '':
				if item.tags.find(apply_tag) == -1:
					item.tags = item.tags + ' ' + apply_tag

			if changed_location:
				comment = Comment()
				comment.user = request.user
				comment.item = item
				comment.message = '*** Moved to %s ***' % location
				comment.date_time = datetime.datetime.now()
				comment.save()


			if target_id != '':
				#print('target id %s' % target_id)
				for loop_target in item.targets.filter(user=request.user):
					#print('clearing target %s' % loop_target.name)
					item.targets.remove(loop_target)
				target = Target.objects.get(id = target_id)
				#print('attaching target %s ' % target)
				item.targets.add(target)

			if project_id != None:
				item.project = project
			if this_user_object != None:
				item.assigned_to = this_user_object
				if this_user_object != request.user:
					if item.location != deleted_location:
						item.unseen = True

				feed = Feed()
				feed.description = '<a href="/roadmap/ledger/item/%s">%s</a> has been assigned to you.' % (item.id, escape(item.description))
				feed.date_time = datetime.datetime.now()
				feed.user = this_user_object
				feed.item = item
				feed.author = request.user
				feed.save()

				#
				# Track assigned to
				#
				assigned = Assigned()
				assigned.item = item
				assigned.location = item.location
				assigned.user = item.assigned_to
				assigned.comments = "Reassigned"
				assigned.save()
			item.save()
			move_count+= 1
	return move_count

@login_required
def move(request):
	items_moved = False

	if request.GET.get('moveTo', '') == 'Edit':
		item_list = request.GET.getlist('id')
		items = Item.objects.filter(id__in = item_list)
		items_count = items.count()

		if items_count == 0:
			request.flash['item'] = 'You have not selected any items to move.'
			return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

		current_location = None
		current_project = None
		current_binder = None

		if items_count != 0:
			current_location = items[0].location
			current_project = items[0].project
			current_binder = items[0].project.binder

		project = Project.objects.filter(binder = current_binder)
		location = Location.objects.filter(project = project).order_by('order')

		targets = None
		try:
			targets = Target.objects.filter(Q(project = current_project, user = request.user, public = 0) | Q(project = current_project, public = 1))
		except:
			pass

		return render_to_response(
			'ledger/moveTo.html',
			{
				'clients': Client.objects.all(),
				'tag_list': request.GET.get('tags', ''),
				'itemcount': items_count,
				'items': items,
				'location': location,
				'project': project,
				'users' : current_binder.all_users(), #User.objects.all(),
				'active_items': active_items(request),
				'current_location': current_location,
				'current_project': current_project,
				'current_binder': current_binder,
				'targets': targets,
				'referrer': request.META.get('HTTP_REFERER'),
				'return': request.GET.get('return', ''),
			},
			context_instance = RequestContext(request),
		)

	if request.method == 'POST':
		if request.POST.get('moveCancel', '') != '':
			import urllib
			new_url = request.POST.get('referrer', '')
			if new_url == None or new_url == 'None':
				new_url = '/'
			return HttpResponseRedirect(new_url)
			if request.POST.get('return', '') == '':
				return HttpResponseRedirect(
					'/roadmap/ledger/active?location=%s&project=%s&binder=%stags=%s' %
					(
						request.POST.get('back_location', ''),
						request.POST.get('back_project', ''),
						request.POST.get('back_binder', ''),
						urllib.quote(request.POST.get('tags', '')),
					)
				)
			else:
				new_url = request.POST.get('referrer', '')
				if new_url == None or new_url == 'None':
					new_url = '/'
				return HttpResponseRedirect(new_url)

		if request.POST.get('moveSubmit', '') != '':
			item_ids = request.POST.get('items', '')
			location_id = request.POST.get('location', '')
			binder_id = request.POST.get('binder_id', '')
			project_id = request.POST.get('project', '')
			target_id = request.POST.get('target', '')
			user_id = request.POST.get('user', '')
			project = Project.objects.get(id = project_id)

			location = Location.objects.get(id = location_id)

			move_count = move_items(request, item_ids.split(' '), location_id, binder_id, project_id, user_id, target_id)
			items_moved = True
			previous = request.POST.get('referrer')
			if previous == None or previous == 'None':
				previous = '/'
			#previous = '/roadmap/ledger/active?location=%s&project=%s&binder=%s&tags=%s' % (
			#	request.POST.get('back_location', ''),
			#	request.POST.get('back_project', ''),
			#	request.POST.get('back_binder', ''),
			#	urllib.quote(request.POST.get('tags', '')),
			#)

	if items_moved:
		request.flash['item'] = u'<a href="/roadmap/ledger/profile/%s">%s %s</a> moved %s items to %s' % (
			request.user.username,
			request.user.first_name,
			request.user.last_name,
			move_count,
			location.name
		)
		for user in User.objects.all():
			feed = Feed()
			feed.description = u'<a href="/roadmap/ledger/profile/%s">%s %s</a> moved %s items to %s &gt; %s %s ' % (
				request.user.username,
				request.user.first_name,
				request.user.last_name,
				move_count,
				project.binder.name,
				project.name,
				location.name,
			)
			feed.date_time = datetime.datetime.now()
			#print(feed.date_time)
			feed.user = user
			feed.author = request.user
			feed.save()

		tags = request.POST.get('tags', '')
		request.session['selected_items'] = []

		#return HttpResponseRedirect(request.POST.get('referrer', ''))
		return HttpResponseRedirect(previous)



@login_required
def new_item(request, item_type, project_id = None):
	"""
	Add a new item.

	Location:
	If the user is in producers group, the item will default to producers
	If the user is in reporters group, the item reverts back to reporters.
	"""

	item = Item()
	item.item_type = Type.objects.get(name = item_type)
	item.location = Location.objects.get(method = 'report')
	item.state = 1
	if project_id == None:
		project_id = request.GET.get('project')
		project = Project.objects.get(id = project_id)
	item.project = project

	#
	# Now add location priorities
	#
	item.assigned_to = project.binder.owner

	#if request.user in item.project.binder.producers.all():
	item.location = Location.objects.get(project = project, method = 'action')
	item.assigned_to = request.user

	#if request.user in item.project.binder.reporters.all():
	#	item.location = Location.objects.get(project = project, method = 'report')
	item.item_state = ItemState.objects.get(constant = constants.ITEMSTATE_IDENTIFIED)

	item.priority = Priority.objects.get(default = True)
	item.save()

	#
	# Track it. We have to wait until item was saved before we can save the assigned record.
	#
	assigned = Assigned()
	assigned.item = item
	assigned.user = request.user
	assigned.location = item.location
	assigned.comments = "Created"
	assigned.save()

	#
	# Did we reassign it?
	#
	if item.assigned_to != request.user:
		reassigned = Assigned()
		reassigned.item = item
		reassigned.user = item.assigned_to
		reassigned.location = item.location
		reassigned.comments = "Reassigned"
		reassigned.save()

	return HttpResponseRedirect(
		'/item/%s?new_item=true&search_id=%s&added_flash_number=%s' % (
			item.id,
			request.GET.get('search_id', ''),
			request.GET.get('added_flash_number', '')
		)
	)

@login_required
def new_client(request):
	form = ClientForm()
	if request.method == 'POST':
		form = ClientForm(request.POST)
		if form.is_valid():
			client = Client()
			client.name = form.cleaned_data['name']
			client.save()
			return HttpResponseRedirect('/roadmap/ledger/client/%s' % (client.slug))

	return render_to_response(
		'ledger/forms/Client.html',
		{
			'form' : form,
			'calendar_output': mini_calendar(request),
			'clients': Client.objects.all(),
		},
		context_instance = RequestContext(request),
	)

@login_required
def new_project(request, id):
	form = ProjectForm()
	binder = Binder.objects.get(id = id)
	client = binder.client

	if request.method == 'POST':
		form = ProjectForm(request.POST)
		if form.is_valid():
			project = Project()
			project.name = form.cleaned_data['name']
			project.binder = binder
			project.save()
			return HttpResponseRedirect('/roadmap/ledger/project/%s/%s' % (binder.slug, project.slug))

	return render_to_response(
		'ledger/forms/Project.html',
		{
			'form' : form,
			'client': client,
			'binder': binder,
			'tag_cloud' : Tag.objects.cloud_for_model(Item, 4, tagging.utils.LOGARITHMIC, {'project__binder__client': client } ),
			'calendar_output' : mini_calendar(request, None, None, client),
		},
		context_instance = RequestContext(request),
	)

@login_required
def new_binder(request, client_id):
	form = BinderForm()
	client = Client.objects.get(id = client_id)

	if request.method == 'POST':
		form = BinderForm(request.POST)

		if form.is_valid():
			binder = Binder()
			binder.name = form.cleaned_data['name']
			binder.owner = request.user
			binder.active = True
			binder.client = client #Client.objects.get(name = 'Internal')
			binder.save()

			#print('creating default project')
			project = Project()
			project.name = 'Initial work'
			project.binder = binder
			#project.save()
			#print('saving')

			#binder.default_project = project
			binder.team.add(request.user)
			binder.reporters.add(request.user)
			binder.save()

			request.flash['new_binder'] = 'This is your new team. Start by adding some team members on the right hand side.'

			return HttpResponseRedirect('/roadmap/ledger/binder/%s/%s' % (client.slug, binder.slug))

	return render_to_response(
		'ledger/forms/Binder.html',
		{
			'form' : form,
			'client' : client,
			'tag_cloud' : Tag.objects.cloud_for_model(Item, 4, tagging.utils.LOGARITHMIC, {'project__binder__client': client } ),
			'calendar_output' : mini_calendar(request, None, None, client),
		},
		context_instance = RequestContext(request),
	)

@login_required
def edit_target(request, target_id, project_id):
	target = Target.objects.get(id = target_id)
	project = Project.objects.get(id = project_id)
	item = project
	form = TargetForm(instance = target)
	if request.method == 'POST':
		form = TargetForm(request.POST)
		if form.is_valid():
			#print('target user  %s %s' % (target.user, request.user))
			if target.user == request.user:
				#print('cleaned data')
				for loop_item in form.cleaned_data:
					#print(loop_item)
					pass
				target.name = form.cleaned_data['name']
				target.deadline = form.cleaned_data['deadline']
				target.public = form.cleaned_data['public']
				target.active = form.cleaned_data['active']
				target.save()
				return HttpResponseRedirect('/roadmap/ledger/project/%s/%s' % (project.binder.slug, project.slug))
		else:
			#print(form.errors)
			pass

	tag_cloud = Tag.objects.cloud_for_model(Item, 4, tagging.utils.LOGARITHMIC, {'project': project} )
	team = project.binder.team.all()
	team = gravatar_list(team)

	return render_to_response(
		'ledger/forms/Target.html',
		{
			'item': item,
			'tag_cloud': tag_cloud,
			'new': False,
			'calendar_output' : mini_calendar(request, project.binder, project),
			'team' : team,
			'reporters' : project.binder.reporters.all(),
			'producers' : project.binder.producers.all(),
			'binder': project.binder,
			'form' : form,
			'project' : project,
			'targets' : Target.objects.filter(Q(project = project, user = request.user, public = 0) | Q(project = project, public = 1)).filter(active = True),
		},
		context_instance = RequestContext(request),
	)


@login_required
def new_target(request, project_id):
	project = Project.objects.get(id = project_id)
	item = project
	form = TargetForm()
	if request.method == 'POST':
		form = TargetForm(request.POST)
		if form.is_valid():
			target = Target()
			target.user = request.user
			target.name = form.cleaned_data['name']
			target.deadline = form.cleaned_data['deadline']
			target.public = form.cleaned_data['public']
			target.project = project
			target.active = form.cleaned_data['active']
			target.save()
			return HttpResponseRedirect('/roadmap/ledger/project/%s/%s' % (project.binder.slug, project.slug))

	tag_cloud = Tag.objects.cloud_for_model(Item, 4, tagging.utils.LOGARITHMIC, {'project': project} )
	team = project.binder.team.all()
	team = gravatar_list(team)

	return render_to_response(
		'ledger/forms/Target.html',
		{
			'item': item,
			'tag_cloud': tag_cloud,
			'new': False,
			'calendar_output' : mini_calendar(request, project.binder, project),
			'team' : team,
			'reporters' : project.binder.reporters.all(),
			'producers' : project.binder.producers.all(),
			'binder': project.binder,
			'project' : project,
			'form' : form,
			'targets' : Target.objects.filter(Q(project = project, user = request.user, public = 0) | Q(project = project, public = 1)).filter(active = True),
		},
		context_instance = RequestContext(request),
	)

@login_required
def active_post(request):
	if request.POST.get("MoveToProduction", "") != "":
		item_list = request.POST.getlist('id')
		if len(item_list) == 0:
			request.flash['move'] = 'You have not selected any items to move.'
			return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

		for loop_item in item_list:
			item = Item.objects.get(id = loop_item)
			item.location = Location.objects.get(name = 'Production')
			item.save()

		for user in User.objects.all():
			feed = Feed()
			feed.description = '%s moved to production.' % (len(item_list))
			feed.date_time = datetime.datetime.now()
			#print(feed.date_time)
			feed.user = user
			feed.author = request.user
			feed.save()

		return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
		return HttpResponseRedirect('/roadmap/ledger/active?location=Reported')

	if request.POST.get("MoveToTesting", "") != "":
		item_list = request.POST.getlist('id')
		if len(item_list) == 0:
			request.flash['move'] = 'You have not selected any items to move.'
			return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

		for loop_item in item_list:
			item = Item.objects.get(id = loop_item)
			item.location = Location.objects.get(name = 'Testing')
			item.save()

		for user in User.objects.all():
			feed = Feed()
			feed.description = '%s moved to testing.' % (len(item_list))
			feed.date_time = datetime.datetime.now()
			#print(feed.date_time)
			feed.user = user
			feed.author = request.user
			feed.save()

		return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
		return HttpResponseRedirect('/roadmap/ledger/active?location=Production')
	return active(request)


def demo(request):
	from django.core import serializers
	items = Item.objects.filter(assigned_to=request.user)
	data = serializers.serialize("xml", items)
	return HttpResponse(
		data,
		'application/xml'
	)


def feed_calendar(request):
	pass
	response = HttpResponse(mimetype='text/calendar')
	feed = Feed.objects.all()
	return render_to_response(
		'ledger/calendar.ical',
		{
			'feed': feed,
		},
		context_instance = RequestContext(request),
	)
#cal = vobject.iCalendar()
#cal.add('method').value = 'PUBLISH'  # IE/Outlook needs this
#for event in event_list:
#    vevent = cal.add('vevent')
#    ... # add your event details
#icalstream = cal.serialize()
#response = HttpResponse(icalstream, mimetype='text/calendar')
#response['Filename'] = 'filename.ics'  # IE needs this
#response['Content-Disposition'] = 'attachment; filename=filename.ics'


def email_return_body(text):
	split_text = text.split('\n')
	output = []
	spool = False
	for loop_item in split_text:
		if spool:
			output.append(loop_item)
		if loop_item == '':
			spool = True
	return output

@csrf_exempt
@login_required
def update_tags(request):
	#print('updating tags')
	item_id = request.POST.get('item_id')
	#print(item_id)
	tags = request.POST.get('tags')
	#print(tags)
	item = Item.objects.get(id = item_id)
	tags = tags.strip().replace('\n', ' ')
	#print('updating item %s with %s' % (item_id, tags))
	item.tags = tags
	item.save()
	#print('saved')

	binder = item.project.binder
	#print('got binder')
	binder_tags = binder.tags
	#print('got binder tags')
	#print(binder.tags)

	json_serializer = serializers.get_serializer("json")()
	return HttpResponse(
		'success',
		mimetype='text/plain',
	)

@csrf_exempt
@login_required
def toggle_item(request, item_id):
	item_key = 'k%s' % item_id
	item = Item.objects.get(id = item_id)

	if not 'selected_items' in request.session.keys():
		request.session['selected_items'] = []
	selected_items = request.session['selected_items']

	#
	# add it
	#
	if request.GET.get('checked', 'false') == 'true':
		if not item_key in selected_items:
			selected_items.append(item_key)
	else:
		if item_key in selected_items:
			del(selected_items[selected_items.index(item_key)])
	request.session['selected_items'] = selected_items

	items_count = len(selected_items)
	plural = ''
	if items_count > 1:
		plural = 's'
	body = loader.render_to_string('ledger/items/selected_items_bar.html', {
		'selected_items_count': items_count,
	})

	#if items_count == 0:
	#	body = ''

	return HttpResponse(
		body,
		mimetype='text/plain',
	)

@login_required
def get_selected_items_bar(request):
	return render_to_response(
		'ledger/items/selected_items_bar.html', {
			'selected_items_count': len(request.session['selected_items']),
		}
	)

@csrf_exempt
@login_required
def item_added(request):
	item_id = request.REQUEST.get('item_id')
	referrer = request.REQUEST.get('referrer')
	search_id = request.REQUEST.get('search_id')

	item = Item.objects.get(id = item_id)
	page = {}
	page['project_id'] = item.project.id

	search_url = None
	if search_id:
		search_data = load_search(search_id)
		if search_data:
			search_url = search_data['searchUrl']

	return render_to_response(
		'ledger/item_added.html',
		{
			'search_url': search_url,
			'page': page,
			'item': item,
			'project': Project.objects.filter(binder = item.project.binder),
			'binder': item.project.binder,
			'binders': Binder.objects.all(),
			'location': Location.objects.all(),
			'users': User.objects.all(),
			'referrer': referrer,
			'active_items': active_items(request),
			'selected_items': request.session.get('selected_items', []),
			'search_id': search_id,
		},
		context_instance = RequestContext(request),
	)

@csrf_exempt
@login_required
def promote_objective(request):
	id = request.GET.get('item_id')
	objective_id = request.GET.get('objective_id')
	objective = ChecklistItem.objects.get(id = objective_id)

	item = Item.objects.get(id = id)
	new_item = Item()
	new_item.description = objective.text
	new_item.item_type = item.item_type
	new_item.assigned_to = item.assigned_to
	new_item.priority = item.priority
	new_item.project = item.project
	new_item.location = item.location
	new_item.tags = item.tags
	new_item.save()

	if item.item_type.name == 'Issue':
		issue = Issue()
		issue.item = new_item
		issue.save()

	if item.item_type.name == 'Requirement':
		requirement = Requirement()
		requirement.item = new_item
		requirement.save()

	for loop_target in item.targets.filter(user = request.user):
		new_item.targets.add(loop_target)

	objective.text = 'Item moved to <a href="/roadmap/ledger/item/%s">here</a>' % (new_item.id)
	objective.save()

	#
	# Notify this item was split out
	#
	comment_text = 'This item was separated out from <a href="/roadmap/ledger/item/%s">%s</a>' % (item.id, item.description)
	new_item.add_comment(request.user, comment_text)
	#comment = Comment()
	#comment.user = request.user
	#comment.item = new_item
	#comment.message = comment_text
	#comment.date_time = datetime.datetime.now()
	#comment.save()

	#if item.item_type.name == 'Issue':
	return HttpResponseRedirect('/roadmap/ledger/item/%s' % (new_item.id))



@login_required
def preview(request, id):
	type_map = {
		'Issue' : [Issue, IssueForm, IssueProcess],
		'Note' : [Note,  NoteForm, NoteProcess],
		'Requirement' : [Requirement, RequirementForm, RequirementProcess],
		'Email' : [Email, EmailForm, EmailProcess],
		'File' : [File, FileForm, FileProcess ],
	}

	item = Item.objects.get(id = id);
	dynamic_type = type_map[item.item_type.name]
	linked_item = None
	linked_item_form = None
	linked_item_check = dynamic_type[0].objects.filter(item = item)
	extra = {}

	if linked_item_check.count() == 0:
		linked_item = dynamic_type[0]()
		linked_item.item = item
		linked_item.save()
	else:
		linked_item = dynamic_type[0].objects.get(item = item)
	manager = dynamic_type[2]()
	linked_item_form = dynamic_type[1](
		initial = manager.load(request, item, linked_item, extra)
	)

	return render_to_response(
		'ledger/forms/Preview.html', # % (item.item_type.name),
		{
			'item' : item,
			'linked_item' : linked_item,
			'linked_item_form' : linked_item_form,
			'related_items' : get_tagged_related_items(item),
		},
		context_instance = RequestContext(request),
	)


@login_required
def item(request, id):
	#
	# Attempts to get the linked item. If this does not exist, create it.
	#
	new_item = False
	if request.GET.get('new_item', '') == 'true':
		new_item = True

	type_map = {
		'Issue' : [Issue, IssueForm, IssueProcess],
		'Note' : [Note,  NoteForm, NoteProcess],
		'Requirement' : [Requirement, RequirementForm, RequirementProcess],
		'Email' : [Email, EmailForm, EmailProcess],
		'File' : [File, FileForm, FileProcess ],
	}

	items = []
	item = Item.objects.get(id = id)
	#
	# Mark item as viewed
	#
	if item.assigned_to == request.user:
		item.unseen = False
		item.replied = False
	item.save()

	dynamic_type = type_map[item.item_type.name]
	extra = {}

	if not user_can_view(request, item):
		return HttpResponseRedirect('/roadmap/ledger')

	linked_item = None
	linked_item_form = None
	linked_item_check = dynamic_type[0].objects.filter(item = item)
	if linked_item_check.count() == 0:
		linked_item = dynamic_type[0]()
		linked_item.item = item
		linked_item.save()
	else:
		linked_item = dynamic_type[0].objects.get(item = item)
	manager = dynamic_type[2]()

	referrer = request.META.get('HTTP_REFERER')

	if request.method == 'POST':
		referrer = request.POST.get('referrer')
		#print('posted')
		custom_form = dynamic_type[1]
		linked_item_form = custom_form(request.POST)
		#print(str(linked_item_form))
		if linked_item_form.is_valid():
			#
			# Call save actions for the specific type
			#
			manager.save(request, item, linked_item, linked_item_form)
			#
			# Check for moving
			#
			#if project_id == 'new':
			#	project = Project()
			#	project.name = request.POST.get('newProject')
			#	project.binder = item.project.binder
			#	project.save()
			#	project_id = project.id

			#
			# If it was set to follow up, clear the request
			#
			if item.assigned_to == request.user:
				item.follow_up = False
				item.save()

			#
			# Check for other projects, location tags
			#
			tags = item.tags.replace(',', ' ')
			check_list = Project.objects.all()
			for loop_item in check_list:
				tags = tags.replace(loop_item.name.lower(), '')
			tags += ' %s' % (item.project)

			check_list = Location.objects.all()
			for loop_item in check_list:
				tags = tags.replace(loop_item.name.lower(), '')
			tags += ' %s' % (item.location)

			check_list = Type.objects.all()
			for loop_item in check_list:
				tags = tags.replace(loop_item.name.lower(), '')
			tags += ' %s' % (item.item_type)

			tags = tags.strip()
			#print('saving tags: %s' % tags)
			#item.tags = tags
			if(item.state == 1):
				new_item = True
				#
				# Update feed to have proper data.
				#
				data = Feed.objects.filter(item=item)
			item.state = 0
			item.save()

			request.flash['item'] = '<br/>Updated <a href="/roadmap/ledger/item/%s">%s</a>.' % (item.id, item.description)

			#
			# We need to check for changes here
			#
			#for user in user_for_binder(request, item.project.binder):
			#	feed = Feed()
			#	feed.description = '<span class="floatRight"><img src="/media/layout/icons/text_signature.png" /></span><a href="/roadmap/ledger/profile/%s">%s %s</a> updated <a href="/roadmap/ledger/item/%s">%s</a> <span class="tags">%s</a>' % (
			#		request.user.username,
			#		request.user.first_name,
			#		request.user.last_name,
			#		item.id,
			#		item.description,
			#		item.tags
			#	)
			#	feed.item = item
			#	feed.date_time = datetime.datetime.now()
			#	#print(feed.date_time)
			#	feed.user = user
			#	feed.author = request.user
			#	feed.save()

			if new_item:
				return HttpResponseRedirect(
					"/roadmap/ledger/new_item/%s?search_id=%s&project=%s&added_flash_number=%s" % (
						item.item_type.name, request.POST.get('search_id', ''), item.project.id, item.id,
					)
				)
			redirect_to_referrer = request.POST.get('referrer')
			if redirect_to_referrer == None or redirect_to_referrer == 'None':
				redirect_to_referrer = '/'
			return HttpResponseRedirect(redirect_to_referrer)
		else:
			pass
			#print('invalid %s' % linked_item_form.errors)
	else:
		#
		# Call the load of the type manager. This may populate extra values.
		#
		linked_item_form = dynamic_type[1](
			initial = manager.load(request, item, linked_item, extra)
		)

	count_notes = Item.objects.filter(item_type = Type.objects.get(name = 'Note'), project = item.project, state = 0).count()
	checklist_items = ChecklistItem.objects.filter(item = item).order_by('order_index')
	file_uuid = str(uuid.uuid1())

	search_id = request.GET.get('search_id','')
	search_found = None
	search_count = None
	search_url = None
	if search_id:
		search_data = load_search(search_id)
		if search_data:
			search_url = search_id #search_data['searchUrl']
			items = search_data.items
			index = -1
			for loop_item in items:
				#print('item %s' %loop_item)
				#print('id %s ' % item.id)
				index+=1
				if str(loop_item) == str(item.id):
					search_found = index + 1
			#
			# Has search expire
			#
			#if search_found == None:
			#	search_id = 'Expired'
			#else:
			search_count = len(items)

	deleted_items = Version.objects.get_deleted(ChecklistItem)
	#print('len %s' % deleted_items)
	#for l in deleted_items:
		#print(str(dir(l)))
		#print

	recently_viewed_items_add(request, item)

	#
	# Get versions
	#
	#version_list = Version.objects.get_for_object(item)
	#
	# Get the viewsettings
	#
	view_settings = ''
	project_setting = ProjectSetting.objects.get(const = 'VIEWPREFERENCES_DEFAULT_VIEWSTATE')
	try:
		user_project_setting = UserProjectSetting.objects.get(
			Q(
				project = item.project,
				user = request.user,
				project_setting = project_setting
			)
		)
		view_settings = user_project_setting.value
	except UserProjectSetting.DoesNotExist:
		pass

	try:
		project_item_filter = ProjectItemFilter.objects.get(search_id = search_id, user = request.user)
	except ProjectItemFilter.DoesNotExist:
		project_item_filter = None

	return render_to_response(
		'ledger/forms/%s.html' % (item.item_type.name),
		{
			'user_filters': item.project.project_filters.filter(user = request.user),
			'deleted': deleted_items,
			'item' : item,
			'items' : Item.objects.filter(id__in = items),
			'new_item' : new_item,
			'search_url': search_url,
			'search_id' : search_id,
			'project_item_filter': project_item_filter,
			'project_item_filters': ProjectItemFilter.objects.filter(project = item.project, user = request.user),
			'search_count' : search_count,
			'search_found' : search_found,
			'linked_item' : linked_item,
			'linked_item_form' : linked_item_form,
			'project' : Project.objects.filter(binder = item.project.binder),
			'binders' : Binder.objects.all(),
			'binder': item.project.binder,
			'locations': Location.objects.filter(project = item.project).order_by('order'),
			'preview' : 'ledger/preview_' + item.item_type.name + '.html',
			'extra' : extra,
			'priorities' : Priority.objects.all().order_by('-order'),
			'settings' : settings,
			'users' : item.project.binder.team.all(), #User.objects.all(),
			'referrer' : referrer,
			'count_notes' : count_notes,
			'checklist_items' : checklist_items,
			'file_uuid' : file_uuid,
			'active_items' : active_items(request),
			'selected_items' : request.session.get('selected_items', []),
			'targets' : Target.objects.filter(
				Q(project = item.project, user = request.user, public = 0) | Q(project = item.project, public = 1)
			).filter(active = True),
			'related_items' : get_tagged_related_items(item),
			'added_flash_number' : request.GET.get('added_flash_number', None),
			#'version_list' : version_list,
			'view_settings': view_settings,
		},
		context_instance = RequestContext(request),
	)


def recently_viewed_items_add(request, item):
	#
	# Add to history
	#
	recently_viewed_items = request.session.get('recently_viewed_items', [])
	if item in recently_viewed_items:
		del(recently_viewed_items[recently_viewed_items.index(item)])
	new_recently_viewed_items = []
	new_recently_viewed_items.append(item)
	item_count = 0
	for loop_item in recently_viewed_items:
		new_recently_viewed_items.append(loop_item)
		item_count+=1
		if item_count > 30:
			break
	request.session['recently_viewed_items'] = new_recently_viewed_items


def mini_calendar(request, binder = None, project = None, client = None):
	todays_date = datetime.datetime.date(datetime.datetime.now())
	todays_month = todays_date.month
	todays_year = todays_date.year
	todays_day = todays_date.day
	actual_month = todays_month
	actual_year = todays_year

	# adjust the date for querystring overrides
	try:
		if request.GET.has_key('month') != '':
			todays_month = int(request.GET['month'])
	except:
		pass

	try:
		if request.GET.has_key('year'):
			todays_year = int(request.GET['year'])
	except:
		pass

	previous_month = todays_month - 1
	previous_year = todays_year
	if previous_month == 0:
		previous_month = 12
		previous_year = todays_year - 1

	next_month = todays_month + 1
	next_year = todays_year
	if next_month == 13:
		next_month = 1
		next_year = next_year + 1

	months = [
		'January',
		'February',
		'March',
		'April',
		'May',
		'June',
		'July',
		'August',
		'September',
		'October',
		'November',
		'December'
	]
	calendar_item = calendar_data()
	calendar_item.todays_year = todays_year
	calendar_item.todays_month = todays_month
	calendar_item.previous_month = previous_month
	calendar_item.previous_year = previous_year
	calendar_item.next_month = next_month
	calendar_item.next_year = next_year
	calendar_item.past_year = todays_year - 1
	calendar_item.future_year = todays_year + 1

	month_post_list = []
	month_post_list = Feed.objects.filter(
		date_time__gte = datetime.datetime(todays_year, todays_month, 1)
	).exclude(
		date_time__gte = datetime.datetime(next_year, next_month, 1)
	)


	target_list = Target.objects.filter(
		Q(user = request.user, public = 0) | Q(public = 1)
	).filter(
		deadline__gte = datetime.datetime(todays_year, todays_month, 1)
	).exclude(
		deadline__gte = datetime.datetime(next_year, next_month, 1)
	).filter(active = True)
	if project != None:
		target_list = target_list.filter(project = project)

	if binder != None:
		target_list = target_list.filter(project__binder = binder)

	if client != None:
		month_post_list.filter(item__project__binder__client = client)
		target_list = target_list.filter(item__project__binder__client = client)

	if binder != None:
		month_post_list.filter(item__project__binder = binder)
		target_list.filter(item__project__binder = binder)

	if project != None:
		month_post_list.filter(item__project = project)
		target_list.filter(item__project = project)

	if not request.user.is_staff:
		month_post_list = month_post_list.filter(item__assigned_to = request.user)

	#
	# need to put some deadline checking code in here
	#
	calendar_item.month_name = months[todays_month - 1]
	for week in calendar.monthcalendar(todays_year, todays_month):
		week_data = []
		for day in week:
			day_item = day_data(day)
			if day == todays_day and todays_month == actual_month and todays_year == actual_year:
				day_item.ccs_class = 'today '

			#if binder != None:
			#	projects = Project.objects.filter(binder=binder)
			#	for loop_project in projects:
			#		#print('%s == %s' % (day, loop_project.deadline))
			#		if day == loop_project.deadline:
			#			day_item.deadline = loop_project

			week_data.append(day_item)
		calendar_item.weeks.append(week_data)

	for loop_week in calendar_item.weeks:
		for loop_day in loop_week:
			loop_day.overdue = False

	for loop_item in month_post_list:
		for loop_week in calendar_item.weeks:
			for loop_day in loop_week:
				if loop_day.value == loop_item.date_time.day:
					loop_day.has_event = True
					loop_day.ccs_class += ' events '
					loop_day.slug = loop_item.description

	for loop_item in target_list:
		for loop_week in calendar_item.weeks:
			for loop_day in loop_week:
				if loop_day.value == loop_item.deadline.day:
					if not hasattr(loop_day, 'targets'):
						loop_day.targets = []
					loop_day.targets.append(loop_item)
					if loop_item.overdue:
						loop_day.overdue = True

	return calendar_item

@login_required
def view_client(request, name):
	client = Client.objects.get(slug = name)
	return render_to_response(
		'ledger/client.html',
		{
			'client' : client,
			'tag_cloud' : Tag.objects.cloud_for_model(Item, 4, tagging.utils.LOGARITHMIC, {'project__binder__client': client } ),
			'calendar_output' : mini_calendar(request, None, None, client),
		},
		context_instance = RequestContext(request),
	)

@login_required
def view_binder(request, client_name, name):
	client = Client.objects.get(slug = client_name)
	binder = Binder.objects.get(slug = name, client = client)

	if not user_can_view(request, binder):
		return HttpResponseRedirect('/roadmap/ledger')

	project_data = Project.objects.filter(binder = binder)
	projects = []
	notes = None
	emails = None
	for item in project_data:
		note_items = Item.objects.filter(project = item, item_type__name = 'Note')
		notes = Note.objects.filter(item__project = item, item__state = 0)
		emails = Email.objects.filter(item__project = item, item__state = 0)
		email_manager = EmailProcess()
		for loop_item in emails:
			loop_item.body = '\n'.join(
				email_return_body(
					email_manager.read_email(
						str(loop_item.file_id)
					)
				)
			).replace('=20', '')
		project = BinderProject()
		project.project = item

		#
		# Pull the chart back in order, then add as a dict
		#
		daily_basic_data = DailyBasic.objects.filter(project = item).order_by('day')
		for loop_daily in daily_basic_data:
			item_key = ('k%s' % loop_daily.day)
			if not item_key in project.chart_data.keys():
				project.chart_data[item_key] = ChartBasicItem()
				project.chart_data[item_key].day = loop_daily.day
			if loop_daily.location.name == 'Reported':
				project.chart_data[item_key].reported = loop_daily.quantity
			if loop_daily.location.name == 'Production':
				project.chart_data[item_key].production = loop_daily.quantity
			if loop_daily.location.name == 'Testing':
				project.chart_data[item_key].testing = loop_daily.quantity
			if loop_daily.location.name == 'Delivered':
				project.chart_data[item_key].delivered = loop_daily.quantity
		#
		# Now re-pack the dict into a single iterable list of complex objects, so the template can unpack
		#
		fetch_keys = project.chart_data.keys()
		fetch_keys.sort()

		for loop_key in fetch_keys:
			project.chart.append(project.chart_data[loop_key])

		#
		# Fetch issues
		#
		row = GridRow()
		for loop_location in Location.objects.all():
			grid_item = GridRow()
			grid_item.count = Item.objects.filter(
				project = item,
				location = loop_location,
				state = 0,
			).exclude(
				item_type = Type.objects.get(name = 'Email')
			).exclude(
				item_type = Type.objects.get(name = 'Note')
			).count()

			grid_item.location = loop_location
			row.items.append(grid_item)

		project.row = row
		projects.append(project)

	team = binder.team.all()
	team = gravatar_list(team)

	binder_items_requirements = Requirement.objects.filter(item__project__binder = binder)
	binder_items_issues = Issue.objects.filter(item__project__binder = binder)

	delivery_notes = []
	for loop_item in binder_items_requirements:
		if loop_item.delivery_notes != '' and loop_item.delivery_notes != None:
			delivery_notes.append(
				{
					'type' : 'Requirement',
					'id' : loop_item.item.id,
					'text' : loop_item.delivery_notes
				}
			)
	for loop_item in binder_items_issues:
		if loop_item.delivery_notes != '' and loop_item.delivery_notes != None:
			delivery_notes.append(
				{
					'type' : 'Issue',
					'id' : loop_item.item.id,
					'text' : loop_item.delivery_notes
				}
			)

	updates_header, feed = latest_updates(request)
	feed = feed.filter(item__project__binder = binder)

	tag_cloud = Tag.objects.cloud_for_model(Item, 4, tagging.utils.LOGARITHMIC, {'project__binder': binder } )

	return render_to_response(
		'ledger/binder.html',
		{
			'tag_cloud': tag_cloud,
			'notes' : notes,
			'emails' : emails,
			'settings' : settings,
			'calendar_output' : mini_calendar(request, binder, None),
			'binder' : binder, #item.binder,
			'team' : team,
			'projects' : projects,
			'users' : User.objects.all().order_by('first_name', 'last_name'),
			'delivery_notes' : delivery_notes,
#			'reporters' : binder.reporters,
#			'producers' : binder.producers,
			'active_items' : active_items(request),
			'locations' : Location.objects.all(),
			'updates_header' : updates_header,
			#'grid_row' : row,
			'feed' : feed,
		},
		context_instance = RequestContext(request),
	)

@login_required
def set_deadline(request):
	project = Project.objects.get(slug = request.GET.get('project'))
	binder = project.binder

	if request.GET.get('action', '') == 'set':
		#print('setting datetime')
		if request.user == binder.owner:
			#print('user is owner')
			new_deadline = datetime.date(
				int(request.GET.get('year')),
				int(request.GET.get('month')),
				int(request.GET.get('day'))
			)
			#print(new_deadline)
			project.deadline = new_deadline
			project.save()
			return HttpResponseRedirect('/roadmap/ledger/project/%s/%s' % (binder.slug, project.slug))
		else:
			#print('user is not owner')
			pass

	return render_to_response(
		'ledger/set_deadline.html',
		{
			'calendar_output' : mini_calendar(request, binder, None),
			'active_items' : active_items(request),
			'project' : project,
			'binder' : binder,
		},
		context_instance = RequestContext(request),
	)

@csrf_exempt
@login_required
def owner_to_binder(request):
	binder_id = request.POST.get('binder_id')
	user_id = request.POST.get('user_id', '')

	binder = Binder.objects.get(id = binder_id)
	binder.owner = User.objects.get(id = user_id)
	binder.save()
	json_serializer = serializers.get_serializer("json")()
	return HttpResponse(
		'success',
		mimetype='text/plain',
	)

@login_required
@csrf_exempt
def user_to_binder(request):
	binder_id = request.POST.get('binder_id')
	user_id = request.POST.get('user_id', '')
	email_address = request.POST.get('email_address')
	action = request.POST.get('actionName')
	producer = request.POST.get('producer', '')
	reporter = request.POST.get('reporter', '')
	binder = Binder.objects.get(id = binder_id)

	if user_id == '0':
		user = User()
		user.email = email_address
		import random
		new_random_password = ''.join([random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for x in xrange(5)])
		#print('creating new user')
		#print(new_random_password)
		user.password = new_random_password
		user.save()
		user_id = user.id
		#print('New user ID %s ' % user_id)

		from django.core.mail import send_mail

		body = 'You have a new signin for http://www.road-map.org/\n\nEmail: %s\n\nPassword:%s' % (email_address, new_random_password)
		send_mail('Your Roadmap signin', body, 'help@road-map.org', [email_address], fail_silently=False)

	user = User.objects.get(id = user_id)
	#print('user %s' % user)
	#print(producer)
	if action == 'add':
		binder.team.add(user)
		if reporter != '':
			binder.reporters.add(user)
		if producer != '':
			#print('adding producer')
			binder.producers.add(user)
	if action == 'remove':

		#binder.team.remove(user)
		if reporter != '':
			binder.reporters.remove(user)
		if producer != '':
			binder.producers.remove(user)
	binder.save()

	return render_to_response(
		'ledger/binder_team_item.html',
		{
			'loop_item' : user,
			'binder': binder,
		},
		context_instance = RequestContext(request),
	)
	#json_serializer = serializers.get_serializer("json")()
	#return HttpResponse(
	#	'success',
	#	mimetype='text/plain',
	#)

@login_required
def notifications(request):
	return render_to_response(
		'ledger/notifications.html',
		{
			'headernav' : 'notifications',
			'active_items' : active_items(request),
		},
		context_instance = RequestContext(request),
	)

@login_required
def create_item_where(request, item_type, client_name = None, binder_name = None, project_name = None):
	client_items = []
	client_filter = {}
	if client_name:
		try:
			find_client = Client.objects.get(slug = client_name)
			client_filter['id'] = find_client.id
		except Client.DoesNotExist:
			pass
	for loop_client in Client.objects.filter(**client_filter).order_by('name'):
		loop_client.binders = []
		binder_filter = {}
		binder_filter['client'] = loop_client
		binder_filter['active'] = True

		if binder_name:
			try:
				find_binder = Binder.objects.get(slug = binder_name)
				binder_filter['id'] = find_binder.id
			except Binder.DoesNotExist:
				pass

		for loop_binder in Binder.objects.filter(**binder_filter).order_by('name'):
			loop_binder.projects = []
			for loop_project in Project.objects.filter(binder = loop_binder).order_by('name'):
				show = False
				if request.user in loop_binder.reporters.all():
					show = True
				if request.user in loop_binder.producers.all():
					show = True
				if request.user == loop_binder.owner:
					show = True
				if show:
					loop_binder.projects.append(loop_project)
			if len(loop_binder.projects) > 0:
				loop_client.binders.append(loop_binder)
		if len(loop_client.binders) > 0:
			client_items.append(loop_client)
	return render_to_response(
		'ledger/create_item_where.html',
		{
			'client_items' : client_items,
			'item_type' : item_type,
			'active_items' : active_items(request),
		},
		context_instance = RequestContext(request)
	)

@login_required
def view_notification(request, notification_id):
	notification = Notification.objects.get(id = notification_id)
	item = notification.item
	item_id = item.id
	notification.delete()

	return HttpResponseRedirect(
		'/item/%s' % item_id
	)


def recently_viewed_client(request, client):
	client_order = request.session.get('client_order', list())
	while client in client_order:
		del(client_order[client_order.index(client)])
	new_client_order = []
	new_client_order.append(client)
	for loop_item in client_order:
		new_client_order.append(loop_item)
	request.session['client_order'] = new_client_order


@login_required
def view_project_breakdown(request, client_name, binder_name, project_name):
	try:
		project = Project.objects.get(slug = project_name, binder = Binder.objects.get(slug = binder_name))
	except Project.DoesNotExist:
		return HttpResponseRedirect('/roadmap/ledger')
	except Binder.DoesNotExist:
		return HttpResponseRedirect('/roadmap/ledger')

	if not user_can_view(request, project):
		return HttpResponseRedirect('/roadmap/ledger')

	#
	# Get common data
	#
	targets = Target.objects.filter(Q(project = project, user = request.user, public = 0) | Q(project = project, public = 1)).filter(active = True)
	tag_cloud = Tag.objects.cloud_for_model(Item, 4, tagging.utils.LOGARITHMIC, {'project': project } )
	follow_ups = Item.objects.filter(project = project, assigned_to = request.user, follow_up = True)
	binder = project.binder
	team = binder.team.all().order_by('first_name', 'last_name')
	team = gravatar_list(team)

	#
	# Find all groups for this project items
	#
	production = Location.objects.get(method = 'action').id
	testing = Location.objects.get(method = 'test').id

	items = Item.active_objects.filter(project = project)

	unique_groups = {}
	for loop_item in items:
		key = 'k%s' % (loop_item.item_group)
		if not unique_groups.__contains__(key):
			name = loop_item.item_group
			if name == None or name == '':
				name = 'Ungrouped'
			unique_groups[key] = {
				'name': name,
				'production_false': 0.0,
				'production_true': 0.0,
				'testing_false': 0.0,
				'testing_true': 0.0,
			}
		if loop_item.location.id == production:
			if loop_item.fixed == True:
				unique_groups[key]['production_true']+=1
			else:
				unique_groups[key]['production_false']+=1
		if loop_item.location.id == testing:
			if loop_item.validated == True:
				unique_groups[key]['testing_true']+=1
			else:
				unique_groups[key]['testing_false']+=1
	#
	# Create percentages
	#
	unique_groups.keys().sort()

	for loop_group_key, loop_group in unique_groups.items():
		try:
			loop_group['production'] = int((float(loop_group['production_true']) / float(loop_group['production_false'] + loop_group['production_true'])) * 100)
		except Exception, ex:
			loop_group['production'] = None
		try:
			loop_group['testing'] = int((float(loop_group['testing_true']) / float(loop_group['testing_false'] + loop_group['testing_true'])) * 100)
		except Exception, ex:
			loop_group['testing'] = None

	return render_to_response(
		'ledger/project_breakdown.html',
		{
			'follow_ups' : follow_ups,
			'tag_cloud' : tag_cloud,
			'item' : project,
			'settings' : settings,
			'calendar_output' : mini_calendar(request, binder, project),
			'binder' : binder,
			'team' : team,
			'reporters' : binder.reporters.all(),
			'producers' : binder.producers.all(),
			'headernav' : 'notifications',
			'locations' : Location.objects.all(),
			'targets' : targets,
			'unique_groups' : unique_groups,
			'active_items' : active_items(request),
		},
		context_instance = RequestContext(request),
	)


@login_required
def project_import_csv(request, client_name, binder_name, project_name):
	try:
		project = Project.objects.get(slug = project_name, binder = Binder.objects.get(slug = binder_name))
	except Project.DoesNotExist:
		return HttpResponseRedirect('/roadmap/ledger')
	except Binder.DoesNotExist:
		return HttpResponseRedirect('/roadmap/ledger')

	if not user_can_view(request, project):
		return HttpResponseRedirect('/roadmap/ledger')

	binder = project.binder

	file_uuid = request.POST.get('file_uuid', str(uuid.uuid1()))
	has_file = False
	columns = []
	field_names = [
		'None',
		'Description',
		'Group',
	]

	if request.method == 'POST':
		has_file = True
		try:
			file = request.FILES["csv"]
		except Exception,ex:
			pass
		attachment_path = os.path.join(settings.MEDIA_ROOT, 'uploads')
		directory_name = os.path.join(attachment_path, 'csv')
		if not os.path.exists(directory_name):
			os.mkdir(directory_name)
		full_file_name = os.path.join(directory_name, file_uuid)

		with open(full_file_name, 'wb+') as output:
			for chunk in file.chunks():
				output.write(chunk)

		import csv
		reader = csv.reader(open(full_file_name), dialect='excel')
		for first_line in reader:
			break
		columns = first_line


	return render_to_response(
		'ledger/project_import_csv.html',
		{
			'item' : project,
			'settings' : settings,
			'binder' : binder,
			'headernav' : 'notifications',
			'file_uuid': file_uuid,
			'has_file': has_file,
			'columns': columns,
			'field_names': field_names,
		},
		context_instance = RequestContext(request),
	)


@login_required
def project_import_csv_mapping(request, client_name, binder_name, project_name):
	try:
		project = Project.objects.get(slug = project_name, binder = Binder.objects.get(slug = binder_name))
	except Project.DoesNotExist:
		return HttpResponseRedirect('/roadmap/ledger')
	except Binder.DoesNotExist:
		return HttpResponseRedirect('/roadmap/ledger')

	if not user_can_view(request, project):
		return HttpResponseRedirect('/roadmap/ledger')

	binder = project.binder
	file_uuid = request.POST.get('file_uuid')

	attachment_path = os.path.join(settings.MEDIA_ROOT, 'uploads')
	directory_name = os.path.join(attachment_path, 'csv')
	full_file_name = os.path.join(directory_name, file_uuid)

	mapping = {}
	for key in sorted(request.POST.iterkeys()):
		value = request.POST.get(key)
		if key.startswith('column_'):
			key_number = (key.split('_'))[1]
			actual_key = 'k%s' % (int(key_number) - 1)
			mapping[actual_key] = value

	location = Location.objects.get(method = 'report')
	priority = Priority.objects.get(default = 1)
	group_name = ''
	group_index = 0
	import csv
	with open(full_file_name) as read_file:
		reader = csv.reader(read_file, dialect='excel')
		ignore_first_line = True
		for line in reader:
			if ignore_first_line:
				ignore_first_line = False
				continue

			field_description = ''
			field_group = ''

			for loop_key in sorted(mapping.keys()):
				loop_value = mapping[loop_key]
				data = line[int(loop_key[1:])]
				if loop_value == 'Description':
					if field_description != '':
						field_description += ' '
					field_description = field_description + data

				if loop_value == 'Group':
					if field_group != '':
						field_group += ' '
					field_group += data

			if field_group != '':
				if group_name != field_group:
					group_name = field_group
					group_index+=1
			#
			# now create the item
			#
			#
			# Add the item to the database
			#
			item = Item()
			item.item_type = Type.objects.get(name = 'Requirement')
			item.location = location
			item.state = 0
			item.project = project
			item.assigned_to = request.user
			item.priority = priority

			linked_item = Requirement()
			print(field_description)
			item.description = field_description#.decode('utf-16')
			if group_index > 0:
				item.item_group = '%s %s' % ( ('0' + str(group_index))[-2:], field_group)
			item.save()

			#
			# link the linked_item in
			#
			linked_item.item = Item.objects.get(id = item.id)
			linked_item.save()

			#item.linked_item = linked_item
			item.save()

			#
			# Track it. We have to wait until item was saved before we can save the assigned record.
			#
			assigned = Assigned()
			assigned.item = item
			assigned.user = request.user
			assigned.location = item.location
			assigned.comments = "Created"
			assigned.save()
	return HttpResponseRedirect(request.POST.get('items_link'))


@login_required
def view_project_settings(request, client_name, binder_name, project_name):
	"""
	Configuration for the project
	"""
	try:
		item = Project.objects.get(slug = project_name, binder = Binder.objects.get(slug = binder_name))
	except Project.DoesNotExist:
		return HttpResponseRedirect('/roadmap/ledger')
	except Binder.DoesNotExist:
		return HttpResponseRedirect('/roadmap/ledger')

	binder = item.binder

	if not user_can_view(request, item):
		return HttpResponseRedirect('/roadmap/ledger')

	locations = Location.objects.filter(method = 'action', project = item).order_by('order')

	if request.method == 'POST':
		if request.POST.get('addLocation', '') != '':
			new_location = Location()
			new_location.project = item
			new_location.description = 'new location'
			new_location.method = 'action'
			new_location.order = len(locations)
			new_location.save()

		for loop_location in locations:
			if request.POST.get('delete_%s' % loop_location.id, '') != '':
				loop_location.delete()

			if request.POST.get('moveUp_%s' % loop_location.id, '') != '' or request.POST.get('moveDown_%s' % loop_location.id, '') != '':
				order_index = loop_location.order
				if request.POST.get('moveUp_%s' % loop_location.id, '') != '':
					new_order_index = order_index - 1
				else:
					new_order_index = order_index + 1
				for new_loop_location in locations:
					if new_loop_location.order == new_order_index:
						new_loop_location.order = order_index
						new_loop_location.save()
						loop_location.order = new_order_index
						loop_location.save()
						break


		if request.POST.get('submit', '') != '':
			for loop_location in locations:
				if request.POST.get('location_edit_%s' % loop_location.id,'' ) != '':
					form_location_name = request.POST.get('location_%s' % loop_location.id )
					#form_location_order = int(request.POST.get('order_%s' % loop_location.id ))
					loop_location.description = form_location_name
					#loop_location.order = form_location_order
					loop_location.save()
			return view_project(request, binder_name, item.slug, 'Overview')
		locations = Location.objects.filter(method = 'action', project = item).order_by('order')



	tag_cloud = Tag.objects.cloud_for_model(Item, 4, tagging.utils.LOGARITHMIC, {'project': item } )
	team = item.binder.team.all().order_by('first_name', 'last_name')
	team = gravatar_list(team)
	user_filters = item.project_filters.filter(user = request.user)
	targets = Target.objects.filter(Q(project = item, user = request.user, public = 0) | Q(project = item, public = 1)).filter(active = True)

	return render_to_response(
		'ledger/project_settings.html',
		{
			'user_filters': user_filters,
			'locations': locations,
			'template_section': 'settings',
			'calendar_output': mini_calendar(request, binder, item),
			'binder': item.binder,
			'team': team,
			'item': item,
			'tag_cloud' : tag_cloud,
		},
		context_instance = RequestContext(request),
	)


@login_required
def view_project(request, binder_name, name, template_section = 'Overview'):
	"""
	The standard landing page, showing status, feed, activity and calendar.
	"""
	try:
		item = Project.objects.get(slug = name, binder = Binder.objects.get(slug = binder_name))
	except Project.DoesNotExist:
		return HttpResponseRedirect('/roadmap/ledger')
	except Binder.DoesNotExist:
		return HttpResponseRedirect('/roadmap/ledger')

	if not user_can_view(request, item):
		return HttpResponseRedirect('/roadmap/ledger')

	note_items = Item.objects.filter(project = item, item_type__name = 'Note')
	notes = Note.objects.filter(item__project = item, item__state = 0)

	#
	# Do we have any locations?
	#
	find_locations = Location.objects.filter(project = item).order_by('order')
	if len(find_locations) == 0:
		current_work = Location()
		current_work.description = 'Current Work'
		current_work.project = item
		current_work.method = 'action'
		current_work.order = 0
		current_work.save()

		delivered_work = Location()
		delivered_work.description = 'Delivered'
		delivered_work.method = 'deliver'
		delivered_work.project = item
		delivered_work.order = 1
		delivered_work.save()

		deleted_work = Location()
		deleted_work.description = 'Abandoned'
		deleted_work.method = 'delete'
		deleted_work.project = item
		deleted_work.order = 2
		deleted_work.save()

		for loop_item in Item.objects.filter(project = item):
			#
			# Delivered. Move to the new delivered location
			if loop_item.location.method == constants.LOCATION_DELIVERED:
				loop_item.location = delivered_work
			#
			# Deleted, move to abandoned
			if loop_item.location.method == constants.LOCATION_DELETED:
				loop_item.location = deleted_work
			if loop_item.location.method != constants.LOCATION_DELIVERED and  loop_item.location.method != constants.LOCATION_DELETED:
				# move to current work, then either action or leave as reported
				loop_item.location = current_work
				#
				# Reported -> Identified
				if loop_item.location.method == constants.LOCATION_REPORTED:
					loop_item.item_state = ItemState.objects.get(constant = constants.ITEMSTATE_IDENTIFIED)
				#
				# PRoduction -> Actioned
				if loop_item.location.method == constants.LOCATION_PRODUCTION:
					loop_item.item_state = ItemState.objects.get(constant = constants.ITEMSTATE_ACTIONED)
				#
				# Completed and verified
				if loop_item.fixed and loop_item.validated:
					loop_item.item_state = ItemState.objects.get(constant = constants.ITEMSTATE_VERIFIED)
				#
				# Just Completed
				elif loop_item.fixed and loop_item.validated == False:
					loop_item.item_state = ItemState.objects.get(constant = constants.ITEMSTATE_COMPLETED)

			loop_item.save()

		find_locations = Location.objects.filter(project = item).order_by('order')

	#
	# Fetch emails
	#
	emails = Email.objects.filter(item__project = item, item__state = 0)
	email_manager = EmailProcess()
	for loop_item in emails:
		loop_item.body = '\n'.join(
			email_return_body(
				email_manager.read_email(
					str(loop_item.file_id)
				)
			)
		).replace('=20', '')

	follow_ups = Item.objects.filter(project = item, assigned_to = request.user, follow_up = True)

	row = GridRow()
	for loop_location in Location.objects.filter(project = item).order_by('order'):
		grid_item = GridRow()
	#	#
	#	# Get all issues
	#	#
		grid_item.items = []
		for loop_state in ItemState.objects.all():
			all_items = Item.objects.filter(
				project = item,
				location = loop_location,
				item_state = loop_state,
				state = 0,
			).exclude(
				item_type = Type.objects.get(name = 'Email')
			).exclude(
				item_type = Type.objects.get(name = 'Note')
			).exclude(
				item_type = Type.objects.get(name = 'File')
			)

			grid_item.items.append(all_items.count())
		grid_item.location = loop_location
		#grid_item.all_count = all_items.count()


	#	grid_item.all_count = all_items.count()
	#	grid_item.my_count = all_items.filter(assigned_to = request.user).count()
	#	#
	#	# For reporting, get sum of all hours
	#	#
	#	if loop_location.method == 'report':
	#		grid_item.hours = all_items.aggregate(Sum('hours_estimated'))
	#		try:
	#			#coverage = int(float((grid_item.all_count - all_items.filter(hours_estimated = 0).aggregate(Count('hours_estimated'))['hours_estimated__count'])) / float(grid_item.all_count) * 100)  # number of 0 estimates
	#			missing_estimates = all_items.filter(hours_estimated = 0).aggregate(Count('hours_estimated'))['hours_estimated__count']
	#			if missing_estimates != 0:
	#				grid_item.missing_estimates = missing_estimates
	#		except:
	#			pass
	#	#
	#	# For production, get sum of all hours + sum of completed hours
	#	#
	#	if loop_location.method == 'action':
	#		grid_item.hours = all_items.aggregate(Sum('hours_estimated'))
	#		grid_item.hours_completed = all_items.filter(fixed = True).aggregate(Sum('hours_total'))
	#		#coverage = int(float((grid_item.all_count - all_items.filter(hours_estimated = 0).aggregate(Count('hours_estimated'))['hours_estimated__count'])) / float(grid_item.all_count) * 100)  # number of 0 estimates
	#		#if coverage != 100:
	#		#	grid_item.coverage = coverage
	#		missing_estimates = all_items.filter(hours_estimated = 0).aggregate(Count('hours_estimated'))['hours_estimated__count']
	#		if missing_estimates != 0:
	#			grid_item.missing_estimates = missing_estimates
	#		grid_item.all_items_completed_count  = all_items.filter(fixed = True).count()
	#		grid_item.all_items_incompleted_count  = all_items.filter(fixed = False).count()
	#		grid_item.all_items_failed_count  = all_items.filter(fixed = False, validated = True).count()
	#
	#		grid_item.my_items_completed_count  = all_items.filter(assigned_to = request.user, fixed = True).count()
	#		grid_item.my_items_incompleted_count  = all_items.filter(assigned_to = request.user, fixed = False).count()
	#		grid_item.my_items_failed_count  = all_items.filter(assigned_to = request.user, fixed = False, validated = True).count()
	#
	#	if loop_location.method == 'test':
	#		grid_item.all_items_validated_count  = all_items.filter(fixed = True, validated = True).count()
	#		grid_item.my_items_validated_count  = all_items.filter(assigned_to = request.user, fixed = True, validated = True).count()
	#		grid_item.my_items_unvalidated_count  = all_items.filter(assigned_to = request.user, fixed = True, validated = False).count()
	#		grid_item.all_items_unvalidated_count  = all_items.filter(fixed = True, validated = False).count()
	#
		row.items.append(grid_item)
	#
	# Fetch files
	#
	files = File.objects.filter(
		item__item_type = Type.objects.get(name = 'File'),
		item__state = 0,
		item__project = item,
	)

	binder = item.binder
	team = item.binder.team.all().order_by('first_name', 'last_name')
	team = gravatar_list(team)

	binder_items_requirements = Requirement.objects.filter(item__project = item)
	binder_items_issues = Issue.objects.filter(item__project = item)

	delivery_notes = []
	for loop_item in binder_items_requirements.exclude(item__location__method = 'delete'): #=Location.objects.get(method='deliver')):
		if loop_item.delivery_notes != '' and loop_item.delivery_notes != None:
			delivery_notes.append(
				{
					'type' : 'Requirement',
					'id' : loop_item.item.id,
					'text' : loop_item.delivery_notes,
					'description' : loop_item.item.description,
				}
			)
	for loop_item in binder_items_issues.exclude(item__location__method = 'delete'):#=Location.objects.get(method='deliver')):
		if loop_item.delivery_notes != '' and loop_item.delivery_notes != None:
			delivery_notes.append(
				{
					'type' : 'Issue',
					'id' : loop_item.item.id,
					'text' : loop_item.delivery_notes,
					'description' : loop_item.item.description,
				}
			)

	updates_header, feed = latest_updates(request)
	feed = feed.filter(item__project = item)
	feed = feed.filter(item__state = 0)
	targets = Target.objects.filter(Q(project = item, user = request.user, public = 0) | Q(project = item, public = 1)).filter(active = True)
	tag_cloud = Tag.objects.cloud_for_model(Item, 4, tagging.utils.LOGARITHMIC, {'project': item } )
	#
	# Get the viewsettings
	#
	project_setting = ProjectSetting.objects.get(const = 'VIEWPREFERENCES_DEFAULT_VIEWSTATE')
	view_settings = ''
	try:
		user_project_setting = UserProjectSetting.objects.get(
			Q(
				project = item,
				user = request.user,
				project_setting = project_setting
			)
		)
		view_settings = user_project_setting.value
	except UserProjectSetting.DoesNotExist:
		pass

	user_filters = item.project_filters.filter(user = request.user)

	return render_to_response(
		'ledger/project.html',
		{
			'user_filters': user_filters,
			'template_section': template_section.lower(),
			'view_settings': view_settings,
			'follow_ups' : follow_ups,
			'tag_cloud' : tag_cloud,
			'item': item,
			'notes': notes,
			'emails': emails,
			'settings': settings,
			'row': row,
			'calendar_output': mini_calendar(request, binder, item),
			'binder': item.binder,
			'team': team,
			'reporters': item.binder.reporters.all(),
			'producers': item.binder.producers.all(),
			'delivery_notes': delivery_notes,
			'headernav': 'notifications',
			'active_items': active_items(request),
			'files': files,
			'updates_header': updates_header,
			'feed': feed,
			'locations': Location.objects.all(),
			'targets': targets,
			'find_locations': find_locations,
		},
		context_instance = RequestContext(request),
	)

def get_next_id(email_dir):
	all_files = os.listdir(email_dir)
	last_index = 0

	for loop_file in all_files:
		file_number = int(loop_file)
		if file_number > last_index:
			last_index = file_number
	return str(last_index+1)

def check_email(request):
	import feedparser
	import uuid

	tags = Tag.objects.usage_for_model(Item)
	server = POP3(settings.ROADMAP_EMAIL_SERVER)
	server.user(settings.ROADMAP_EMAIL_USERNAME)
	server.pass_(settings.ROADMAP_EMAIL_PASSWORD)
	messages = server.list()[1]
	emails = []
	email_dir = os.path.join(settings.MEDIA_ROOT, 'emails')
	debug = []

	for message in messages:
		#print('got message')
		message_number = int(message.split(' ')[0])
		message_size = int(message.split(' ')[1])
		message_retrieve = server.retr(message_number)[1]
		headers = []
		body = []
		write_body = False
		#
		# Save to file
		#
		message_id = str(uuid.uuid1()) #get_next_id(email_dir)
		filename = os.path.join(email_dir, message_id)
		output = open(filename, 'wt')
		for line in message_retrieve:
			output.write(line + '\n')
			if write_body:
				body.append(line)
			else:
				headers.append(line)
			if line == '':
				write_body = True
		output.close()
		#
		# Parse headers
		#
		email_headers = {}
		for line in headers:
			colon = line.find(':')
			if colon != -1:
				key = line[:colon].lower().strip()
				value = line[colon + 1:].strip()
				email_headers[key] = value
				#print('%s\n\t%s' % (key, value))
		#
		# Now figure out the binders
		#
		split_description = email_headers['subject'].split(' ')
		found_binders = []
		for loop_item in split_description:
			#print('scanning binder %s' % loop_item)
			found_binders.extend(Binder.objects.filter(Q(slug__iexact=loop_item)|Q(name__iexact=loop_item)))
		#print('found binders %s' % found_binders)
		#
		# Now add to the binder's default project
		#
		for loop_item in found_binders:
			item = Item()
			item.item_type = Type.objects.get(name = 'Email')
			item.priority = Priority.objects.get(default = 1)

			item.location = Location.objects.get(name = 'Reported')
			item.project = project = loop_item.default_project
			item.assigned_to = item.project.binder.owner

			#
			# create a new email object, but we can't hook it to the item object
			# until the item has been saved.
			# we can't save the item until we know the binder and project
			#
			email_item = Email()
			email_item.file_id = message_id
			if 'references' in email_headers.keys():
				#print('setting references')
				email_item.references = email_headers['references']
			if 'message-id' in email_headers.keys():
				#print('setting message_id')
				email_item.message_id = email_headers['message-id']
			if 'in-reply-to' in email_headers.keys():
				email_item.in_reply_to = email_headers['in-reply-to']
			if 'subject' in email_headers.keys():
				#print('setting description')
				item.description = email_headers['subject']
			if 'from' in email_headers.keys():
				email_item.email_from = email_headers['from']
			if 'to' in email_headers.keys():
				email_item.email_to = email_headers['to']
			if 'date' in email_headers.keys():
				parse_date = feedparser._parse_date(email_headers['date'])
				email_item.date_time = datetime.datetime(*(parse_date[0:6]))
			#
			# Save the item, then link email->item
			#
			item.save()
			email_item.item = item

			#email_item.message = '\n'.join(body)
			#email_item.html = '<br/>'.join(body)
			#emails.append(email_item)
			tag_list = []
			for tag in tags:
				if item.description.find(tag.name) != -1:
					tag_list.append(tag.name)
			item.tags = ' '.join(tag_list)
			item.date_time = datetime.datetime.now()

			#print('saving item')
			item.save()
			email_item.save()
		#
		# Finally, delete from server
		#
		#print('deleting item')
		server.dele(message_number)

		#for user in User.objects.all():
		#	debug.append('adding feed to %s' % user)
		#	feed = Feed()
		#	feed.description = '<a href="/roadmap/ledger/item/%s">Email</a> from %s to %s: "%s"' % (item.id, email_item.email_from, email_item.email_to, item.description,)
		#	feed.user = user
		#	feed.save()
	server.quit()
	return render_to_response(
		'ledger/email.html',
		{
			'emails' : emails,
			'debug' : debug,
		},
		context_instance = RequestContext(request),
	)

@login_required
def profile(request, username):
	user = User.objects.get(username = username)
	binders = []

	for loop_binder in Binder.objects.all():
		if user in loop_binder.reporters.all():
			#print('iun')
			if loop_binder not in binders:
				binders.append(loop_binder)

		if user in loop_binder.producers.all():
			if loop_binder not in binders:
				binders.append(loop_binder)

		if user == loop_binder.owner:
			if loop_binder not in binders:
				binders.append(loop_binder)

	return render_to_response(
		'ledger/forms/Profile.html',
		{
			'profile_user': user,
			'binders': binders,
			'active_items' : active_items(request),
			'clients': Client.objects.all().order_by('name'),
		},
		context_instance = RequestContext(request),
	)

@csrf_exempt
@login_required
def item_details_location(request):
	location = Location.objects.get(id = request.POST.get('location_id'))
	item = Item.objects.get(id = request.POST.get('item_id'))
	item.location = location
	item.save()

	comment = Comment()
	comment.user = request.user
	comment.item = item
	comment.message = '*** Moved to %s ***' % location
	comment.date_time = datetime.datetime.now()
	comment.save()

	return render_to_response(
		'ledger/objects/extra_details.html',
		{
			'item': item,
			'priorities' : Priority.objects.all().order_by('-order'),
			'project' : Project.objects.filter(binder = item.project.binder),
			'users' : item.project.binder.team.all(),
			'location' : Location.objects.filter(project = item.project),
			'targets' : Target.objects.filter(
				Q(project = item.project, user = request.user, public = 0) | Q(project = item.project, public = 1)
			).filter(active = True),
			'related_items' : get_tagged_related_items(item),
		},
		context_instance = RequestContext(request),
	)

def get_tagged_related_items(item):
	scan_related_items = TaggedItem.objects.get_related(item, Item)
	related_items = []
	for loop_item in scan_related_items:
		if loop_item.project == item.project:
			related_items.append(loop_item)

	if len(related_items) > 10:
		related_items = related_items[:10]
	return related_items

@login_required
def reports(request):
	user = request.user
	teams = user.binder_set.all()
	clients = Client.objects.filter(binder__team__in = teams)
	projects = Project.objects.filter(binder__client__in = clients).order_by('name')
	locations = Location.objects.all().order_by('id')
	users = User.objects.all().order_by('first_name', 'last_name')
	items = None
	search = {}
	filters = {}
	subquery = {}

	if request.POST.get('search', '') != '':
		search['user'] = []
		search['client'] = []
		search['projects'] = []
		search['location'] = []
		search
		for key, value in request.POST.iteritems():
			#print('Checking %s -> %s' % (key, value))
			if key.find('_') != -1:
				split_key = key.split('_')
				new_key = split_key[0]
				if not search.has_key(new_key):
					search[new_key] = ''
				search[new_key].append(int(split_key[1]))

		if len(search['user']) > 0:
			filters['assigned_to__in'] = search['user']
		if len(search['binder']) > 0:
			filters['project__in'] = search['projects']
		if len(search['location']) > 0:
			filters['location__in'] = search['location']

		query = Q(**filters)

		if request.POST.get('completed', '') != '':
			filters['fixed'] = True
			subquery['fixed'] = True

		if request.POST.get('verified', '') != '':
			filters['validated'] = True
			subquery['validated'] = True

		if len(subquery) > 0:
			items = Item.objects.filter(query, Q(**subquery)).order_by('project')
		else:
			items = Item.objects.filter(query).order_by('project')

	return render_to_response(
		'ledger/reports/index.html',
		{
			'clients': clients,
			'teams': teams,
			'projects': projects,
			'locations': locations,
			'users': users,
			'items': items,
			'search': search,
			'filters': filters,
		},
		context_instance = RequestContext(request),
	)

@login_required
def ownership(request, item_id):
	item = Item.objects.get(id = item_id)
	ownership_list = Assigned.objects.filter(item=item)
	ownership_list.order_by('date_time')

	search_id = request.GET.get('search_id','')
	search_found = None
	search_count = None
	search_url = None
	if search_id:
		search_data = load_search(search_id)
		if search_data:
			search_url = search_id # search_data['searchUrl']
			items = search_data.items
			index = -1
			for loop_item in items:
				#print('item %s' %loop_item)
				#print('id %s ' % item.id)
				index+=1
				if str(loop_item) == str(item.id):
					search_found = index + 1
			#
			# Has search expire
			#
			#if search_found == None:
			#	search_id = 'Expired'
			#else:
			search_count = len(items)

	return render_to_response(
		'ledger/ownership.html',
		{
			'item': item,
			'ownership_list': ownership_list,
			'active_items' : active_items(request),
			'search_url': search_url,
			'search_id' : search_id,
			'search_count' : search_count,
			'search_found' : search_found,
		},
		context_instance = RequestContext(request),
	)

@csrf_exempt
@login_required
def item_details_estimates(request):
	item = Item.objects.get(id = request.POST.get('item_id'))

	if item.assigned_to == request.user:
		item.hours_estimated = Decimal(request.POST.get('estimated'))
		item.hours_total = Decimal(request.POST.get('total'))
		item.save()

		feed = Feed()
		feed.description = '<a href="/roadmap/ledger/item/%s">%s</a> has updated schedule details.' % (item.id, escape(item.description))
		feed.date_time = datetime.datetime.now()
		feed.user = request.user
		feed.item = item
		feed.author = request.user
		feed.save()

	content = ''

	return render_to_response(
		'ledger/objects/time.html',
		{
			'item' : item,
		},
		context_instance = RequestContext(request),
	)

@csrf_exempt
@login_required
def item_toggle_followup(request):
	item = Item.objects.get(id = request.POST.get('item_id'))
	value = request.POST.get('value', 'false') == 'true'

	item.follow_up = value
	item.save()

	content = ''

	if item.follow_up:
		feed_text = '<a href="/roadmap/ledger/item/%s">%s</a> requires following up.' % (item.id, escape(item.description))

		feed = Feed()
		feed.description = feed_text
		feed.date_time = datetime.datetime.now()
		feed.user = request.user
		feed.item = item
		feed.author = request.user
		feed.save()

		if item.assigned_to != request.user:
			feed = Feed()
			feed.description = feed_text
			feed.date_time = datetime.datetime.now()
			feed.user = item.assigned_to
			feed.item = item
			feed.author = request.user
			feed.save()

		content = 'success'
	return HttpResponse(
		content,
		mimetype='text/plain',
	)

@login_required
@csrf_exempt
def item_details_owner(request):
	user = User.objects.get(id = request.POST.get('owner_id'))
	item = Item.objects.get(id = request.POST.get('item_id'))
	if item.assigned_to != user:
		item.assigned_to = user

		#
		# Was the last comment written by the logged in user? if so, mark it as had a reply
		#
		fetch_comments = Comment.objects.filter(item = item).order_by('date_time')
		if fetch_comments.count() > 0:
			if fetch_comments[0].user == request.user:
				item.replied = True
		item.unseen = True
		item.save()

		feed = Feed()
		feed.description = '<a href="/roadmap/ledger/item/%s">Item %s</a> has been assigned to you.' % (item.id, escape(item.description))
		feed.date_time = datetime.datetime.now()
		feed.user = user
		feed.item = item
		feed.author = request.user
		feed.save()

		#
		# Track assigned to
		#
		assigned = Assigned()
		assigned.item = item
		assigned.location = item.location
		assigned.user = item.assigned_to
		assigned.comments = "Reassigned"
		assigned.save()

	return render_to_response(
		'ledger/objects/extra_details.html',
		{
			'item': item,
			'priorities' : Priority.objects.all().order_by('-order'),
			'project' : Project.objects.filter(binder = item.project.binder),
			'users' : item.project.binder.team.all(),
			'location' : Location.objects.all(),
			'targets' : Target.objects.filter(
				Q(project = item.project, user = request.user, public = 0) | Q(project = item.project, public = 1)
			).filter(active = True),
			'related_items' : get_tagged_related_items(item),
		},
		context_instance = RequestContext(request),
	)

@login_required
@csrf_exempt
def item_details_comment(request):
	item = Item.objects.get(id = request.POST.get('item_id'))
	comment_text = request.POST.get('comments')
	#
	# comment text needs to be HTML escaped here
	#
	comment = Comment()
	comment.user = request.user
	comment.item = item
	comment.message = comment_text
	comment.date_time = datetime.datetime.now()
	comment.save()

	#
	# If it was set to follow up, clear the request
	#
	if item.assigned_to == request.user:
		item.follow_up = False
		item.save()
	else:
		item.replied = True
		item.unseen = True
		item.save()

	comment_teaser = comment_text
	if len(comment_teaser) > 100:
		comment_teaser = comment_teaser[:100] + '...'

	extra = {}
	fetch_comments = Comment.objects.filter(item = item).order_by('date_time')
	extra['comments'] = fetch_comments

	user_set = set()
	user_set.add(item.assigned_to)
	for loop_comment in fetch_comments:
		if loop_comment.user not in user_set:
			user_set.add(loop_comment.user)

	for loop_user in user_set:
		feed = Feed()
		feed.description = '<a href="/roadmap/ledger/profile/%s">%s %s</a> has commented on <a href="/roadmap/ledger/item/%s">%s</a><p><em>&quot;%s&quot;</em></p>' % (
			request.user.username, request.user.first_name, request.user.last_name, item.id, escape(item.description), escape(comment_teaser)
		)
		feed.date_time = datetime.datetime.now()
		feed.user = loop_user
		feed.item = item
		feed.author = request.user
		feed.save()

	return render_to_response(
		'ledger/forms/comments.html',
		{
			'extra': extra,
			'user': request.user,
			'item': item,
		},
		context_instance = RequestContext(request),
	)

def test_serialize(request):
	item = Item.objects.filter(id = 130)
	json_serializer = serializers.get_serializer("json")()
	return HttpResponse(
		json_serializer.serialize(item, ensure_ascii=False),
		mimetype='application/json',
	)

@csrf_exempt
@login_required
def item_details_project(request):
	item = Item.objects.get(id = request.POST.get('item_id'))

	# check if it's a  new project, add it
	new_project_name = request.POST.get('new_project', '')
	if new_project_name != '':
		new_project = Project()
		new_project.name = new_project_name
		new_project.binder = item.project.binder
		new_project.save()
		project = new_project
	else:
		project = Project.objects.get(id = request.POST.get('project_id'))
	item.project = project
	item.save()

	return render_to_response(
		'ledger/objects/extra_details.html',
		{
			'item': item,
			'priorities' : Priority.objects.all().order_by('-order'),
			'project' : Project.objects.filter(binder = item.project.binder),
			'users' : item.project.binder.team.all(),
			'location' : Location.objects.all(),
			'targets' : Target.objects.filter(
				Q(project = item.project, user = request.user, public = 0) | Q(project = item.project, public = 1)
			).filter(active = True),
			'related_items' : get_tagged_related_items(item),
		},
		context_instance = RequestContext(request),
	)

@csrf_exempt
@login_required
def item_details_priority(request):
	item = Item.objects.get(id = request.POST.get('item_id'))
	priority = Priority.objects.get(id = request.POST.get('priority_id'))
	item.priority = priority
	item.save()

	return render_to_response(
		'ledger/objects/extra_details.html',
		{
			'item': item,
			'priorities' : Priority.objects.all().order_by('-order'),
			'project' : Project.objects.filter(binder = item.project.binder),
			'users' : item.project.binder.team.all(),
			'location' : Location.objects.all(),
			'targets' : Target.objects.filter(
				Q(project = item.project, user = request.user, public = 0) | Q(project = item.project, public = 1)
			).filter(active = True),
			'related_items' : get_tagged_related_items(item),
		},
		context_instance = RequestContext(request),
	)

@csrf_exempt
@login_required
def item_details_target(request):
	item = Item.objects.get(id = request.POST.get('item_id'))
	#if item.assigned_to == request.user:
	target_id = request.POST.get('target_id')
	#
	# Unattach any targets for this user and item
	#
	for loop_target in item.targets.filter(user=request.user):
		item.targets.remove(loop_target)

	if target_id == '0':
		pass
	else:
		target = Target.objects.get(id = target_id)
		try:
			for loop_item in item.targets.all:
				#print('%s' % loop_item)
				pass
		except Exception, ex:
			#print('%s' % ex)
			pass
		item.targets.add(target)
	item.save()

	feed = Feed()
	feed.description = '<a href="/roadmap/ledger/item/%s">%s</a> has updated schedule details.' % (item.id, escape(item.description))
	feed.date_time = datetime.datetime.now()
	feed.user = request.user
	feed.item = item
	feed.author = request.user
	feed.save()

	return render_to_response(
		'ledger/objects/extra_details.html',
		{
			'item': item,
			'priorities' : Priority.objects.all().order_by('-order'),
			'project' : Project.objects.filter(binder = item.project.binder),
			'users' : item.project.binder.team.all(),
			'location' : Location.objects.all(),
			'targets' : Target.objects.filter(
				Q(project = item.project, user = request.user, public = 0) | Q(project = item.project, public = 1)
			).filter(active = True),
			'related_items' : get_tagged_related_items(item),
		},
		context_instance = RequestContext(request),
	)

@login_required
@csrf_exempt
def edit_checklist_item(request):
	item_type = request.POST.get('item_type')
	text = request.POST.get('text')
	text = text.strip()

	checklistitem_id = request.POST.get('checklistitem_id')
	checklist_item = ChecklistItem.objects.get(id = checklistitem_id)

	if text == '':
		checklist_item.delete()
	else:
		checklist_item.text = text
		checklist_item.save()

	item = Item.objects.get(id = request.POST.get('item_id'))
	checklist_items_new = ChecklistItem.objects.filter(item = item).order_by('order_index')

	return render_to_response(
		'ledger/forms/%s/Steps.html' % item_type,
		{
			'checklist_items' : checklist_items_new,
			'item' : item,
		},
		context_instance = RequestContext(request),
	)

@csrf_exempt
def upload_profile(request):
	#print('getting upload')
	upload_path = os.path.join(settings.MEDIA_ROOT, 'uploads')
	file_uuid = str(uuid.uuid1())
	full_file_name = os.path.join(upload_path, file_uuid)
	#print('full file name %s' % full_file_name)

	#for loop_item in request.FILES:
		#print(str(loop_item))

	if request.GET.get('base64', '') == 'true':
		# Chrome
		upload_file = request.raw_post_data
		output = open(full_file_name, 'wb+')
		output.write(base64.decodestring(upload_file))
		output.close()
	else:
		# File API
		try:
			upload_file = request.FILES['attachFile']
			output = open(full_file_name, 'wb+')
			for chunk in upload_file.chunks():
				output.write(chunk)
			output.close()
		except Exception,ex:
			#print(str(ex))
			upload_file = request.raw_post_data
			output = open(full_file_name, 'wb+')
			output.write(upload_file)
			output.close()

	return HttpResponse(
		'done:' + file_uuid,
		mimetype = 'text/html',
	)

@csrf_exempt
@login_required
def add_checklist_item(request):
	item = Item.objects.get(id = request.POST.get('item_id'))
	item_text = request.POST.get('item_text')
	item_type = request.POST.get('item_type')
	file_uuid = request.POST.get('file_uuid')

	#print('add %s' % item_text)
	#print(request.POST.get('item_id'))
	#print(item)

	#print('getting upload directory')
	upload_path = os.path.join(settings.MEDIA_ROOT, 'uploads')
	#print('getting attachment')
	attachment_path = os.path.join(settings.MEDIA_ROOT, 'attachments')
	#print('file_uuid %s' % file_uuid)
	directory_name = os.path.join(upload_path, file_uuid)
	#print('dir %s' % directory_name)

	checklist_items = ChecklistItem.objects.filter(item = item)
	checklist_item = ChecklistItem()
	checklist_item.item = item
	checklist_item.text = item_text
	checklist_item.order_index = checklist_items.count() + 1
	checklist_item.save()

	if os.path.exists(directory_name):
		#print('has attachment. scanning %s' % directory_name)
		file_list = os.listdir(directory_name)
		if len(file_list) > 1:
			file_list = [(os.path.getmtime(x), x) for x in os.listdir(directory_name)]
			##print('sorting. length %s' % len(file_list))
			file_list.sort()
			#print('getting attached')
			attached_file = file_list[-1][1]
		elif len(file_list) == 1:
			attached_file = file_list[0]
		elif len(file_list) == 0:
			attached_file = None

		if attached_file:
			#print('attached %s' % ((attached_file)))

			attachment_filename = os.path.join(attachment_path, str(checklist_item.id))
			if not os.path.exists(attachment_filename):
				#print('creating dir %s' % attachment_filename)
				os.mkdir(attachment_filename)
			old_file = os.path.join(directory_name, attached_file)
			new_file = os.path.join(attachment_filename, attached_file)
			#print('copying from %s to %s' % (old_file, new_file))
			shutil.copyfile(old_file, new_file)

			shutil.rmtree(directory_name)
			checklist_item.filename = attached_file
			checklist_item.save()

	#print('saved')

	checklist_items_new = ChecklistItem.objects.filter(item = item).order_by('order_index')

	return render_to_response(
		'ledger/forms/%s/Steps.html' % item_type,
		{
			'checklist_items' : checklist_items_new,
			'item' : item,
		},
		context_instance = RequestContext(request),
	)

@csrf_exempt
def add_checklist_file(request):
	item_type = request.GET.get('item_type')
	file_uuid = request.GET.get('file_uuid')
	item_id = request.GET.get('item_id')
	file_name = None

	if request.method == 'POST':
		#print('adding file %s' % len(request.FILES))
		try:
			file = request.FILES["attachFile"]
		except Exception,ex:
			#print(str(ex))
			pass
		#print('got file')
		attachment_path = os.path.join(settings.MEDIA_ROOT, 'uploads')
		directory_name = os.path.join(attachment_path, file_uuid)
		if not os.path.exists(directory_name):
			#print('creating dir')
			os.mkdir(directory_name)
		file_name = file.name
		full_file_name = os.path.join(directory_name, file_name)
		#print('outputting to %s' % full_file_name)

		output = open(full_file_name, 'wb+')
		for chunk in file.chunks():
			output.write(chunk)
		output.close()

	return render_to_response(
		'ledger/forms/AddChecklistFile.html',
		{
			'item_id' : item_id,
			'file_uuid' : file_uuid,
			'file_name' : file_name,
		},
		context_instance = RequestContext(request),
	)

@csrf_exempt
@login_required
def item_details_mark_completed(request):
	item = Item.objects.get(id = request.POST.get('item_id'))
	item.item_state = ItemState.objects.get(id = 3)
	item.save()

	for loop_user in user_for_binder(request, item.project.binder):
		feed = Feed()
		feed.description = '<a href="/roadmap/ledger/profile/%s">%s %s</a> has marked <a href="/roadmap/ledger/item/%s">%s</a> as completed.' % (
			request.user.username,
			request.user.first_name,
			request.user.last_name,
			item.id,
			escape(item.description)
		)
		#print(feed.description)
		feed.date_time = datetime.datetime.now()
		feed.user = loop_user # item.assigned_to
		feed.item = item
		feed.author = request.user
		feed.save()

	comment = Comment()
	comment.user = request.user
	comment.item = item
	comment.message = '*** Completed ***'
	comment.date_time = datetime.datetime.now()
	comment.save()

	return render_to_response(
		'ledger/objects/extra_details.html',
		{
			'item': item,
			'priorities' : Priority.objects.all().order_by('-order'),
			'project' : Project.objects.filter(binder = item.project.binder),
			'users' : item.project.binder.team.all(),
			'location' : Location.objects.all(),
			'targets' : Target.objects.filter(
				Q(project = item.project, user = request.user, public = 0) | Q(project = item.project, public = 1)
			).filter(active = True),
			'related_items' : get_tagged_related_items(item),
		},
		context_instance = RequestContext(request),
	)

@csrf_exempt
@login_required
def item_details_mark_reopened(request):
	location = Location.objects.get(method='action')

	item = Item.objects.get(id = request.POST.get('item_id'))
	item.item_state = ItemState.objects.get(id = 2)

	#
	# Testing -> Production
	#
	previous_producer = None

	ownership_list = Assigned.objects.filter(item=item)
	ownership_list.order_by('id')
	for loop_owner in ownership_list:
		#print('checking %s' % loop_owner.user)
		if loop_owner.location == location: # has it been in testing before?
			#print('is previous producer')
			previous_producer = loop_owner.user
			break;
		# We want the previous producer
		if loop_owner.user in item.project.binder.producers.all() or loop_owner == item.project.binder.owner:
			#print('remembering %s' % loop_owner.user)
			previous_producer = loop_owner.user
	#print('previous tester %s' % previous_producer)
	if previous_producer != None:
		item.assigned_to = previous_producer

		#
		# Track assigned to
		#
		assigned = Assigned()
		assigned.item = item
		assigned.location = location
		assigned.user = item.assigned_to
		assigned.comments = "Reassigned"
		assigned.save()

	#item.location = location
	item.save()

	feed = Feed()
	feed.description = '<a href="/roadmap/ledger/profile/%s">%s %s</a> has reopened <a href="/roadmap/ledger/item/%s">%s</a>.</span>' % (
		request.user.username,
		request.user.first_name,
		request.user.last_name,
		item.id,
		escape(item.description)
	)
	feed.date_time = datetime.datetime.now()
	feed.user = item.assigned_to
	feed.item = item
	feed.author = request.user
	feed.save()

	return render_to_response(
		'ledger/objects/extra_details.html',
		{
			'item': item,
			'priorities' : Priority.objects.all().order_by('-order'),
			'project' : Project.objects.filter(binder = item.project.binder),
			'users' : item.project.binder.team.all(),
			'location' : Location.objects.all(),
			'targets' : Target.objects.filter(
				Q(project = item.project, user = request.user, public = 0) | Q(project = item.project, public = 1)
			).filter(active = True),
			'related_items' : get_tagged_related_items(item),
		},
		context_instance = RequestContext(request),
	)

@csrf_exempt
@login_required
def item_details_mark_actioned(request):
	item = Item.objects.get(id = request.POST.get('item_id'))
	item.item_state = ItemState.objects.get(id = 2)
	item.save()

	for loop_user in user_for_binder(request, item.project.binder):
		feed = Feed()
		feed.description = '<a href="/roadmap/ledger/profile/%s">%s %s</a> has actioned <a href="/roadmap/ledger/item/%s">%s</a>. </span>' % (request.user.username, request.user.first_name, request.user.last_name, item.id, escape(item.description))
		feed.date_time = datetime.datetime.now()
		feed.user = loop_user #item.assigned_to
		feed.item = item
		feed.author = request.user
		feed.save()

	return render_to_response(
		'ledger/objects/extra_details.html',
		{
			'item': item,
			'priorities' : Priority.objects.all().order_by('-order'),
			'project' : Project.objects.filter(binder = item.project.binder),
			'users' : item.project.binder.team.all(),
			'location' : Location.objects.filter(project = item.project),
			'targets' : Target.objects.filter(
				Q(project = item.project, user = request.user, public = 0) | Q(project = item.project, public = 1)
			).filter(active = True),
			'related_items' : get_tagged_related_items(item),
		},
		context_instance = RequestContext(request),
	)
@csrf_exempt
@login_required
def item_details_mark_identified(request):
	item = Item.objects.get(id = request.POST.get('item_id'))
	item.item_state = ItemState.objects.get(id = 1)
	item.save()

	feed = Feed()
	feed.description = '<a href="/roadmap/ledger/profile/%s">%s %s</a> has halted work on <a href="/roadmap/ledger/item/%s">%s</a>. </span>' % (request.user.username, request.user.first_name, request.user.last_name, item.id, escape(item.description))
	feed.date_time = datetime.datetime.now()
	feed.user = item.assigned_to
	feed.item = item
	feed.author = request.user
	feed.save()

	return render_to_response(
		'ledger/objects/extra_details.html',
		{
			'item': item,
			'priorities' : Priority.objects.all().order_by('-order'),
			'project' : Project.objects.filter(binder = item.project.binder),
			'users' : item.project.binder.team.all(),
			'location' : Location.objects.filter(project = item.project),
			'targets' : Target.objects.filter(
				Q(project = item.project, user = request.user, public = 0) | Q(project = item.project, public = 1)
			).filter(active = True),
			'related_items' : get_tagged_related_items(item),
		},
		context_instance = RequestContext(request),
	)

@csrf_exempt
@login_required
def item_details_mark_failed(request):
	#location = Location.objects.get(method='action')

	item = Item.objects.get(id = request.POST.get('item_id'))
	item.item_state = ItemState.objects.get(id = 2)

	#
	# Testing -> Production
	#
	previous_producer = None

	ownership_list = Assigned.objects.filter(item=item)
	ownership_list.order_by('id')
	for loop_owner in ownership_list:
		#print('checking %s' % loop_owner.user)
		if loop_owner.location == location: # has it been in testing before?
			#print('is previous producer')
			previous_producer = loop_owner.user
			break;
		# We want the previous producer
		if loop_owner.user in item.project.binder.producers.all() or loop_owner == item.project.binder.owner:
			#print('remembering %s' % loop_owner.user)
			previous_producer = loop_owner.user
	#print('previous tester %s' % previous_producer)
	if previous_producer != None:
		item.assigned_to = previous_producer

		#
		# Track assigned to
		#
		assigned = Assigned()
		assigned.item = item
		#assigned.location = location
		assigned.user = item.assigned_to
		assigned.comments = "Reassigned"
		assigned.save()

	#item.location = location
	item.save()

	feed = Feed()
	feed.description = '<a href="/roadmap/ledger/profile/%s">%s %s</a> has marked <a href="/roadmap/ledger/item/%s">%s</a> as failed.' % (request.user.username, request.user.first_name, request.user.last_name, item.id, escape(item.description))
	feed.date_time = datetime.datetime.now()
	feed.user = item.assigned_to
	feed.item = item
	feed.author = request.user
	feed.save()

	return render_to_response(
		'ledger/objects/extra_details.html',
		{
			'item': item,
			'priorities' : Priority.objects.all().order_by('-order'),
			'project' : Project.objects.filter(binder = item.project.binder),
			'users' : item.project.binder.team.all(),
			'location' : Location.objects.all(),
			'targets' : Target.objects.filter(
				Q(project = item.project, user = request.user, public = 0) | Q(project = item.project, public = 1)
			).filter(active = True),
			'related_items' : get_tagged_related_items(item),
		},
		context_instance = RequestContext(request),
	)

@csrf_exempt
@login_required
def item_details_mark_verified(request):
	item = Item.objects.get(id = request.POST.get('item_id'))
	item.item_state = ItemState.objects.get(id = 4)
	item.save()

	for loop_user in user_for_binder(request, item.project.binder):
		feed = Feed()
		feed.description = '<a href="/roadmap/ledger/profile/%s">%s %s</a> has marked <a href="/roadmap/ledger/item/%s">%s</a> as verified.' % (request.user.username, request.user.first_name, request.user.last_name, item.id, escape(item.description))
		feed.date_time = datetime.datetime.now()
		feed.user = loop_user #item.assigned_to
		feed.item = item
		feed.author = request.user
		feed.save()

	comment = Comment()
	comment.user = request.user
	comment.item = item
	comment.message = '*** Verified ***'
	comment.date_time = datetime.datetime.now()
	comment.save()

	return render_to_response(
		'ledger/objects/extra_details.html',
		{
			'item': item,
			'priorities' : Priority.objects.all().order_by('-order'),
			'project' : Project.objects.filter(binder = item.project.binder),
			'users' : item.project.binder.team.all(),
			'location' : Location.objects.all(),
			'targets' : Target.objects.filter(
				Q(project = item.project, user = request.user, public = 0) | Q(project = item.project, public = 1)
			).filter(active = True),
			'related_items' : get_tagged_related_items(item),
		},
		context_instance = RequestContext(request),
	)

#
# Delivery workflow
#
@login_required
def make_delivery_index(request, client_name = None, binder_name = None, project_name = None):
	client_items = []
	client_filter = {}
	if client_name:
		try:
			find_client = Client.objects.get(slug = client_name)
			client_filter['id'] = find_client.id
		except Client.DoesNotExist:
			pass
	for loop_client in Client.objects.filter(**client_filter).order_by('name'):
		loop_client.binders = []
		binder_filter = {}
		binder_filter['client'] = loop_client
		binder_filter['active'] = True

		if binder_name:
			try:
				find_binder = Binder.objects.get(slug = binder_name)
				binder_filter['id'] = find_binder.id
			except Binder.DoesNotExist:
				pass

		for loop_binder in Binder.objects.filter(**binder_filter).order_by('name'):
			loop_binder.projects = []
			for loop_project in Project.objects.filter(binder = loop_binder).order_by('name'):
				show = False
				if request.user in loop_binder.reporters.all():
					show = True
				if request.user in loop_binder.producers.all():
					show = True
				if request.user == loop_binder.owner:
					show = True
				if show:
					loop_binder.projects.append(loop_project)
			if len(loop_binder.projects) > 0:
				loop_client.binders.append(loop_binder)
		if len(loop_client.binders) > 0:
			client_items.append(loop_client)
	return render_to_response(
		'ledger/delivery/index.html',
		{
			'client_items' : client_items,
		},
		context_instance = RequestContext(request),
	)

@login_required
def make_delivery_location(request, client, binder, project):
	project_item = Project.objects.get(slug = project, binder__slug = binder, binder__client__slug = client)
	return render_to_response(
		'ledger/delivery/location.html',
		{
			'client': client,
			'binder': binder,
			'project': project,
			'project_item': project_item,
		},
		context_instance = RequestContext(request),
	)

@login_required
def make_delivery_items(request, client, binder, project, location):
	selected_items = []

	project_item = Project.objects.get(slug = project, binder__slug = binder, binder__client__slug = client)

	if location == 'testing':
		location_search = Location.objects.get(method = constants.LOCATION_PRODUCTION)
		destination_location = Location.objects.get(method = constants.LOCATION_TESTING)
	if location == 'production':
		location_search = Location.objects.get(method = constants.LOCATION_TESTING)
		destination_location = Location.objects.get(method = constants.LOCATION_DELIVERED)
	find_items = Q(
		state = 0,
		project__slug = project,
		project__binder__slug = binder,
		project__binder__client__slug = client,
		location = location_search
	)
	items = Item.objects.filter(find_items)

	# don't show files
	items = items.exclude(item_type = Type.objects.get(name = 'File'))
	items = items.exclude(item_type = Type.objects.get(name = 'Email'))
	items = items.exclude(item_type = Type.objects.get(name = 'Note'))
	items = items.exclude(location = Location.objects.get(method = constants.LOCATION_DELETED))

	items = items.order_by('location', 'item_group', )

	for loop_item in items:
		loop_item.selected = False
		if location == 'testing':
			if loop_item.fixed == True:
				loop_item.selected = True
				selected_items.append('k%s' % loop_item.id)
		if location == 'production':
			if loop_item.validated == True:
				loop_item.selected = True
				selected_items.append('k%s' % loop_item.id)

	location_list = []
	location_list.append(location_search)
	location_search.items = items
	location_search.item_count = len(items)

	request.session['selected_items'] = selected_items

	return render_to_response(
		'ledger/delivery/items.html',
		{
			'client': client,
			'binder': binder,
			'project': project,
			'location': location,
			'location_list': location_list,
			'selected_items': selected_items,
			'hide_switchers': True,
			'project_item': project_item,
			'destination_location': destination_location,
		},
		context_instance = RequestContext(request),
	)

@login_required
def make_delivery_notes(request, client, binder, project, location):
	project_item = Project.objects.get(slug = project, binder__slug = binder, binder__client__slug = client)

	if location == 'testing':
		location_search = Location.objects.get(method = constants.LOCATION_PRODUCTION)
		destination_location = Location.objects.get(method = constants.LOCATION_TESTING)
	if location == 'production':
		location_search = Location.objects.get(method = constants.LOCATION_TESTING)
		destination_location = Location.objects.get(method = constants.LOCATION_DELIVERED)

	new_selected_items = []
	notes_items = []
	# select the ticked items
	item_list = request.POST.getlist('id')
	items = Item.objects.filter(id__in = item_list)

	for fetch_item in items:
		if hasattr(fetch_item.linked_item, 'delivery_notes'):
			delivery_notes = fetch_item.linked_item.delivery_notes
			if delivery_notes != '':
				notes_items.append(fetch_item)

	new_selected_items = ['k%s' % item for item in item_list]
	request.session['selected_items'] = new_selected_items

	return render_to_response(
		'ledger/delivery/notes.html',
		{
			'client': client,
			'binder': binder,
			'project': project,
			'location': location,
			'selected_items': new_selected_items,
			'project_item': project_item,
			'destination_location': destination_location,
			'notes_items': notes_items,
		},
		context_instance = RequestContext(request),
	)

@login_required
def make_delivery_assign(request, client, binder, project, location):
	project_item = Project.objects.get(slug = project, binder__slug = binder, binder__client__slug = client)

	if location == 'testing':
		location_search = Location.objects.get(method = constants.LOCATION_PRODUCTION)
		destination_location = Location.objects.get(method = constants.LOCATION_TESTING)
	if location == 'production':
		location_search = Location.objects.get(method = constants.LOCATION_TESTING)
		destination_location = Location.objects.get(method = constants.LOCATION_DELIVERED)

	selected_items = request.session['selected_items']

	return render_to_response(
		'ledger/delivery/assign.html',
		{
			'client': client,
			'binder': binder,
			'project': project,
			'location': location,
			'selected_items': selected_items,
			'project_item': project_item,
			'destination_location': destination_location,
			'team': project_item.binder.all_users(),
		},
		context_instance = RequestContext(request),
	)

@login_required
def make_delivery_reassign(request, client, binder, project, location):
	project_item = Project.objects.get(
		slug = project,
		binder__slug = binder,
		binder__client__slug = client
	)
	reassign = request.POST.get('assign', '')
	tags = request.POST.get('tag', '')

	reassign_user = None
	if reassign.startswith('user'):
		reassign_user = User.objects.get(username = reassign[5:])

	if location == 'testing':
		location_search = Location.objects.get(method = constants.LOCATION_PRODUCTION)
		destination_location = Location.objects.get(method = constants.LOCATION_TESTING)
	if location == 'production':
		location_search = Location.objects.get(method = constants.LOCATION_TESTING)
		destination_location = Location.objects.get(method = constants.LOCATION_DELIVERED)

	selected_items = request.session['selected_items']
	print(selected_items)
	keys = [item.replace('k', '') for item in selected_items]

	items = Item.objects.filter(id__in = keys)

	for loop_item in items:
		loop_item.location = destination_location
		if location == 'testing':
			loop_item.fixed = True
		if location == 'production':
			loop_item.verified = True
		if reassign == 'no':
			pass
		elif reassign == 'reporter':
			pass
			#
			# reassign to original reporter
			#
		if reassign.startswith('user'):
			loop_item.assigned_to = reassign_user
			loop_item.unseen = True

		if tags != '':
			loop_item.tags += tags
		loop_item.save()
	#
	# Add item into the feed
	#
	for loop_user in user_for_binder(request, project_item.binder):
		feed = Feed()
		feed.description = '<a href="/roadmap/ledger/profile/%s">%s %s</a> has delivered to %s' % (
			request.user.username,
			request.user.first_name,
			request.user.last_name,
			destination_location.name,
		)

		feed.date_time = datetime.datetime.now()
		feed.user = loop_user
		#feed.item = item
		feed.author = request.user
		feed.save()
	request.session['selected_items'] = []

	return HttpResponseRedirect(
		reverse('roadmap.ledger.views.view_project', None, None, {
			'binder_name': binder,
			'name': project,
		}
	))

@login_required
def shell(request):
	if not request.user.email in [item[1] for item in settings.ADMINS]:
		return HttpResponseRedirect('/')
	output = ''
	command = request.POST.get('command', '')
	if command:
		import sys
		from StringIO import StringIO
		command = os.linesep.join(command.splitlines())

		buffer = StringIO()
		sys.stdout = buffer
		try:
			exec(command)
			sys.stdout = sys.__stdout__
			output = buffer.getvalue()
		except Exception, ex:
			output = ex

	return render_to_response(
		'ledger/reports/shell.html',
		{
			'output': output,
			'command': command,
		},
		context_instance = RequestContext(request),
	)

@login_required
def change_password(request):
	#print('changing password')
	form = PasswordForm()
	#print('got password form. %s' % request.method )
	if request.method == 'POST':
		#print('  change password. post')
		form = PasswordForm(request.POST)
		if form.is_valid():
			#print('   change password valid')
			user_item = User.objects.get(id = request.user.id)
			user_item.set_password(form.cleaned_data['password'])
			user_item.save()

			feed = Feed()
			feed.description = 'Your password has been changed.'
			feed.date_time = datetime.datetime.now()
			feed.user = request.user
			feed.author = request.user
			feed.save()

			return HttpResponseRedirect('/roadmap/ledger/profile/%s' % (request.user.username))
		else:
			#print('   change password invalid')
			pass

	return render_to_response(
		'ledger/forms/ChangePassword.html',
		{
			'form': form,
			'clients': Client.objects.all().order_by('name'),
		},
		context_instance = RequestContext(request),
	)

@login_required
def feed_growl(request):
	lastcheck = request.session.get('last_checked', datetime.datetime.now())
	feed_date = datetime.datetime(
		lastcheck.year,
		lastcheck.month,
		lastcheck.day,
		lastcheck.hour,
		lastcheck.minute,
		lastcheck.second,
	)
	#ten_seconds = datetime.datetime.timedelta(seconds=-10)
	#print(feed_date)
	data = Feed.objects.filter(
		date_time__gte = feed_date,
		user = request.user,
		item__state = 0
	)
	json_serializer = serializers.get_serializer("json")()
	request.session['last_checked'] = datetime.datetime.now()
	serialized = json_serializer.serialize(data, ensure_ascii = False)
	#try:
	#	serialized = simplejson.dumps(data)
	#except Exception,ex:
	#	#print(ex)
	#print(serialized)

	return HttpResponse(
		serialized,
		mimetype='application/json',
	)

def new_database(request):
	from django.core import management
	management.call_command('flush', verbosity=0, interactive=False)

def signup(request):
	form = SignupForm()
	if request.method == 'POST':
		form = SignupForm(request.POST)
		if form.is_valid():
			user = User()
			user.first_name = form.cleaned_data['first_name']
			user.last_name = form.cleaned_data['last_name']
			user.username = form.cleaned_data['username']
			user.set_password(form.cleaned_data['password'])
			user.save()
			return HttpResponseRedirect('/')

	return render_to_response(
		'ledger/forms/Signup.html',
		{
			'form': form,
		},
		context_instance = RequestContext(request),
	)

def sign_out(request):
	now = time.time()
	path = os.path.join(settings.MEDIA_ROOT, 'searches')
	if not os.path.exists(path):
		os.mkdir(path)
	for loop_file in os.listdir(path):
		loop_file_path = os.path.join(path, loop_file)
		if os.stat(loop_file_path).st_mtime < now - 86400:
			if os.path.isfile(loop_file_path):
				#os.remove(loop_file_path)
				pass

	import roadmap.chat.views
	roadmap.chat.views.sign_out(request)
	from django.contrib.auth import logout
	logout(request)
	return HttpResponseRedirect('/')