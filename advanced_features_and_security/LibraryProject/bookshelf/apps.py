from django.apps import AppConfig

from django.apps import AppConfig

class AdvancedFeaturesAndSecurityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'advanced_features_and_security'

    def ready(self):
        import bookshelf.signals

class BookshelfConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookshelf'
