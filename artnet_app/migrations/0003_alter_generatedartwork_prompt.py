# Generated by Django 4.1 on 2023-03-07 13:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("artnet_app", "0002_backend_textpromptmodel_generatedartwork"),
    ]

    operations = [
        migrations.AlterField(
            model_name="generatedartwork",
            name="prompt",
            field=models.TextField(
                help_text="Type Your Artwork Prompt here.", max_length=500
            ),
        ),
    ]
