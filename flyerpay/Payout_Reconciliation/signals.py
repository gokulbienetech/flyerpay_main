from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import zomato_order, clients_zomato



@receiver(post_delete, sender=zomato_order)
def delete_clients_zomato_if_no_orders_left(sender, instance, **kwargs):
    """
    Deletes clients_zomato entry if no zomato_order exist for its date range.
    """
    related_clients = clients_zomato.objects.filter(
        from_date__lte=instance.Order_Date, 
        to_date__gte=instance.Order_Date,
        fp_restaurant_id=instance.fp_restaurant_id,
        client_name=instance.Client_Name
    )
    
    for client in related_clients:
        # Check if any orders still exist within this date range
        remaining_orders = zomato_order.objects.filter(
            fp_restaurant_id=client.fp_restaurant_id,
            Client_Name=client.client_name,
            Order_Date__range=[client.from_date, client.to_date]
        ).exists()

        if not remaining_orders:
            client.delete()
