import urllib, hashlib
import django.template
from django.template import Library

register = Library()

@register.filter()
def contains(value, arg):
	"""
	Usage:
	{% if text|contains:"http://" %}
	This is a link.
	{% else %}
	Not a link.
	{% endif %}
	"""
	return arg in value

@register.filter()
def removedots(value):
	return value.replace('.', '')

@register.filter()
def make_key(value):
	return 'k%s' % value

@register.filter()
def user_tags(value):
	tags = value.split(' ')
	new_tags = []
	for loop_item in tags:
		if loop_item[:1] == '#':
			new_tags.append(loop_item)
	return ' '.join(new_tags)

@register.inclusion_tag('ledger/templatetags/gravatar.html')
def show_gravatar(email, size = 48):
	default = "/media/layout/icons/user_gray.png"

	url = "http://www.gravatar.com/avatar.php?"
	url += urllib.urlencode({
		'gravatar_id': hashlib.md5(email).hexdigest(),
		'default': '',
		'size': str(size)
	})
	#print(url)

	return {'gravatar': {'url': url, 'size': size}}

class ActiveItems(object):
	def __init__(self):
		self.must_be_first = False

	def get_nodes_by_type(self, thingy):
		pass

	def render(self, context):
		request = context['request']
		#print('IN ACTIVE ITEMS')
		active_items = []
		#if request.user:
		for loop_binder in Binder.objects.filter(active = True):
			for loop_project in Project.objects.filter(binder = loop_binder):
				default_location = None
				if request.user in loop_binder.reporters.all():
					default_location = Location.objects.get(name = 'Testing')
				if request.user in loop_binder.producers.all():
					default_location = Location.objects.get(name = 'Production')
				if request.user == loop_binder.owner:
					default_location = Location.objects.get(name = 'Reported')

				if default_location:
					data = {}
					data['project'] = loop_project.slug
					data['binder'] = loop_binder.slug
					data['location'] = default_location
					data['name'] = '%s' % (loop_project.name,)
					active_items.append(data)
		items_template = template.loader.get_template('ledger/templatetags/active_items.html')
		return items_template.render(
			Context(
				{
					'active_items': active_items
				},
				autoescape=context.autoescape
			)
		)

class OverrideQuerystring(django.template.Node):
	def __init__(self, overriders):
		self.must_be_first = False
		self.overriders = overriders

	def render(self, context):
		request = context['request']
		items = {}

		if request.GET != None:
			for loop_key, loop_value in request.GET.items():
				items[loop_key] = loop_value

		for loop_overriders in self.overriders:
			split_string = loop_overriders.split('=')
			if len(split_string) == 2:
				override_key = split_string[0].strip()
				override_value = split_string[1].strip()
				if override_value.startswith('"') and override_value.endswith('"'):
					override_value = override_value[1:-1]
				else:
					try:
						variable = django.template.Variable(override_value)
						override_value = variable.resolve(context)
					except django.template.VariableDoesNotExist, ex:
						pass
					except Exception, ex:
						pass
				items[override_key] = override_value

		items_template = django.template.loader.get_template('ledger/templatetags/override_urls.html')
		return items_template.render(
			django.template.Context(
				{
					'items': items
				},
				autoescape=context.autoescape
			)
		)

	#def get_nodes_by_type(self, thingy):
	#	#print('Override URL get_nodes_by_type')
	#	#print(thingy)
	#	return []

def override_querystring(parser, token):
	split_contents = token.split_contents()
	return OverrideQuerystring(split_contents)

def active_items(parser, token):
	return ActiveItems()

register.tag('active_items', active_items)
register.tag('override_querystring', override_querystring)