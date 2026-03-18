from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('servers', '0005_minecraftserver_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='minecraftserver',
            name='ram',
            field=models.IntegerField(
                choices=[(2, '2GB'), (4, '4GB'), (8, '8GB'), (16, '16GB')],
                default=2,
            ),
        )
    ]
