# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ItemState'
        db.create_table('ledger_itemstate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('constant', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('ledger', ['ItemState'])

        # Adding field 'Item.item_state'
        db.add_column('ledger_item', 'item_state', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ledger.ItemState'], null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting model 'ItemState'
        db.delete_table('ledger_itemstate')

        # Deleting field 'Item.item_state'
        db.delete_column('ledger_item', 'item_state_id')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'ledger.assigned': {
            'Meta': {'object_name': 'Assigned'},
            'comments': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'date_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 4, 29, 16, 24, 51, 377649)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Item']"}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Location']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'ledger.binder': {
            'Meta': {'object_name': 'Binder'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'clients'", 'blank': 'True', 'to': "orm['ledger.Client']"}),
            'default_project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'default_project'", 'null': 'True', 'to': "orm['ledger.Project']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo_url': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'binders'", 'to': "orm['auth.User']"}),
            'producers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'producers'", 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'reporters': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'reporters'", 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'tags': ('tagging.fields.TagField', [], {}),
            'team': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'team'", 'symmetrical': 'False', 'to': "orm['auth.User']"})
        },
        'ledger.checklistitem': {
            'Meta': {'object_name': 'ChecklistItem'},
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Item']"}),
            'order_index': ('django.db.models.fields.IntegerField', [], {}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '2000'})
        },
        'ledger.client': {
            'Meta': {'object_name': 'Client'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_viewed': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'ledger.comment': {
            'Meta': {'object_name': 'Comment'},
            'date_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 4, 29, 16, 24, 51, 375197)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Item']"}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'ledger.contact': {
            'Meta': {'object_name': 'Contact'},
            'email': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'telephone': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'ledger.dailybasic': {
            'Meta': {'object_name': 'DailyBasic'},
            'day': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Location']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Project']"}),
            'quantity': ('django.db.models.fields.IntegerField', [], {})
        },
        'ledger.email': {
            'Meta': {'object_name': 'Email'},
            'date_time': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'file_id': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_reply_to': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Item']"}),
            'message_id': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'references': ('django.db.models.fields.CharField', [], {'max_length': '4000'})
        },
        'ledger.feed': {
            'Meta': {'object_name': 'Feed'},
            'action': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.FeedAction']", 'null': 'True', 'blank': 'True'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'author'", 'null': 'True', 'to': "orm['auth.User']"}),
            'date_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 4, 29, 16, 24, 51, 368150)'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '4000'}),
            'group': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Item']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'ledger.feedaction': {
            'Meta': {'object_name': 'FeedAction'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '2000'})
        },
        'ledger.file': {
            'Meta': {'object_name': 'File'},
            'file': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'filetype': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Item']"}),
            'name': ('django.db.models.fields.TextField', [], {})
        },
        'ledger.issue': {
            'Meta': {'object_name': 'Issue'},
            'associated_media': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['ledger.File']", 'symmetrical': 'False'}),
            'delivery_notes': ('django.db.models.fields.TextField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issue'", 'to': "orm['ledger.Item']"}),
            'replicate_steps': ('django.db.models.fields.TextField', [], {}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '4000'})
        },
        'ledger.item': {
            'Meta': {'object_name': 'Item'},
            'assigned_to': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'associated_items': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['ledger.Item']", 'symmetrical': 'False'}),
            'date_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 4, 29, 16, 24, 51, 364034)'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'fixed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'follow_up': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hours_estimated': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '5', 'decimal_places': '1'}),
            'hours_total': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '5', 'decimal_places': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_group': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'item_state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.ItemState']", 'null': 'True', 'blank': 'True'}),
            'item_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Type']"}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Location']"}),
            'priority': ('django.db.models.fields.related.ForeignKey', [], {'default': '2', 'to': "orm['ledger.Priority']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Project']"}),
            'reminder': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'replied': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'tags': ('tagging.fields.TagField', [], {}),
            'targets': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['ledger.Target']", 'symmetrical': 'False'}),
            'unseen': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'validated': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'ledger.itemstate': {
            'Meta': {'object_name': 'ItemState'},
            'constant': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'ledger.location': {
            'Meta': {'object_name': 'Location'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Project']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False'})
        },
        'ledger.note': {
            'Meta': {'object_name': 'Note'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Item']"}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'ledger.notification': {
            'Meta': {'object_name': 'Notification'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Item']"}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'ledger.priority': {
            'Meta': {'object_name': 'Priority'},
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'ledger.project': {
            'Meta': {'object_name': 'Project'},
            'binder': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Binder']"}),
            'deadline': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_viewed': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'ledger.projectsetting': {
            'Meta': {'object_name': 'ProjectSetting'},
            'const': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.ProjectSettingGroup']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'ledger.projectsettinggroup': {
            'Meta': {'object_name': 'ProjectSettingGroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'user_setting': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'ledger.requirement': {
            'Meta': {'object_name': 'Requirement'},
            'delivery_notes': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Item']"}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'ledger.systemprojectsetting': {
            'Meta': {'object_name': 'SystemProjectSetting'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Project']", 'null': 'True'}),
            'project_setting': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.ProjectSetting']"}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'ledger.target': {
            'Meta': {'object_name': 'Target'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'deadline': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Project']", 'null': 'True'}),
            'public': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'ledger.trophy': {
            'Meta': {'object_name': 'Trophy'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'ledger.type': {
            'Meta': {'object_name': 'Type'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'ledger.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'gravatar_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'ledger.userprojectsetting': {
            'Meta': {'object_name': 'UserProjectSetting'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Project']", 'null': 'True'}),
            'project_setting': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.ProjectSetting']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'value': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['ledger']
