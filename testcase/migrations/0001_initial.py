# Generated by Django 5.1.3 on 2024-11-30 06:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='InputFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('file', models.FileField(upload_to='data/testcase/input')),
            ],
        ),
        migrations.CreateModel(
            name='TestCases',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('problem_id', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='OutputFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='data/testcase/output')),
                ('inputfile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='output', to='testcase.inputfile')),
            ],
        ),
        migrations.AddField(
            model_name='inputfile',
            name='testcase',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inputfiles', to='testcase.testcases'),
        ),
    ]