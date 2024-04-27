from django.apps import AppConfig
from django.conf import settings

class LogicalmodellingConfig(AppConfig):
    name = 'api'

    def ready(self):
        
        if settings.DATABASES['default']['HOST'] is not None and not settings.RUN_INSTALL:
            
            from api.models.common import create_guest_account
            create_guest_account()