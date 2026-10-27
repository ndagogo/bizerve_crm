from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SessionPolicy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'inactivity_timeout_minutes',
                    models.PositiveIntegerField(
                        default=30,
                        help_text='Sign users out after this many minutes without a request. Use 1 to 1,440.',
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(1440),
                        ],
                        verbose_name='Inactivity limit (minutes)',
                    ),
                ),
                (
                    'is_enabled',
                    models.BooleanField(default=True, verbose_name='Sign out after inactivity'),
                ),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Session policy',
                'verbose_name_plural': 'Session policy',
            },
        ),
    ]
