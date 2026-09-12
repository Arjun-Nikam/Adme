from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("merchants", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="merchant",
            name="approval_status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending review"),
                    ("approved", "Approved"),
                    ("rejected", "Rejected"),
                ],
                default="approved",
                max_length=20,
            ),
        ),
    ]