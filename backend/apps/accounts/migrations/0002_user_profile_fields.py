import datetime

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="name",
            field=models.CharField(default="Usuario sin nombre", max_length=150),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="user",
            name="birthdate",
            field=models.DateField(default=datetime.date(1900, 1, 1)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="user",
            name="country",
            field=models.CharField(default="ZZ", max_length=2),
            preserve_default=False,
        ),
    ]
