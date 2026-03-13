from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('servers', '0003_minecraftserver_seed'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='minecraftserver',
            name='port_number',
        ),
        migrations.AddField(
            model_name='minecraftserver',
            name='server_ip',
            field=models.CharField(max_length=50, null=True, blank=True)
        )
    ]