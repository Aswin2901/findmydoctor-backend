from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('doctors', '0006_previous_migration_name'),  # Update this to the actual previous migration
    ]

    operations = [
        migrations.AddField(
            model_name='appointmentavailability',
            name='duration_temp',
            field=models.IntegerField(null=True),
        ),
        migrations.RunSQL(
            """
            UPDATE doctors_appointmentavailability
            SET duration_temp = EXTRACT(EPOCH FROM duration) / 60
            WHERE duration IS NOT NULL;
            """
        ),
        migrations.RemoveField(
            model_name='appointmentavailability',
            name='duration',
        ),
        migrations.RenameField(
            model_name='appointmentavailability',
            old_name='duration_temp',
            new_name='duration',
        ),
    ]