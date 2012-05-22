from django.conf.urls.defaults import *
import os

urlpatterns = patterns('roadmap.chat',
	url(r'^chat_home$', 'views.chat_home'),
	url(r'^chat_core$', 'views.chat_core'),
	url(r'^chat_post$', 'views.chat_post'),
	url(r'^set_chat_status$', 'views.set_chat_status'),
	url(r'^set_chatting_with$', 'views.set_chatting_with'),
)
