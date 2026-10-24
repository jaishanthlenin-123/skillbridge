from django.db import migrations
from config.errors import ERROR_REGISTRY

def seed_error_codes(apps, schema_editor):
    ErrorCode = apps.get_model('core', 'ErrorCode')
    for code, info in ERROR_REGISTRY.items():
        ErrorCode.objects.update_or_create(
            code=code,
            defaults={
                'http_status': info['http_status'],
                'title': info['title'],
                'meaning': info['meaning'],
                'typical_cause': info.get('typical_cause', ''),
                'explanation': info['explanation'],
                'recovery_action': info['recovery_action'],
                'retryable': info['retryable'],
                'is_active': True,
            }
        )

def unseed_error_codes(apps, schema_editor):
    ErrorCode = apps.get_model('core', 'ErrorCode')
    ErrorCode.objects.filter(code__in=list(ERROR_REGISTRY.keys())).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_error_codes, reverse_code=unseed_error_codes),
    ]
