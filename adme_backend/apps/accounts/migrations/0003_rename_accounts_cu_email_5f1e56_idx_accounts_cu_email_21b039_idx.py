from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_customersignupchallenge"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="customersignupchallenge",
            old_name="accounts_cu_email_5f1e56_idx",
            new_name="accounts_cu_email_21b039_idx",
        ),
    ]
