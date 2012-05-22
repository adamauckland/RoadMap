from django.conf.urls.defaults import *
import os
SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
	(r'^media/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': os.path.join(SITE_ROOT, 'media' ) }),
	(r'^comments/', include('django.contrib.comments.urls')),
	(r'^roadmap/ledger/', include('roadmap.ledger.urls')),
	(r'^roadmap/chat/', include('roadmap.chat.urls')),
	(r'^accounts/login/$', 'django.contrib.auth.views.login'),
	(r'^admin/', include(admin.site.urls)),
	(r'^tinymce/', include('tinymce.urls')),
	(r'^avatar/', include('avatar.urls')),
	(r'^search/', include('haystack.urls')),
	(r'', include('roadmap.ledger.urls')),
)
