from django.apps import AppConfig

class SubscriptionsConfig(AppConfig):
    name = 'lms.djangoapps.subscriptions'
    verbose_name = 'Bundles and Subscriptions'

    def ready(self):
        super().ready()

        # noinspection PyUnresolvedReferences
        import lms.djangoapps.subscriptions.signals  # pylint: disable=unused-import, import-outside-toplevel

