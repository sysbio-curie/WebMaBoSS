from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_estimate_past_activity'),
    ]

    operations = [
        migrations.AddField(
            model_name='mabosssimulation',
            name='observed_graph',
            field=models.TextField(null=True),
        ),
    ]
