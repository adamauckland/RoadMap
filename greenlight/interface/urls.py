from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('greenlight.interface',
	# Examples:
	url(r'^list_suite$', 'views.list_suite'),

	url(r'^start_learning/(?P<suite_id>\d+)$', 'views.start_learning'),
	url(r'^stop_learning/(?P<suite_id>\d+)$', 'views.stop_learning'),
	url(r'^start_suite/(?P<suite_id>\d+)$', 'views.start_suite'),
	url(r'^read_log/(?P<suite_id>\d+)$', 'views.read_log'),

	url(r'^examine_session/(?P<session_id>\d+)$', 'views.examine_session'),

	url(r'^$', 'views.home', name='home'),
	#url(r'^greenlight/', include('greenlight.interface.urls')),

	# Uncomment the admin/doc line below to enable admin documentation:
	# url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

	# Uncomment the next line to enable the admin:
	# url(r'^admin/', include(admin.site.urls)),
)
