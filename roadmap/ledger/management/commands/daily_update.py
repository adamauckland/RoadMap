from django.core.management.base import BaseCommand, CommandError
from roadmap.ledger.models import *
from django.db.models import Q
import datetime

class Command(BaseCommand):

	def handle(self, *args, **options):
		reminder_items = Item.objects.filter(reminder__lte = datetime.datetime.now())
		for loop_item in reminder_items:
			loop_item.reminder = None
			loop_item.unseen = True
			loop_item.save()

		for loop_binder in Binder.objects.filter(active = True):
			for loop_project in Project.objects.filter(binder = loop_binder):
				for location in Location.objects.exclude(name = 'Delivered'):
					search = {}
					search['project'] = loop_project
					search['location'] = location
					search['state'] = 0
					if location.name == 'Testing':
						search['fixed'] = True
						search['validated'] = False

					todays_items = Item.objects.filter(Q(**search))

					daily_basic = DailyBasic()
					daily_basic.quantity = len(todays_items)
					daily_basic.project = loop_project
					daily_basic.location = location
					daily_basic.save()

					#
					# hack to save completed as well as tested
					#
					if location.name == 'Testing':
						search['validated'] = True
						todays_items = Item.objects.filter(Q(**search))
						daily_basic = DailyBasic()
						daily_basic.quantity = len(todays_items)
						daily_basic.project = loop_project
						daily_basic.location = Location.objects.get(name = 'Delivered')
						daily_basic.save()