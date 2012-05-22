import calendar
import datetime
import hashlib
import os, os.path
import pickle
from poplib import *
import settings
import shutil
import urllib
import uuid

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core import serializers
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms import ModelForm, Form
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

class MessageUser(list):
	def __init__(self):
		pass

class Message(object):
	def __init__(self):
		self.message = ''
		self.user = None
		self.date_time = datetime.datetime.now()

class Messages(dict):
	def __init__(self):
		pass

def sign_out(request):
	user_filename = os.path.join(settings.CHAT_ROOT, str(request.user.id))
	try:
		if os.path.exists(user_filename):
			os.remove(user_filename)
	except:
		pass

def start(user_filename):
	if not os.path.exists(settings.CHAT_ROOT):
		os.mkdir(settings.CHAT_ROOT)
		
	if not os.path.exists(user_filename):
		messages = Messages()
		file_output = file(user_filename, 'wb')
		pickle.dump(messages, file_output)
		file_output.close()

@login_required
def chat_core(request):
	user_filename = os.path.join(settings.CHAT_ROOT, str(request.user.id))
	start(user_filename)
	file_input = file(user_filename, 'rb')
	messages = pickle.load(file_input)
	file_input.close()
	
	chatting_with = request.GET.get('user_id')
	chat_with_user = User.objects.get(id = chatting_with)
	if chat_with_user in messages.keys():
		actual_messages = messages[chat_with_user]
	else:
		actual_messages = []
	
	return render_to_response(
		'chat/core.html',
		{
			'chat_user' : chat_with_user,
			'chat_messages': actual_messages,
		},
		context_instance = RequestContext(request),
	)

def chat_post(request):
	user_to_id = request.POST.get('user_to')
	user_to = User.objects.get(id = user_to_id)
	
	#
	# open my file first
	#
	user_filename = os.path.join(settings.CHAT_ROOT, str(request.user.id))
	print('opening %s' % user_filename)
	start(user_filename)
	
	print('reading file')
	file_input = file(user_filename, 'rb')
	messages = pickle.load(file_input)
	file_input.close()
	print('read messages')
	#
	# open their key in my file
	#
	if not user_to in messages.keys():
		message_user = MessageUser()
		messages[user_to] = message_user
	print('made sure the user is there')
	
	#
	# add a message in their key in my file
	#
	message = Message()
	message.message = request.POST.get('message')
	message.user = request.user
	print('adding')
	print(messages[user_to])
	try:
		messages[user_to].append(message)
	except Exception,ex:
		print(ex)
	print('aded message in my file')

	file_output = file(user_filename, 'wb')
	pickle.dump(messages, file_output)
	file_output.close()

	#
	# Now post in the targets
	# 
	target_user_filename = os.path.join(settings.CHAT_ROOT, str(user_to_id))
	start(target_user_filename)
		
	target_user = file(target_user_filename, 'rb')
	target_messages = pickle.load(target_user)
	#
	# write into our key in targets file
	# 
	if not request.user in target_messages.keys():
		message_from_user = MessageUser()
		target_messages[request.user] = message_from_user
	#
	# write a message into our key in their file
	#
	print('writing message to other user')
	target_message = Message()
	target_message.message = request.POST.get('message')
	target_message.user = request.user
	target_messages[request.user].append(target_message)

	print('target saved')
	
	file_output = file(target_user_filename, 'wb')
	pickle.dump(target_messages, file_output)
	file_output.close()
	print('ending')
	
	return HttpResponse(
		'success',
		mimetype='text/plain',
	)

@login_required
def chat_home(request):
	user_filename = os.path.join(settings.CHAT_ROOT, str(request.user.id))
	start(user_filename)
	
	file_input = file(user_filename, 'rb')
	messages = pickle.load(file_input)
	file_input.close()
	
#	file_output = file(user_filename, 'wb')
#	pickle.dump(messages, file_output)
#	file_output.close()
	
	return render_to_response(
		'chat/home.html',
		{
			'users' : User.objects.all(),
			'messages': messages,
		},
		context_instance = RequestContext(request),
	)

def set_chat_status(request):
	chat_status = request.GET.get('chat_status')
	request.session['chat_status'] = chat_status
	return HttpResponse(
		chat_status,
		mimetype='text/plain',
	)

def set_chatting_with(request):
	chatting_with = request.GET.get('chatting_with')
	request.session['chatting_with'] = chatting_with
	return HttpResponse(
		chatting_with,
		mimetype='text/plain',
	)