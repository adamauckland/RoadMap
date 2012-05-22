from roadmap.ledger.models import *
from django.contrib import admin
import roadmap.ledger.mercurial
from django.conf.urls.defaults import patterns
from django.shortcuts import get_object_or_404, render_to_response
from django.template import loader, RequestContext

class ProjectAdmin(admin.ModelAdmin):
	list_display = ('name', 'binder', 'client_name', 'slug')
	list_filter = ('binder__client', )
	search_fields = ('name', 'binder__name', 'binder__client__name' )


	def get_urls(self):
		urls = super(ProjectAdmin, self).get_urls()
		my_urls = patterns('',
			(r'^commit_log/$',  self.admin_site.admin_view(self.commit_log))
		)
		return my_urls + urls


	def create_system_settings(modeladmin, request, queryset):
		all_settings = ProjectSetting.objects.filter(group__user_setting = False)
		for loop_project in queryset:
			for loop_setting in all_settings:
				try:
					check_for_setting = SystemProjectSetting.objects.get(
						project = loop_project,
						project_setting = loop_setting
					)
				except SystemProjectSetting.DoesNotExist:
					new_setting = SystemProjectSetting()
					new_setting.project = loop_project
					new_setting.project_setting = loop_setting
					new_setting.value = ''
					new_setting.save()


	def commit_log(modeladmin, request, queryset):
		opts = modeladmin.model._meta
		admin_site = modeladmin.admin_site

		for loop_project in queryset:
			connection_string = SystemProjectSetting.objects.get(
				project=loop_project,
				project_setting = ProjectSetting.objects.get(const='MERCURIAL_CONNECTION_STRING')
			).value
			repository_path = SystemProjectSetting.objects.get(
				project=loop_project,
				project_setting = ProjectSetting.objects.get(const='MERCURIAL_REPOSITORY_PATH')
			).value
			password = SystemProjectSetting.objects.get(
				project=loop_project,
				project_setting = ProjectSetting.objects.get(const='MERCURIAL_REPOSITORY_PASSWORD')
			).value

		reader = roadmap.ledger.mercurial.MercurialReader(connection_string, password, repository_path)
		logs = reader.get_logs(revision_from = '1', revision_to = 'tip')
		return render_to_response(
			'ledger/project_commit_log.html',
			{
				'admin_site': admin_site.name,
				'title': 'Commit Log',
				'opts': opts,
				'logs': logs,
				'root_path': '/%s' % admin_site.root_path,
				'app_label': opts.app_label,
			},
			RequestContext(request, {}),
		)


	def info_log(modeladmin, request, queryset):
		opts = modeladmin.model._meta
		admin_site = modeladmin.admin_site

		for loop_project in queryset:
			connection_string = SystemProjectSetting.objects.get(
				project=loop_project,
				project_setting = ProjectSetting.objects.get(const='MERCURIAL_CONNECTION_STRING')
			).value
			repository_path = SystemProjectSetting.objects.get(
				project=loop_project,
				project_setting = ProjectSetting.objects.get(const='MERCURIAL_REPOSITORY_PATH')
			).value
			password = SystemProjectSetting.objects.get(
				project=loop_project,
				project_setting = ProjectSetting.objects.get(const='MERCURIAL_REPOSITORY_PASSWORD')
			).value

		reader = roadmap.ledger.mercurial.MercurialReader(connection_string, password, repository_path)
		old_logs = reader.get_logs(revision_from = '1', revision_to = 'tip')
		logs = [log for log in old_logs if log.summary.lower().find('*') != -1]

		return render_to_response(
			'ledger/project_commit_log.html',
			{
				'admin_site': admin_site.name,
				'title': "Information Log",
				'opts': opts,
				'logs': logs,
				'root_path': '/%s' % admin_site.root_path,
				'app_label': opts.app_label,
			},
			RequestContext(request, {}),
		)
	actions = [commit_log, info_log, create_system_settings]


class ProjectSettingAdmin(admin.ModelAdmin):
	list_display = ('name', 'const', 'group' )


class SystemProjectSettingAdmin(admin.ModelAdmin):
	list_display = ('project', 'project_setting_name', 'project_setting_const', 'value' )
	list_filter = ('project', 'project_setting')
	search_fields = ('value', )


admin.site.register(Feed)
admin.site.register(Type)
admin.site.register(Location)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Client)
admin.site.register(Binder)
admin.site.register(Priority)
admin.site.register(File)
admin.site.register(Note)
admin.site.register(Issue)
admin.site.register(Item)
admin.site.register(ProjectSettingGroup)
admin.site.register(ProjectSetting, ProjectSettingAdmin)
admin.site.register(SystemProjectSetting, SystemProjectSettingAdmin)
admin.site.register(UserProjectSetting)
