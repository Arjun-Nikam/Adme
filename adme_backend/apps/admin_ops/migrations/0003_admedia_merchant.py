import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("admin_ops", "0002_admedia"),
        ("merchants", "0002_merchant_approval_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="admedia",
            name="merchant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="ad_media",
                to="merchants.merchant",
            ),
        ),
    ]
