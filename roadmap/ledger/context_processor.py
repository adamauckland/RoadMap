# Create your views here.
import os, os.path
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from roadmap.ledger.models import *
import roadmap.ledger.views
from django.contrib.auth.models import User, Group
from django.forms import ModelForm
from django.contrib.auth.decorators import login_required

def user_details(request):
	"""
	Used for the Instant Messenger. Currently in the process of separating this out into a separate binder.
	"""
	if hasattr(request, 'user'):
		chat_status = 0
		chatting_with = 'null'

		output = {}
		try:
			chat_status = request.session['chat_status']
		except:
			chat_status = 0
			pass
		output['chat_status'] = chat_status

		try:
			chatting_with = request.session['chatting_with']
			output['chatting_with_user'] = User.objects.get(id=chatting_with)
		except:
			chatting_with = 0
			output['chatting_with_user'] = request.user
			pass

		output['chatting_with'] = chatting_with
		output['global_user'] = request.user
		fetch_users = User.objects.all()
		fetch_users.exclude(username = '')
		output['global_users'] = fetch_users
		return output
	return {}

def notifications(request):
	"""
	Handles populating the following collections which are on every page:

		* header_notifications
		* replies
		* unseen
		* recently_viewed_items_count
		* follow_up_count

	"""
	result = {}
	try:
		notifications = Notification.objects.filter(user = request.user)
		result['header_notifications'] = notifications
	except:
		pass
	try:
		replies = Item.objects.filter(assigned_to = request.user, replied = True).count()
		result['replies'] = replies
	except Exception, ex:
		pass
	try:
		unseen = Item.objects.filter(assigned_to = request.user, unseen = True).count()
		result['unseen'] = unseen
	except Exception, ex:
		pass

	try:
		item_states_list = roadmap.ledger.views.get_update_items(request)
		result['item_states_list'] = item_states_list
	except Exception, ex:
		pass

	try:
		recently_viewed_items = request.session['recently_viewed_items']
		result['recently_viewed_items_count'] = len(recently_viewed_items)
	except Exception,ex:
		pass

	try:
		follow_up_count = Item.objects.filter(assigned_to = request.user, follow_up = True).count()
		result['follow_up_count'] = follow_up_count
	except Exception, ex:
		pass

	return result

def get_current_path(request):
	"""
	Get the full path of the pre-mapped URL entered in the request.
	"""
	#print(request.get_full_path())
	return {
		'current_path': request.get_full_path()
	}
