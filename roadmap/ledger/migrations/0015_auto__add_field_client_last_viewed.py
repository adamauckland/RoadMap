# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Client.last_viewed'
        db.add_column('ledger_client', 'last_viewed', self.gf('django.db.models.fields.DateField')(null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Client.last_viewed'
        db.delete_column('ledger_client', 'last_viewed')


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
            'date_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 16, 2, 10, 20, 632954)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Item']"}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Location']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
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
            'date_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 16, 2, 10, 20, 630376)'}),
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
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'author'", 'null': 'True', 'to': "orm['auth.User']"}),
            'date_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 16, 2, 10, 20, 622813)'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '4000'}),
            'group': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Item']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
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
            'date_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 16, 2, 10, 20, 620342)'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'fixed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'follow_up': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hours_estimated': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '5', 'decimal_places': '1'}),
            'hours_total': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '5', 'decimal_places': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Type']"}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Location']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Project']"}),
            'priority': ('django.db.models.fields.related.ForeignKey', [], {'default': '2', 'to': "orm['ledger.Priority']"}),
            'replied': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'tags': ('tagging.fields.TagField', [], {}),
            'targets': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['ledger.Target']", 'symmetrical': 'False'}),
            'unseen': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'validated': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'ledger.location': {
            'Meta': {'object_name': 'Location'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'ledger.project': {
            'Meta': {'object_name': 'Project'},
            'deadline': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_viewed': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'binder': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Binder']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
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
        'ledger.binder': {
            'Meta': {'object_name': 'Binder'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Client']", 'blank': 'True'}),
            'default_project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'default_project'", 'null': 'True', 'to': "orm['ledger.Project']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo_url': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'producers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'producers'", 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'reporters': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'reporters'", 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'tags': ('tagging.fields.TagField', [], {}),
            'team': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'team'", 'symmetrical': 'False', 'to': "orm['auth.User']"})
        },
        'ledger.requirement': {
            'Meta': {'object_name': 'Requirement'},
            'delivery_notes': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Item']"}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'ledger.target': {
            'Meta': {'object_name': 'Target'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'deadline': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Project']", 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
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
        }
    }

    complete_apps = ['ledger']
