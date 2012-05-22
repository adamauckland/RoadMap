from django.conf.urls.defaults import *
import os

urlpatterns = patterns('roadmap.ledger',
	(r'^$', 'views.home'),

	url(r'^queries$', 'views.queries'),
	url(r'^new_item/(?P<item_type>\w+)$', 'views.new_item', name='view-new-item'),
	url(r'^create_item_where/(?P<item_type>\w+)$', 'views.create_item_where'),
	url(r'^create_item_where/(?P<item_type>\w+)/(?P<client_name>.+)$', 'views.create_item_where'),
	url(r'^create_item_where/(?P<item_type>\w+)/(?P<client_name>.+)/(?P<binder_name>.+)$', 'views.create_item_where'),
	url(r'^create_item_where/(?P<item_type>\w+)/(?P<client_name>.+)/(?P<binder_name>.+)/(?P<project_name>.+)$', 'views.create_item_where'),

	url(r'^item/(?P<id>\d+)$', 'views.item', name='view-item'),
	url(r'^item/(?P<slug>\w+)$', 'views.item', name='view-item'),
	url(r'^preview/(?P<id>\d+)$', 'views.preview'),

	url(r'^active$', 'views.active', name='view-active'),
	url(r'^tagged_items$', 'views.tagged_items', name='view-active'),
	url(r'^back_next$', 'views.back_next'),
	url(r'^feed_calendar$', 'views.feed_calendar' ),
	url(r'^feed_growl$', 'views.feed_growl' ),
	#url(r'^mini_calendar$', 'views.mini_calendar' ),
	url(r'^set_deadline$', 'views.set_deadline' ),
	url(r'^move$', 'views.move' ),
	url(r'^check_email$', 'views.check_email' ),

	url(r'^activepost$', 'views.active_post' ),

	url(r'^demo$', 'views.demo'),

	#
	# Project and binder pages
	#
	url(r'^binder/(?P<name>.+)$', 'views.view_binder', name='view-binder'),
	url(r'^(?P<client_name>.+)/(?P<binder_name>.+)/(?P<project_name>.+)/breakdown$', 'views.view_project_breakdown'),
	url(r'^(?P<client_name>.+)/(?P<binder_name>.+)/(?P<project_name>.+)/import_csv$', 'views.project_import_csv'),
	url(r'^(?P<client_name>.+)/(?P<binder_name>.+)/(?P<project_name>.+)/project_import_csv_mapping$', 'views.project_import_csv_mapping'),
	url(r'^project/(?P<binder_name>.+)/(?P<name>.+)/(?P<template_section>.+)$', 'views.view_project', name='view-project'),
	url(r'^project/(?P<binder_name>.+)/(?P<name>.+)$', 'views.view_project', name='view-project'),
	url(r'^new_project_filter/(?P<project_id>.+)$', 'views.new_project_filter'),


	url(r'^active/(?P<client_name>.+)/(?P<binder_name>.+)/(?P<project_name>.+)/(?P<location_name>.+)$', 'views.active', name='view-active-list'),
	url(r'^sign-out$', 'views.sign_out' ),
	#
	# Item AJAX
	#
	url(r'^item_details_location$', 'views.item_details_location' ),
	url(r'^item_details_owner$', 'views.item_details_owner' ),
	url(r'^item_details_comment$', 'views.item_details_comment' ),
	url(r'^item_details_project$', 'views.item_details_project' ),
	url(r'^item_details_priority$', 'views.item_details_priority' ),

	url(r'^item_details_mark_completed$', 'views.item_details_mark_completed' ),
	url(r'^item_details_mark_verified$', 'views.item_details_mark_verified' ),
	url(r'^item_details_mark_failed$', 'views.item_details_mark_failed' ),
	url(r'^item_details_mark_reopened$', 'views.item_details_mark_reopened' ),
	url(r'^item_details_mark_identified$', 'views.item_details_mark_identified' ),
	url(r'^item_details_mark_actioned$', 'views.item_details_mark_actioned' ),

	url(r'^item_details_target$', 'views.item_details_target' ),
	url(r'^item_toggle_followup$', 'views.item_toggle_followup' ),
	#
	# Item list callbacks
	#
	url(r'^promote_objective$', 'views.promote_objective'),
	url(r'^select_all_click$', 'views.select_all_click'),
	url(r'^selected_to_group$', 'views.selected_to_group'),
	url(r'^selected_to_remind$', 'views.selected_to_remind'),
	url(r'^selected$', 'views.selected_items'),
	url(r'^get_selected_items_bar$', 'views.get_selected_items_bar'),
	url(r'^save_view_settings$', 'views.save_view_settings'),

	url(r'^my-items$', 'views.my_items'),
	url(r'^recently-viewed-items$', 'views.recently_viewed_items'),
	url(r'^(?P<client_name>.+)/(?P<binder_name>.+)/(?P<project_name>.+)/items$', 'views.items'),
	url(r'^(?P<client_name>.+)/(?P<binder_name>.+)/(?P<project_name>.+)/items/(?P<target_name>.+)$', 'views.items'),

	url(r'^show_hide$', 'views.items_expand_location'),

	url(r'^new_client$', 'views.new_client'),
	url(r'^client/(?P<name>.+)$', 'views.view_client', name='view-client'),

	url(r'^new_project/(?P<id>.+)$', 'views.new_project'),


	url(r'^item_link_item/(?P<item>\w+)/(?P<linked_item>\w+)$', 'views.item_link_item'),
	url(r'^item_link_item$', 'views.item_link_item'),

	url(r'^attach_new_file$', 'views.attach_new_file'),
	url(r'^add_linked_item_popup$', 'views.add_linked_item_popup'),
	url(r'^item_added$', 'views.item_added' ),
	url(r'^no_item$', 'views.no_item'),
	url(r'^test_serialize$', 'views.test_serialize' ),
	url(r'^add_checklist_item$', 'views.add_checklist_item' ),
	url(r'^edit_checklist_item$', 'views.edit_checklist_item' ),
	url(r'^add_checklist_file$', 'views.add_checklist_file' ),
	url(r'^new_binder/(?P<client_id>.+)$', 'views.new_binder' ),
	url(r'^new_target/(?P<project_id>\w+)$', 'views.new_target'),
	url(r'^edit_target/(?P<target_id>\w+)/(?P<project_id>\w+)$', 'views.edit_target'),
	url(r'^user_to_binder$', 'views.user_to_binder' ),
	url(r'^notifications$', 'views.notifications' ),
	url(r'^view_notification/(?P<notification_id>.+)$', 'views.view_notification' ),
	url(r'^owner_to_binder$', 'views.owner_to_binder'),
	url(r'^update_tags$', 'views.update_tags'),
	url(r'^upload_profile$', 'views.upload_profile'),
	url(r'^toggle_item/(?P<item_id>.+)$', 'views.toggle_item'),
	url(r'^download/(?P<filename>.+)$', 'views.download'),
	url(r'^profile/(?P<username>.+)$', 'views.profile'),
	url(r'^change_password$', 'views.change_password'),
	url(r'^ownership/(?P<item_id>\w+)$', 'views.ownership'),
	url(r'^estimates$', 'views.item_details_estimates'),
	url(r'^new_database$', 'views.new_database'),
	url(r'^signup$', 'views.signup'),
	url(r'^select_multiple$', 'views.select_multiple'),
	#
	# Delivery workflow
	#
	url(r'^make_delivery_index$', 'views.make_delivery_index'),
	url(r'^make_delivery_location/(?P<client>.+)/(?P<binder>.+)/(?P<project>.+)$', 'views.make_delivery_location'),
	url(r'^make_delivery_items/(?P<client>.+)/(?P<binder>.+)/(?P<project>.+)/(?P<location>.+)$', 'views.make_delivery_items'),
	url(r'^make_delivery_notes/(?P<client>.+)/(?P<binder>.+)/(?P<project>.+)/(?P<location>.+)$', 'views.make_delivery_notes'),
	url(r'^make_delivery_assign/(?P<client>.+)/(?P<binder>.+)/(?P<project>.+)/(?P<location>.+)$', 'views.make_delivery_assign'),
	url(r'^make_delivery_reassign/(?P<client>.+)/(?P<binder>.+)/(?P<project>.+)/(?P<location>.+)$', 'views.make_delivery_reassign'),
	#
	# Reports
	#
	url(r'^reports$', 'views.reports'),
	url(r'^reports/shell$', 'views.shell'),
)
