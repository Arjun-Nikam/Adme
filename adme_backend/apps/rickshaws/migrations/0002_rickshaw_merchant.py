import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rickshaws", "0001_initial"),
        ("merchants", "0002_merchant_approval_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="rickshaw",
            name="merchant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="rickshaws",
                to="merchants.merchant",
            ),
        ),
    ]
