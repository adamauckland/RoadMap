import datetime
from django.db import models
from django.contrib.auth.models import User, Group, UserManager
from tagging.fields import TagField
from django.utils.safestring import mark_safe
from django.template.defaultfilters import slugify
from django.db.models import Q
import reversion
import constants

#class RecoveryModel(object):
#	def __getattr__(self, name):
#		if not hasattr(self, name):
#			self.__dict__[name] = self.missing_function
#
#	def missing_function(self):
#		return "Missing function"

class RoadmapUser(User):
	"""
	Helper methods for built in user types
	"""
	objects = UserManager()
	class Meta():
		proxy = True

	def short_name(self):
		return "%s %s" % (self.first_name, self.last_name[:1])

class Priority(models.Model):
	"""
	Priority for triage.

	Attributes:
		| name
		| description
		| order
		| default
	"""
	name = models.CharField(max_length = 50)
	description = models.CharField(max_length = 500)
	order = models.IntegerField(default = 1)
	default = models.BooleanField(default = False)

	def __unicode__(self):
		return self.name

class Type(models.Model):
	"""
	Describes the type of the item.
	"""
	name = models.CharField(max_length = 50)

	def __unicode__(self):
		return self.name

class Client(models.Model):
	"""
	A client.

	Attributes:
		| name
		| slug
		| last_viewed
	"""
	name = models.CharField(max_length = 200)
	slug = models.SlugField()
	last_viewed = models.DateField(null = True, blank = True)

	def __unicode__(self):
		return self.name

	def save(self, *args, **kwargs):
		"""
		Save
		"""
		if not self.id:
			self.slug = slugify(self.name)
		super(Client, self).save(*args, **kwargs)

	def binders(self):
		"""
		Return all binders for the client
		"""
		return Binder.objects.filter(client = self)

if not reversion.is_registered(Client):
	reversion.register(Client)

class Binder(models.Model):
	"""
	A binder.

	The binder is the security model. If a user can only view the items for this binder if they exist in:
		* team
		* reporters
		* producers
		* owner

	This way, a single RoadMap instance can be used for many users. Each one only seeing the binders they are assigned to.

	Attributes:
		| name
		| client
		| owner
		| active
		| team
		| reporters
		| producers
		| logo_url
		| default_project
		| slug
		| tags
	"""
	name = models.CharField(max_length = 500)
	client = models.ForeignKey(Client, blank = True, db_index = True, related_name = 'clients')
	owner = models.ForeignKey(User, related_name = 'binders')
	active = models.BooleanField(default = True)
	team = models.ManyToManyField(User, related_name = 'team')

	reporters = models.ManyToManyField(User, related_name = 'reporters')
	producers = models.ManyToManyField(User, related_name = 'producers')

	logo_url = models.CharField(max_length = 500, blank = True)
	default_project = models.ForeignKey('Project', related_name = 'default_project', null = True)
	slug = models.SlugField()
	tags = TagField()

	def __unicode__(self):
		return self.name

	def save(self, *args, **kwargs):
		if not self.id:
			self.slug = slugify(self.name)
		super(Binder, self).save(*args, **kwargs)

	def projects(self):
		"""
		Return a list of all projects contained in this binder.
		"""
		return Project.objects.filter(binder = self)

	def all_users(self):
		"""
		Return all unique users who have access to read/write this binder as a sorted set
		"""
		all_users_set = set()
		for loop_user in self.producers.all():
			all_users_set.add(loop_user)
		for loop_user in self.reporters.all():
			all_users_set.add(loop_user)
		all_users_set.add(self.owner)
		return sorted(all_users_set)

if not reversion.is_registered(Binder):
	reversion.register(Binder)

class ProjectItemFilter(models.Model):
	"""
	Search items
	"""
	name = models.CharField(max_length = 250)
	search_id = models.CharField(max_length = 250)
	user = models.ForeignKey(User)
	default = models.BooleanField(default = False)

class Project(models.Model):
	"""
	A project to group items by.

	Attributes
		| name
		| deadline
		| binder
		| slug
		| last_viewed
	"""
	name = models.CharField(max_length = 250)
	deadline = models.DateField(null = True, blank = True)
	binder = models.ForeignKey(Binder, db_index = True)
	slug = models.SlugField()
	last_viewed = models.DateField(null = True, blank = True)
	project_filters = models.ManyToManyField(ProjectItemFilter)

	def __unicode__(self):
		return self.name

	def save(self, *args, **kwargs):
		if not self.id:
			self.slug = slugify(self.name)

		super(Project, self).save(*args, **kwargs)

	def feed_message(self, author, description, item):
		"""
		Add a message into the feed for this project.

		Required parameters:
			| author: who wrote it
			| description: the text to display
			| item: reference back to the item

		This feature needs splitting into a separate binder
		"""
		for loop_user in self.binder.team.all():
			feed = Feed()
			feed.description = description
			feed.date_time = datetime.datetime.now()
			feed.user = loop_user
			feed.item = item
			feed.author = author
			feed.save()

	def client_name(self):
		return self.binder.client.name

if not reversion.is_registered(Project):
	reversion.register(Project)

class Location(models.Model):
	"""
	Where the item is logically.

	Attributes:
		| name
		| description
		| method
	"""
	name = models.CharField(max_length = 50, default = '')
	description = models.CharField(max_length = 500)
	#groups = models.ManyToManyField(Group, blank = True)
	method = models.CharField(max_length = 10)
	project = models.ForeignKey(Project)
	order = models.IntegerField(null = False, blank = False, default = 0)
	users = models.ManyToManyField(User)

	def __unicode__(self):
		return self.description

class Target(models.Model):
	"""
	A date for users to use to prioritise things.

	Items can be added to a target.

	Targets can be either private or public

	Attributes:
		| name
		| deadline
		| public
		| user
		| slug
		| project
		| active
	"""
	public_choices = (
		(0, 'Private'),
		(1, 'Public'),
	)
	name = models.CharField(max_length = 2000)
	deadline = models.DateField(null = False, blank = False)
	public = models.IntegerField(default = 0, choices = public_choices)
	user = models.ForeignKey(User)
	slug = models.SlugField()
	project = models.ForeignKey(Project, null = True, blank = False, db_index = True)
	active = models.BooleanField(default = True)

	def save(self, *args, **kwargs):
		if not self.id:
			self.slug = slugify(self.name)

		super(Target, self).save(*args, **kwargs)

	def get_overdue(self):
		"""
		Return True if the deadline has passed
		"""
		if self.deadline < datetime.date.today():
			return True
		else:
			return False
	overdue = property(get_overdue)

if not reversion.is_registered(Target):
	reversion.register(Target)

class ItemManager(models.Manager):
	"""
	Helper class to return only non-deleted items
	"""
	def get_query_set(self):
		return super(ItemManager, self).get_query_set().exclude(
			Q(location__method = constants.LOCATION_DELETED) | Q(state = 1)
		)

class ItemState(models.Model):
	"""
	Identified, Actioned, Completed and Verified
	"""
	description = models.CharField(max_length = 100)
	constant = models.CharField(max_length = 200)

class Item(models.Model):
	"""
	A trackable item in the db. Might be an issue or change_request or document

	state:
		1 - new
		0 - saved
	"""
	description = models.CharField(max_length = 2000)
	item_type = models.ForeignKey(Type)
	location = models.ForeignKey(Location, db_index = True)
	project = models.ForeignKey(Project, db_index = True)
	priority = models.ForeignKey(Priority, default = 2)
	assigned_to = models.ForeignKey(User)
	state = models.IntegerField(default = 0)
	fixed = models.BooleanField(default = False)
	validated = models.BooleanField(default = False)
	tags = TagField()
	date_time = models.DateTimeField(default = datetime.datetime.now())
	#
	# New state field
	#
	item_state = models.ForeignKey(ItemState, null = True, blank = True)

	hours_estimated = models.DecimalField(max_digits = 5, decimal_places = 1, default = 0)
	hours_total = models.DecimalField(max_digits = 5, decimal_places = 1, default = 0)

	targets = models.ManyToManyField(Target)

	follow_up = models.BooleanField(default = False)
	unseen = models.BooleanField(default = False)
	replied = models.BooleanField(default = False)

	associated_items = models.ManyToManyField('Item')
	item_group = models.CharField(max_length = 1000, null = True, blank = True)

	reminder = models.DateTimeField(null = True, blank = True)
	#
	# Implement table level functionality
	#
	objects = models.Manager()
	active_objects = ItemManager()

	def __unicode__(self):
		return self.description

	def get_linked_item(self):
		type_map = {
			'Issue' : Issue,
			'Note' : Note,
			'Requirement' : Requirement,
			'Email' : Email,
			'File' : File,
		}
		dynamic_type = type_map[self.item_type.name]
		linked_item = dynamic_type.objects.get(item = self)
		return linked_item
	linked_item = property(get_linked_item)

	def add_comment(self, user, message, date_time = datetime.datetime.now()):
		"""
		Add a comment from <user> to <item>. Message test is <message>.
		"""
		comment = Comment()
		comment.user = user
		comment.item = self
		comment.message = message
		comment.date_time = date_time
		comment.save()

	def get_comments(self):
		"""
		Return all the comments for this item
		"""
		return Comment.objects.filter(item = self).order_by('date_time')
	comments = property(get_comments)

	def latest_comment(self):
		"""
		Return the latest comments for this item in an ordered list
		"""
		comments = Comment.objects.filter(item = self).order_by('-date_time')
		try:
			return comments[0]
		except:
			return None

	def assigned_to_short_version(self):
		return "%s %s" % (self.assigned_to.first_name, self.assigned_to.last_name[:1])

if not reversion.is_registered(Item):
	reversion.register(Item)

class Trophy(models.Model):
	description = models.CharField(max_length = 2000)

class FeedAction(models.Model):
	name = models.CharField(max_length = 100)
	template = models.CharField(max_length = 2000)

class Feed(models.Model):
	"""
	Feed for news.

	description: an html or possibly Markdown formatted string to show on the frontend.
	This would be in the format:

		JAMES created a MILESTONE

	where the uppercase are links which lead you to a filtered page. Possibly by using tags.

	date_time: when it happened for ordering.
	user: who to send message to.
	author: user who created it.
	group: group to send message to.

	"""
	description = models.CharField(max_length = 4000)
	date_time = models.DateTimeField(default = datetime.datetime.now())
	user = models.ForeignKey(User)
	author = models.ForeignKey(User, related_name = 'author', null = True)
	group = models.ManyToManyField(Group)
	item = models.ForeignKey(Item, null = True, blank = True)
	action = models.ForeignKey(FeedAction, null = True, blank = True)

	def __unicode__(self):
		return self.description

class Note(models.Model):
	"""
	Useful text for the binder.
	"""
	item = models.ForeignKey(Item)
	text = models.TextField()
if not reversion.is_registered(Note):
	reversion.register(Note)

class File(models.Model):
	"""
	Stores a file such as a spec or an image.

	Ideally versioned with audit history.

	Attributes:
		| item
		| file
		| filetype
		| name
	"""
	item = models.ForeignKey(Item)
	file = models.CharField(max_length = 255)
	filetype = models.CharField(max_length = 255)
	name = models.TextField()

	def icon(self):
		"""
		Return the icon for this filetype (i.e. Word doc icon or PDF icon)

		Returns: full URL
		"""
		return_icon = self.filetype.replace('.', '')
		if return_icon == '':
			return 'File.png'
		else:
			return 'filetypes/%s.ico' % return_icon

if not reversion.is_registered(File):
	reversion.register(File)

class Email(models.Model):
	"""
	An email read by RoadMap from the email POP mailbox assigned to it.

	Once read, the POP mailbox message will be deleted.

	Attributes:
		| item
		| file_id
		| message_id
		| in_reply_to
		| references
		| date_time
	"""
	item = models.ForeignKey(Item, db_index = True)
	file_id = models.IntegerField()
	message_id = models.CharField(max_length = 2000)
	in_reply_to = models.CharField(max_length = 2000)
	references = models.CharField(max_length = 4000)
	date_time = models.DateField(null = True, blank = True)

if not reversion.is_registered(Email):
	reversion.register(Email)

class ChecklistItem(models.Model):
	"""
	Checklist Item.

	Attributes:
		| item
		| order_index
		| text
		| filename
	"""
	item = models.ForeignKey(Item, db_index = True)
	order_index = models.IntegerField()
	text = models.CharField(max_length = 2000)
	filename = models.CharField(max_length = 2000)

if not reversion.is_registered(ChecklistItem):
	reversion.register(ChecklistItem)

class Issue(models.Model):
	"""
	A fault.

	Attributes:
		| item
		| replicate_steps
		| url
		| description
		| associated_media
		| delivery_notes
	"""
	item = models.ForeignKey(Item, related_name = 'issue', db_index = True)
	replicate_steps = models.TextField()
	url = models.CharField(max_length = 4000)
	description = models.TextField()
	associated_media = models.ManyToManyField(File)
	delivery_notes = models.TextField()

if not reversion.is_registered(Issue):
	reversion.register(Issue)

class Requirement(models.Model):
	"""
	A simple requirement.

	Attributes:
		| item
		| text
		| delivery_nodes
	"""
	item = models.ForeignKey(Item, db_index = True)
	text = models.TextField()
	delivery_notes = models.TextField()

if not reversion.is_registered(Requirement):
	reversion.register(Requirement)

class Comment(models.Model):
	"""
	A block of text a user has added to an item.
	"""
	item = models.ForeignKey(Item, db_index = True)
	user = models.ForeignKey(User)
	date_time = models.DateTimeField(default = datetime.datetime.now())
	message = models.TextField()

	def message_safe(self):
		return mark_safe(self.message)

if not reversion.is_registered(Comment):
	reversion.register(Comment)

class UserProfile(models.Model):
	"""
	Used to extend the user model
	"""
	gravatar_url = models.URLField()
	user = models.ForeignKey(User, unique=True)

class Notification(models.Model):
	"""
	Notification for an item (unused)
	"""
	user = models.ForeignKey(User)
	text = models.TextField()
	item = models.ForeignKey(Item)

class DailyBasic(models.Model):
	day = models.DateField(auto_now_add=True)
	quantity = models.IntegerField()
	location = models.ForeignKey(Location)
	project = models.ForeignKey(Project)

class Assigned(models.Model):
	"""
	Tracks who was assigned to this item.
	"""
	date_time = models.DateTimeField(default = datetime.datetime.now())
	item = models.ForeignKey(Item)
	location = models.ForeignKey(Location)
	user = models.ForeignKey(User)
	comments = models.CharField(max_length = 100)

class Contact(models.Model):
	"""
	A person's contact details.
	"""
	name = models.CharField(max_length = 200)
	job_title = models.CharField(max_length = 200)
	email = models.CharField(max_length = 200)
	telephone = models.CharField(max_length = 100)
	notes = models.CharField(max_length = 2000)

class LocationExpander():
	def __init__(self):
		self.location_expanded = {}
		for loop_location in Location.objects.all():
			self.location_expanded[loop_location] = True

class ProjectSettingGroup(models.Model):
	"""
	Used to group project settings
	"""
	name = models.CharField(max_length = 200)
	user_setting = models.BooleanField(default = False)
	def __unicode__(self):
		return self.name

class ProjectSetting(models.Model):
	"""
	ProjectSetting is a setting for the project page or child page.
	This will control the default view the user is presented with, and what they
	see on the project page.

	These are the options available which get linked together by the ProjectUserSetting table
	"""
	name = models.CharField(max_length = 200)
	const = models.CharField(max_length = 100)
	group = models.ForeignKey(ProjectSettingGroup, null = True, blank = True)
	def __unicode__(self):
		return self.name

class SystemProjectSetting(models.Model):
	"""
	Store settings for the project for all users
	"""
	project = models.ForeignKey(Project, null = True)
	project_setting = models.ForeignKey(ProjectSetting)
	value = models.TextField()
	def project_setting_name(self):
		return self.project_setting.name
	def project_setting_const(self):
		return self.project_setting.const

class UserProjectSetting(models.Model):
	"""
	Store the settings for each user, for each project setting.
	"""
	project = models.ForeignKey(Project, null = True)
	user = models.ForeignKey(User)
	project_setting = models.ForeignKey(ProjectSetting)
	value = models.TextField()


# Register the Item object with the tagging application. For reference see http://api.rst2a.com/1.0/rst2/html?uri=http://django-tagging.googlecode.com/svn/trunk/docs/overview.txt
import tagging
#tagging.register(Item)