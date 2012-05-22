# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'Priority'
        db.create_table('ledger_priority', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('default', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('ledger', ['Priority'])

        # Adding model 'Type'
        db.create_table('ledger_type', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('ledger', ['Type'])

        # Adding model 'Client'
        db.create_table('ledger_client', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('ledger', ['Client'])

        # Adding model 'Binder'
        db.create_table('ledger_binder', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ledger.Client'], blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('logo_url', self.gf('django.db.models.fields.CharField')(max_length=500, blank=True)),
            ('default_project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='default_project', null=True, to=orm['ledger.Project'])),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
        ))
        db.send_create_signal('ledger', ['Binder'])

        # Adding M2M table for field team on 'Binder'
        db.create_table('ledger_binder_team', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('binder', models.ForeignKey(orm['ledger.binder'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('ledger_binder_team', ['binder_id', 'user_id'])

        # Adding M2M table for field reporters on 'Binder'
        db.create_table('ledger_binder_reporters', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('binder', models.ForeignKey(orm['ledger.binder'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('ledger_binder_reporters', ['binder_id', 'user_id'])

        # Adding M2M table for field producers on 'Binder'
        db.create_table('ledger_binder_producers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('binder', models.ForeignKey(orm['ledger.binder'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('ledger_binder_producers', ['binder_id', 'user_id'])

        # Adding model 'Location'
        db.create_table('ledger_location', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('method', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal('ledger', ['Location'])

        # Adding M2M table for field groups on 'Location'
        #db.create_table('ledger_location_groups', (
        #   ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
        #    ('location', models.ForeignKey(orm['ledger.location'], null=False)),
        #    ('group', models.ForeignKey(orm['auth.group'], null=False))
        #))
        #db.create_unique('ledger_location_groups', ['location_id', 'group_id'])

        # Adding model 'Project'
        db.create_table('ledger_project', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('deadline', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('binder', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ledger.Binder'])),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
        ))
        db.send_create_signal('ledger', ['Project'])

        # Adding model 'Item'
        db.create_table('ledger_item', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=2000)),
            ('item_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ledger.Type'])),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ledger.Location'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ledger.Project'])),
            ('priority', self.gf('django.db.models.fields.related.ForeignKey')(default=2, to=orm['ledger.Priority'])),
            ('assigned_to', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('state', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('fixed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('validated', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('tags', self.gf('tagging.fields.TagField')()),
            ('date_time', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 1, 14, 8, 38, 39, 130790))),
        ))
        db.send_create_signal('ledger', ['Item'])

        # Adding model 'Trophy'
        db.create_table('ledger_trophy', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=2000)),
        ))
        db.send_create_signal('ledger', ['Trophy'])

        # Adding model 'Feed'
        db.create_table('ledger_feed', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=4000)),
            ('date_time', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 1, 14, 8, 38, 39, 132140))),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ledger.Item'], null=True, blank=True)),
        ))
        db.send_create_signal('ledger', ['Feed'])

        # Adding M2M table for field group on 'Feed'
        db.create_table('ledger_feed_group', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('feed', models.ForeignKey(orm['ledger.feed'], null=False)),
            ('group', models.ForeignKey(orm['auth.group'], null=False))
        ))
        db.create_unique('ledger_feed_group', ['feed_id', 'group_id'])

        # Adding model 'Note'
        db.create_table('ledger_note', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ledger.Item'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('ledger', ['Note'])

        # Adding model 'File'
        db.create_table('ledger_file', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ledger.Item'])),
            ('file', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('filetype', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('name', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('ledger', ['File'])

        # Adding model 'Email'
        db.create_table('ledger_email', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ledger.Item'])),
            ('file_id', self.gf('django.db.models.fields.IntegerField')()),
            ('message_id', self.gf('django.db.models.fields.CharField')(max_length=2000)),
            ('in_reply_to', self.gf('django.db.models.fields.CharField')(max_length=2000)),
            ('references', self.gf('django.db.models.fields.CharField')(max_length=4000)),
            ('date_time', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal('ledger', ['Email'])

        # Adding model 'ChecklistItem'
        db.create_table('ledger_checklistitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ledger.Item'])),
            ('order_index', self.gf('django.db.models.fields.IntegerField')()),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=2000)),
            ('filename', self.gf('django.db.models.fields.CharField')(max_length=2000)),
        ))
        db.send_create_signal('ledger', ['ChecklistItem'])

        # Adding model 'Issue'
        db.create_table('ledger_issue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(related_name='issue', to=orm['ledger.Item'])),
            ('replicate_steps', self.gf('django.db.models.fields.TextField')()),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=4000)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('delivery_notes', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('ledger', ['Issue'])

        # Adding M2M table for field associated_media on 'Issue'
        db.create_table('ledger_issue_associated_media', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('issue', models.ForeignKey(orm['ledger.issue'], null=False)),
            ('file', models.ForeignKey(orm['ledger.file'], null=False))
        ))
        db.create_unique('ledger_issue_associated_media', ['issue_id', 'file_id'])

        # Adding model 'Requirement'
        db.create_table('ledger_requirement', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ledger.Item'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('delivery_notes', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('ledger', ['Requirement'])

        # Adding model 'Comment'
        db.create_table('ledger_comment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ledger.Item'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('date_time', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 1, 14, 8, 38, 39, 138240))),
            ('message', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('ledger', ['Comment'])

        # Adding model 'UserProfile'
        db.create_table('ledger_userprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('gravatar_url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
        ))
        db.send_create_signal('ledger', ['UserProfile'])

        # Adding model 'Notification'
        db.create_table('ledger_notification', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ledger.Item'])),
        ))
        db.send_create_signal('ledger', ['Notification'])

        # Adding model 'DailyBasic'
        db.create_table('ledger_dailybasic', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('day', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('quantity', self.gf('django.db.models.fields.IntegerField')()),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ledger.Location'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ledger.Project'])),
        ))
        db.send_create_signal('ledger', ['DailyBasic'])


    def backwards(self, orm):

        # Deleting model 'Priority'
        db.delete_table('ledger_priority')

        # Deleting model 'Type'
        db.delete_table('ledger_type')

        # Deleting model 'Client'
        db.delete_table('ledger_client')

        # Deleting model 'Binder'
        db.delete_table('ledger_binder')

        # Removing M2M table for field team on 'Binder'
        db.delete_table('ledger_binder_team')

        # Removing M2M table for field reporters on 'Binder'
        db.delete_table('ledger_binder_reporters')

        # Removing M2M table for field producers on 'Binder'
        db.delete_table('ledger_binder_producers')

        # Deleting model 'Location'
        db.delete_table('ledger_location')

        # Removing M2M table for field groups on 'Location'
        db.delete_table('ledger_location_groups')

        # Deleting model 'Project'
        db.delete_table('ledger_project')

        # Deleting model 'Item'
        db.delete_table('ledger_item')

        # Deleting model 'Trophy'
        db.delete_table('ledger_trophy')

        # Deleting model 'Feed'
        db.delete_table('ledger_feed')

        # Removing M2M table for field group on 'Feed'
        db.delete_table('ledger_feed_group')

        # Deleting model 'Note'
        db.delete_table('ledger_note')

        # Deleting model 'File'
        db.delete_table('ledger_file')

        # Deleting model 'Email'
        db.delete_table('ledger_email')

        # Deleting model 'ChecklistItem'
        db.delete_table('ledger_checklistitem')

        # Deleting model 'Issue'
        db.delete_table('ledger_issue')

        # Removing M2M table for field associated_media on 'Issue'
        db.delete_table('ledger_issue_associated_media')

        # Deleting model 'Requirement'
        db.delete_table('ledger_requirement')

        # Deleting model 'Comment'
        db.delete_table('ledger_comment')

        # Deleting model 'UserProfile'
        db.delete_table('ledger_userprofile')

        # Deleting model 'Notification'
        db.delete_table('ledger_notification')

        # Deleting model 'DailyBasic'
        db.delete_table('ledger_dailybasic')


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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'ledger.comment': {
            'Meta': {'object_name': 'Comment'},
            'date_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 1, 14, 8, 38, 39, 138240)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Item']"}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
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
            'date_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 1, 14, 8, 38, 39, 132140)'}),
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
            'date_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 1, 14, 8, 38, 39, 130790)'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'fixed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Type']"}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Location']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Project']"}),
            'priority': ('django.db.models.fields.related.ForeignKey', [], {'default': '2', 'to': "orm['ledger.Priority']"}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'tags': ('tagging.fields.TagField', [], {}),
            'validated': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'ledger.location': {
            'Meta': {'object_name': 'Location'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'ledger.project': {
            'Meta': {'object_name': 'Project'},
            'deadline': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            'team': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'team'", 'symmetrical': 'False', 'to': "orm['auth.User']"})
        },
        'ledger.requirement': {
            'Meta': {'object_name': 'Requirement'},
            'delivery_notes': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ledger.Item']"}),
            'text': ('django.db.models.fields.TextField', [], {})
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
