import datetime
from haystack import indexes
from haystack import site
from roadmap.ledger.models import *


class ItemIndex(indexes.SearchIndex):
	text = indexes.CharField(document = True)
	#subject = indexes.CharField(model_attr = 'subject', use_template = True)
	body = indexes.CharField(model_attr = 'description')

	def prepare(self, obj):
		self.prepared_data = super(ItemIndex, self).prepare(obj)

		prepared_data = []
		prepared_data.append(str(obj.id))
		prepared_data.append(obj.description)
		prepared_data.append(obj.tags)
		#
		# Add comments in
		#
		fetch_comments = Comment.objects.filter(item = obj).order_by('date_time')
		for loop_comments in fetch_comments:
			prepared_data.append(loop_comments.message)
		prepared_data.append(obj.project.name)
		prepared_data.append(obj.project.binder.name)

		self.prepared_data['text'] = '\n'.join(prepared_data)

		return self.prepared_data

	def get_queryset(self):
		"Used when the entire index for model is updated."
		return Item.objects.all()

site.register(Item, ItemIndex)
