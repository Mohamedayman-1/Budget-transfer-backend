from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


def check_table_exists(schema_editor, table_name):
    """Check if table exists in Oracle database"""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM user_tables WHERE table_name = %s
        """, [table_name.upper()])
        return cursor.fetchone()[0] > 0


def safe_create_table(apps, schema_editor, model_name, model_class):
    """Safely create table only if it doesn't exist"""
    table_name = model_class._meta.db_table
    if not check_table_exists(schema_editor, table_name):
        schema_editor.create_model(model_class)


def safe_add_index(schema_editor, model, index):
    """Safely add index only if it doesn't exist"""
    try:
        schema_editor.add_index(model, index)
    except Exception:
        # Index might already exist, skip
        pass


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user_management', '0001_initial'),
        ('budget_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(
            code=lambda apps, schema_editor: None,  # Forward operation
            reverse_code=lambda apps, schema_editor: None,  # Reverse operation
        ),
        
        migrations.CreateModel(
            name='ApprovalWorkflowTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=60, unique=True)),
                ('transfer_type', models.CharField(choices=[('FAR', 'FAR'), ('AFR', 'AFR'), ('FAD', 'FAD'), ('GEN', 'Generic')], max_length=10)),
                ('name', models.CharField(max_length=120)),
                ('description', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('version', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'APPR_WORKFLOW_TEMPLATE',
                'ordering': ['transfer_type', '-version', 'code'],
            },
        ),
        
        migrations.CreateModel(
            name='ApprovalWorkflowStageTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_index', models.PositiveIntegerField(help_text='1-based ordering of stages')),
                ('name', models.CharField(max_length=120)),
                ('decision_policy', models.CharField(choices=[('ALL', 'All must approve'), ('ANY', 'Any one can approve'), ('QUORUM', 'Quorum of approvals')], default='ALL', max_length=10)),
                ('quorum_count', models.PositiveIntegerField(blank=True, null=True)),
                ('required_role', models.CharField(blank=True, help_text='Optional user.role filter', max_length=50, null=True)),
                ('dynamic_filter_json', models.TextField(blank=True, help_text='Reserved for future dynamic filtering (store JSON string)', null=True)),
                ('allow_reject', models.BooleanField(default=True)),
                ('allow_delegate', models.BooleanField(default=False)),
                ('sla_hours', models.PositiveIntegerField(blank=True, null=True)),
                ('parallel_group', models.PositiveIntegerField(blank=True, help_text='Future use: stages in same group run in parallel', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('workflow_template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stages', to='approvals.approvalworkflowtemplate')),
                ('required_user_level', models.ForeignKey(blank=True, help_text='If set, assignments will include users with this level', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stage_templates', to='user_management.xx_userlevel')),
            ],
            options={
                'db_table': 'APPR_WORKFLOW_STAGE_TEMPLATE',
                'ordering': ['workflow_template', 'order_index'],
            },
        ),
        
        migrations.CreateModel(
            name='ApprovalWorkflowInstance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')], default='pending', max_length=15)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('completed_stage_count', models.PositiveIntegerField(default=0)),
                ('budget_transfer', models.OneToOneField(db_column='transaction_id', on_delete=django.db.models.deletion.CASCADE, related_name='workflow_instance', to='budget_management.xx_budgettransfer')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='instances', to='approvals.approvalworkflowtemplate')),
                ('current_stage_template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='active_instances', to='approvals.approvalworkflowstagetemplate')),
            ],
            options={
                'db_table': 'APPR_WORKFLOW_INSTANCE',
            },
        ),
        
        migrations.CreateModel(
            name='ApprovalWorkflowStageInstance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('active', 'Active'), ('completed', 'Completed'), ('skipped', 'Skipped'), ('cancelled', 'Cancelled')], default='pending', max_length=12)),
                ('activated_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('workflow_instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stage_instances', to='approvals.approvalworkflowinstance')),
                ('stage_template', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='stage_instances', to='approvals.approvalworkflowstagetemplate')),
            ],
            options={
                'db_table': 'APPR_WORKFLOW_STAGE_INSTANCE',
                'ordering': ['workflow_instance', 'stage_template__order_index'],
            },
        ),
        
        migrations.CreateModel(
            name='ApprovalAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role_snapshot', models.CharField(blank=True, max_length=50, null=True)),
                ('level_snapshot', models.CharField(blank=True, max_length=50, null=True)),
                ('is_mandatory', models.BooleanField(default=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('delegated', 'Delegated')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('stage_instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='approvals.approvalworkflowstageinstance')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='approval_assignments', to='user_management.xx_user')),
            ],
            options={
                'db_table': 'APPR_ASSIGNMENT',
            },
        ),
        
        migrations.CreateModel(
            name='ApprovalAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('approve', 'Approve'), ('reject', 'Reject'), ('delegate', 'Delegate'), ('comment', 'Comment')], max_length=10)),
                ('comment', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('triggers_stage_completion', models.BooleanField(default=False)),
                ('stage_instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='approvals.approvalworkflowstageinstance')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='approval_actions', to='user_management.xx_user')),
                ('assignment', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='action', to='approvals.approvalassignment')),
            ],
            options={
                'db_table': 'APPR_ACTION',
                'ordering': ['created_at'],
            },
        ),
        
        migrations.CreateModel(
            name='ApprovalDelegation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('deactivated_at', models.DateTimeField(blank=True, null=True)),
                ('from_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delegations_given', to='user_management.xx_user')),
                ('to_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delegations_received', to='user_management.xx_user')),
                ('stage_instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delegations', to='approvals.approvalworkflowstageinstance')),
            ],
            options={
                'db_table': 'APPR_DELEGATION',
            },
        ),
        
        # Add constraints and indexes safely
        migrations.AlterUniqueTogether(
            name='approvalworkflowstagetemplate',
            unique_together={('workflow_template', 'order_index')},
        ),
        migrations.AlterUniqueTogether(
            name='approvalassignment',
            unique_together={('stage_instance', 'user')},
        ),
    ]
