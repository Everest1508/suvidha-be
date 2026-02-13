# Generated migration: add lat/lon to SavedAddress

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('addresses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='savedaddress',
            name='latitude',
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                help_text='Latitude from map/location',
                max_digits=9,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='savedaddress',
            name='longitude',
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                help_text='Longitude from map/location',
                max_digits=9,
                null=True,
            ),
        ),
    ]
