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
import urllib2
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
from django.core.paginator import Paginator
from django.db import connection, transaction
from django.db.models import Sum, Count
from django.db.models import Q
from django.forms import ModelForm, Form
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import loader, RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import escape
from django.db import connection
from django.forms.extras.widgets import SelectDateWidget
from django.template.defaultfilters import slugify
from django.views.decorators.cache import never_cache

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
	delivery_notes = forms.CharField(label = 'Delivery Tasks', widget = forms.widgets.Textarea(), required = False)

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
		linked_item.url = linked_item_form.cleaned_data['url']
		item.description = linked_item_form.cleaned_data['subject']
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

		item.save()
		linked_item.save()

		#
		# Check for comments and add
		#
		comment_text = linked_item_form.cleaned_data['comments'].strip()
		if comment_text != '':
			post_comment(request, item, comment_text)

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
	deadline = forms.DateField(widget=SelectDateWidget(), initial = datetime.date.today() + datetime.timedelta(1) )

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
	delivery_notes = forms.CharField(label = 'Delivery Tasks', widget = forms.widgets.Textarea(), required = False)

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

class EmailForm(ModelForm):
	class Meta:
		model = Email

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