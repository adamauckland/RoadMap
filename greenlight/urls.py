from django.conf.urls.defaults import patterns, include, url
import os
SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'greenlight.views.home', name='home'),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': os.path.join(SITE_ROOT, 'media/' ) }),
    url(r'^greenlight/', include('greenlight.interface.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
