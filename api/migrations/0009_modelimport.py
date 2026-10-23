import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_mabosssimulation_observed_graph'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelImport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('repository', models.CharField(max_length=32)),
                ('remote_id', models.CharField(max_length=256)),
                ('name', models.CharField(max_length=256)),
                ('use_sbml_names', models.BooleanField(default=True)),
                ('status', models.CharField(choices=[('Running', 'Busy'), ('Finished', 'Ended'), ('Failed', 'Error')], default='Running', max_length=15)),
                ('error', models.TextField(default='')),
                ('model', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.logicalmodel')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.project')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
