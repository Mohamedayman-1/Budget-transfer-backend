from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account_and_entitys', '0006_rename_xx_adjd_account_entity_limit_xx_account_entity_limit_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MainCurrency',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('icon', models.CharField(max_length=255, null=True, blank=True, help_text='Icon URL or class name for the currency')),
            ],
            options={
                'verbose_name': 'Main Currency',
                'verbose_name_plural': 'Main Currencies',
                'db_table': 'main_currency',
            },
        ),
        migrations.CreateModel(
            name='MainRoutesName',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('english_name', models.CharField(max_length=255)),
                ('arabic_name', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'Main Route Name',
                'verbose_name_plural': 'Main Routes Names',
                'db_table': 'main_routes_name',
            },
        ),
    ]


# i need to make seeder to add this data in table MainRoutesName
#   { label: 'لوحة القيادة - Dashboard' },
#   { label: 'المناقلات - Transfers' },
#   { label: 'التسويه - Fund Adjustment Department' },
#   { label: 'التعزيزات - Additional Fund Request' },
#   { label: 'التعزيزات قيد الاعتماد - Pending Transfers' },
#   { label: 'العقود قيد الاعتماد - Pending Fund Adjustment' },
#   { label: 'التسويات قيد الاعتماد - Pending Additional Fund' },
#   { label: 'إدارة المستخدمين - User Management' },
#   { label: 'إدارة الحسابات والكيانات - Account-Entity Management' },
#   { label: 'الحسابات والكيانات - Accounts & Entities' },
#   { label: 'التحكم - Control' }