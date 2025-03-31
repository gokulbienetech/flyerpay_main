from django.apps import AppConfig


class PayoutReconciliationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Payout_Reconciliation'
    
    
    def ready(self):
        import Payout_Reconciliation.signals
