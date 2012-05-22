from django.db.models import get_model
from django.template import Library, Node, TemplateSyntaxError, Variable, resolve_variable
from django.utils.translation import ugettext as _
from roadmap.ledger.models import *
import calendar
from datetime import datetime


register = Library()

class calendar_data(object):
	def __init__(self):
		self.month_name = ''
		self.weeks = []

class day_data(object):
	def __init__(self, value):
		self.ccs_class = ''
		self.value = value
	
class mini_calendar(object):
	def __init__(self):
		pass

	def render(self, context):
		request = context['request']
		
		todays_date = datetime.date(datetime.now())
		todays_month = todays_date.month
		todays_year = todays_date.year
		todays_day = todays_date.day
		actual_month = todays_month
		actual_year = todays_year
		
		# adjust the date for querystring overrides
		try:
			if request.GET.has_key('month') != '':
				todays_month = int(request.GET['month'])
		except:
			pass
		
		try:
			if request.GET.has_key('year'):
				todays_year = int(request.GET['year'])
		except:
			pass
		
		previous_month = todays_month - 1
		previous_year = todays_year
		if previous_month == 0:
			previous_month = 12
			previous_year = todays_year - 1
		
		next_month = todays_month + 1
		next_year = todays_year
		if next_month == 13:
			next_month = 1
			next_year = next_year + 1
		
		months = [
			'January',
			'February',
			'March',
			'April',
			'May',
			'June',
			'July',
			'August',
			'September',
			'October',
			'November',
			'December'
		]
		calendar_item = calendar_data()
		calendar_item.todays_year = todays_year
		calendar_item.todays_month = todays_month
		calendar_item.previous_month = previous_month
		calendar_item.previous_year = previous_year
		calendar_item.next_month = next_month
		calendar_item.next_year = next_year
		calendar_item.past_year = todays_year - 1
		calendar_item.future_year = todays_year + 1
		
		month_post_list = Item.objects.filter(
			date_time__gte = datetime(todays_year, todays_month, 1)
		).exclude(
			date_time__gte = datetime(next_year, next_month, 1)
		)
		
		calendar_item.month_name = months[todays_month - 1]
		for week in calendar.monthcalendar(todays_year, todays_month):
			week_data = []
			for day in week:
				day_item = day_data(day)
				if day == todays_day and todays_month == actual_month and todays_year == actual_year:
					day_item.ccs_class = 'today '
				week_data.append(day_item)
			calendar_item.weeks.append(week_data)
		
		for loop_item in month_post_list:
			for loop_week in calendar_item.weeks:
				for loop_day in loop_week:
					if loop_day.value == loop_item.date_time.day: 
						loop_day.ccs_class += ' events '
						loop_day.slug = loop_item.name

		context['calendar_output'] = calendar_item

def do_mini_calendar(parser, token):
	return mini_calendar()
	
register.tag('mini_calendar', do_mini_calendar)