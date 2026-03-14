from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('servers', '0004_fix_schema'),
    ]

    operations = [
        migrations.AddField(
            model_name='minecraftserver',
            name='status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('PROVISIONING', 'Provisioning EC2'),
                    ('INSTALLING', 'Installing Dependencies'),
                    ('STARTING', 'Starting Container'),
                    ('BOOTING', 'Booting Minecraft'),
                    ('ONLINE', 'Online'),
                    ('OFFLINE', 'Offline'),
                ],
                default='PROVISIONING',
            ),
        )
    ]