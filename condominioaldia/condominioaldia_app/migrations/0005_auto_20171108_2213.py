# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-09 02:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('condominioaldia_app', '0004_factura_condominio_demo_mode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cobranza_condominio',
            name='tipo_monto',
            field=models.CharField(choices=[(b'porcEgresos', 'Percentage of expenses'), (b'monto', 'amount'), (b'porAlicuota', 'by alicuote')], max_length=25),
        ),
    ]
