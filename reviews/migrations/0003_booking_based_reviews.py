# Generated migration: booking-based reviews (one review per booking)

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0001_initial'),  # adjust if your first booking migration has different name
        ('reviews', '0002_alter_review_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='booking',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='reviews',
                to='bookings.booking',
            ),
        ),
        migrations.RemoveConstraint(
            model_name='review',
            name='unique_review_per_service',
        ),
        migrations.RemoveConstraint(
            model_name='review',
            name='unique_review_per_provider_no_service',
        ),
        migrations.AddConstraint(
            model_name='review',
            constraint=models.UniqueConstraint(
                condition=models.Q(('booking__isnull', False)),
                fields=('booking',),
                name='unique_review_per_booking',
            ),
        ),
    ]
