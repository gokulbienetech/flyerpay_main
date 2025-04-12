from django.db import models
from django.utils import timezone

class zomato_order(models.Model):
    S_No = models.CharField(max_length=255)
    order_id = models.CharField(unique=True,max_length=255)
    Order_Date = models.DateTimeField()
    Week_No = models.FloatField(null=True, blank=True)
    Res_name = models.CharField(max_length=255)
    Res_ID = models.FloatField(null=True, blank=True)
    Discount_Construct = models.CharField(max_length=255, null=True, blank=True)
    Mode_of_payment = models.CharField(max_length=255, null=True, blank=True)
    Order_status = models.CharField(max_length=255, null=True, blank=True)
    Cancellation_policy = models.CharField(max_length=255, null=True, blank=True)
    Cancellation_Rejection_Reason = models.CharField(max_length=255, null=True, blank=True)
    Cancelled_Rejected_State = models.CharField(max_length=255, null=True, blank=True)
    Order_type = models.CharField(max_length=255, null=True, blank=True)
    Delivery_State_code = models.FloatField(null=True, blank=True)
    Subtotal = models.FloatField(null=True, blank=True)
    Packaging_charge = models.FloatField(null=True, blank=True)
    Delivery_charge_for_restaurants_on_self_logistics = models.FloatField(null=True, blank=True)
    Restaurant_discount_Promo = models.FloatField(null=True, blank=True)
    Restaurant_Discount = models.FloatField(null=True, blank=True)
    Brand_pack_subscription_fee = models.FloatField(null=True, blank=True)
    Delivery_charge_discount_Relisting_discount = models.FloatField(null=True, blank=True)
    Total_GST_collected_from_customers = models.FloatField(null=True, blank=True)
    Net_order_value = models.FloatField(null=True, blank=True)
    Commissionable_value = models.FloatField(null=True, blank=True)
    Service_fees = models.FloatField(null=True, blank=True)
    Service_fee = models.FloatField(null=True, blank=True)
    Payment_mechanism_fee = models.FloatField(null=True, blank=True)
    Service_fee_payment_mechanism_fees = models.FloatField(null=True, blank=True)
    Taxes_on_service_payment_mechanism_fees = models.FloatField(null=True, blank=True)
    Applicable_amount_for_TCS = models.FloatField(null=True, blank=True)
    Applicable_amount_for = models.FloatField(null=True, blank=True)
    Tax_collected_at_source = models.FloatField(null=True, blank=True)
    TCS_IGST_amount = models.FloatField(null=True, blank=True)
    TDS_194O_amount = models.FloatField(null=True, blank=True)
    GST_paid_by_Zomato_on_behalf_of_restaurant_under_section = models.FloatField(null=True, blank=True)
    GST_to_be_paid_by_Restaurant_partner_to_Govt = models.FloatField(null=True, blank=True)
    Government_charges = models.FloatField(null=True, blank=True)
    Customer_Compensation_Recoupment = models.FloatField(null=True, blank=True)
    Delivery_Charges_Recovery = models.FloatField(null=True, blank=True)
    Amount_received_in_cash = models.FloatField(null=True, blank=True)
    Credit_note_adjustment = models.FloatField(null=True, blank=True)
    Promo_recovery_adjustment = models.FloatField(null=True, blank=True)
    Extra_Inventory_Ads_and_Misc = models.FloatField(null=True, blank=True)
    Brand_loyalty_points_redemption = models.FloatField(null=True, blank=True)
    Express_Order_Fee = models.FloatField(null=True, blank=True)
    Other_order_level_deductions = models.FloatField(null=True, blank=True)
    Net_Deductions = models.FloatField(null=True, blank=True)
    Net_Additions = models.FloatField(null=True, blank=True)
    Order_level_Payout = models.FloatField(null=True, blank=True)  # Changed to FloatField
    Settlement_status = models.CharField(max_length=255, null=True, blank=True)
    Settlement_date = models.DateField(null=True, blank=True)  # Changed to DateField
    Bank_UTR = models.CharField(max_length=255, null=True, blank=True)
    Unsettled_Amount = models.FloatField(null=True, blank=True)  # Changed to FloatField
    Customer_ID = models.CharField(max_length=255, null=True, blank=True)
    fp_Client_Name = models.CharField(max_length=255, null=False, blank=False)
    # fp_Dispute_Status = models.CharField(max_length=25, null=True, blank=True)  # Made optional
    fp_restaurant_id = models.CharField(max_length=255)     

    def __str__(self):
        return f"{self.order_id} - {self.Res_name}"





class sales_report(models.Model):
    Date = models.DateField()
    Invoice_Date = models.DateField()
    Client_Order_No = models.CharField(max_length=255)
    Order_From = models.CharField(max_length=255)
    Virtual_Brand_Name = models.CharField(max_length=255)
    Outlet_Display_Name = models.CharField(max_length=255)
    Order_Type = models.CharField(max_length=255)
    Customer_Name = models.CharField(max_length=255)
    Customer_Phone = models.CharField(max_length=20)
    Payment_Type = models.CharField(max_length=255)
    Status = models.CharField(max_length=255)
    Total_Amount = models.FloatField()
    Invoice_No = models.CharField(max_length=255)
    Cancellation_By = models.CharField(max_length=255, null=True, blank=True)
    Client_Name = models.CharField(max_length=255)
    fp_restaurant_id = models.CharField(max_length=255)
    Service_Fee =  models.FloatField()
    Payment_Mechanism_Fee = models.FloatField()
    Taxes_on_Service_Payment_Fees = models.FloatField()
    Expected_Payout = models.FloatField()
    fp_status = models.CharField(max_length=255)
    # fp_restaurant_id = models.CharField(max_length=255)
    def __str__(self):
        return f"{self.Client_Order_No} - {self.fp_Client_Name}"




class SwiggyOrder(models.Model):
    order_id = models.CharField(unique=True, max_length=255)
    parent_order_id = models.CharField(max_length=255, null=True, blank=True)
    fp_order_date = models.DateTimeField()  # Renamed order_date to fp_order_date
    order_status = models.CharField(max_length=255, null=True, blank=True)
    order_category = models.CharField(max_length=255, null=True, blank=True)
    order_payment_type = models.CharField(max_length=255, null=True, blank=True)
    cancelled_by = models.CharField(max_length=255, null=True, blank=True)
    coupon_type_applied_by_customer = models.CharField(max_length=255, null=True, blank=True)
    item_total = models.FloatField(null=True, blank=True)
    packaging_charges = models.FloatField(null=True, blank=True)
    restaurant_discounts_promo_freebies = models.FloatField(null=True, blank=True)
    swiggy_one_exclusive_offer_discount = models.FloatField(null=True, blank=True)
    restaurant_discount_share = models.FloatField(null=True, blank=True)
    net_bill_value_before_taxes = models.FloatField(null=True, blank=True)
    gst_collected = models.FloatField(null=True, blank=True)
    total_customer_paid = models.FloatField(null=True, blank=True)
    commission_charged_on = models.FloatField(null=True, blank=True)
    service_fees = models.FloatField(null=True, blank=True)
    commission = models.FloatField(null=True, blank=True)
    long_distance_charges = models.FloatField(null=True, blank=True)
    discount_on_long_distance_fee = models.FloatField(null=True, blank=True)
    pocket_hero_fees = models.FloatField(null=True, blank=True)
    swiggy_one_fees = models.FloatField(null=True, blank=True)
    payment_collection_charges = models.FloatField(null=True, blank=True)
    restaurant_cancellation_charges = models.FloatField(null=True, blank=True)
    call_center_charges = models.FloatField(null=True, blank=True)
    delivery_fee_sponsored_by_restaurant = models.FloatField(null=True, blank=True)
    gst_on_service_fee = models.FloatField(null=True, blank=True)
    total_swiggy_fees = models.FloatField(null=True, blank=True)
    customer_cancellations = models.IntegerField(null=True, blank=True)
    customer_complaints = models.IntegerField(null=True, blank=True)
    complaint_cancellation_charges = models.FloatField(null=True, blank=True)
    gst_deduction = models.FloatField(null=True, blank=True)
    tcs = models.FloatField(null=True, blank=True)
    tds = models.FloatField(null=True, blank=True)
    total_taxes = models.FloatField(null=True, blank=True)
    net_payout_for_order_after_taxes = models.FloatField(null=True, blank=True)
    
    # Changed to CharField instead of BooleanField
    long_distance_order = models.CharField(max_length=50, null=True, blank=True)
    mfr_accurate = models.CharField(max_length=50, null=True, blank=True)
    mfr_pressed = models.CharField(max_length=50, null=True, blank=True)
    replicated_order = models.CharField(max_length=50, null=True, blank=True)
    swiggy_one_customer = models.CharField(max_length=50, null=True, blank=True)
    pocket_hero_order = models.CharField(max_length=50, null=True, blank=True)
    
    last_mile_km = models.FloatField(null=True, blank=True)
    coupon_code_sourced = models.CharField(max_length=255, null=True, blank=True)
    discount_campaign_id = models.CharField(max_length=255, null=True, blank=True)
    base_order_id = models.CharField(max_length=255, null=True, blank=True)
    cancellation_time = models.DateTimeField(null=True, blank=True)
    pick_up_status = models.CharField(max_length=255, null=True, blank=True)

    # Newly added fields
    fp_client_name = models.CharField(max_length=255, null=False, blank=False)  # Added fp_client_name
    fp_dispute_status = models.CharField(max_length=25, null=True, blank=True)  # Added fp_dispute_status
    fp_restaurant_id = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.order_id} - {self.order_status}"


class sales_report_swiggy(models.Model):
    Date = models.DateField()
    Invoice_Date = models.DateField()
    Client_Order_No = models.CharField(max_length=255)
    Order_From = models.CharField(max_length=255)
    Virtual_Brand_Name = models.CharField(max_length=255)
    Outlet_Display_Name = models.CharField(max_length=255)
    Order_Type = models.CharField(max_length=255)
    Customer_Name = models.CharField(max_length=255)
    Customer_Phone = models.CharField(max_length=20)
    Payment_Type = models.CharField(max_length=255)
    Status = models.CharField(max_length=255)
    Total_Amount = models.FloatField()
    Invoice_No = models.CharField(max_length=255)
    Cancellation_By = models.CharField(max_length=255, null=True, blank=True)
    fp_Client_Name = models.CharField(max_length=255)
    
    fp_Net_Bill = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fp_Net_Bill_GST = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fp_Service_Fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fp_Payment_Mechanism_Fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fp_Taxes_on_Service_Payment_Fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fp_Expected_Payout = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fp_restaurant_id = models.CharField(max_length=255)
    fp_status = models.CharField(max_length=255)

    # created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)

    def __str__(self):
        return f"{self.Client_Order_No} - {self.fp_Client_Name}"

class ClientDetails(models.Model):
    BUSINESS_TYPES = [
        ("Restaurant", "Restaurant"),
        ("Grocery", "Grocery"),
        ("Meat Shop", "Meat Shop"),
        ("Fruit Shop", "Fruit Shop"),
        ("Vegetable Shop", "Vegetable Shop"),
        ("E-commerce Seller", "E-commerce Seller"),
    ]
    MEMBERSHIP_TYPES = [
        ("Monthly", "Monthly"),
        ("Yearly", "Yearly"),
        ("One Time", "One Time"),
    ]

    client_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    postal_address = models.TextField()
    email = models.EmailField()
    contact_number = models.CharField(max_length=15)
    business_type = models.CharField(max_length=50, choices=BUSINESS_TYPES)
    partnership_vendor = models.ManyToManyField('Aggregator', related_name='clients')
    # membership_type = models.CharField(max_length=50, choices=MEMBERSHIP_TYPES)
    membership_type = models.ForeignKey('Membership', on_delete=models.SET_NULL, null=True, blank=True,limit_choices_to={'delflag': 1})

    zomato_finance_poc = models.EmailField(blank=True, null=True)
    zomato_escalation_manager = models.EmailField(blank=True, null=True)
    swiggy_finance_poc = models.EmailField(blank=True, null=True)
    swiggy_escalation_manager = models.EmailField(blank=True, null=True)
    fe_finance_poc = models.EmailField(blank=True, null=True)
    fe_escalation_manager = models.EmailField(blank=True, null=True)

    fp_username = models.CharField(max_length=20)
    fp_password = models.CharField(max_length=10)

    create_date = models.DateTimeField(null=True)  # Automatically set when created
    updated_date = models.DateTimeField(null=True) # Automatically update when modified
    delflag = models.IntegerField(default=1)  # 1 = Active, 0 = Deleted (soft delete)
    postel_code = models.CharField(max_length=20)
    zomato_restaurant_id = models.CharField(max_length=20)
    swiggy_restaurant_id = models.CharField(max_length=20)
    flyereats_restaurant_id = models.CharField(max_length=20)
    zomato_commission_percentage = models.CharField(max_length=20,blank=True, null=True)
    swiggy_commission_percentage = models.CharField(max_length=20,blank=True, null=True)
    flyereats_commission_percentage = models.CharField(max_length=20,blank=True, null=True)
    email_password = models.CharField(max_length=20,blank=True, null=True)
    zomato_tax = models.BooleanField(default=False)
    swiggy_tax = models.BooleanField(default=False)
    flyereats_tax = models.BooleanField(default=False)
    

    def __str__(self):
        return self.client_name



class ReconciliationSummary(models.Model):
    client_name = models.ForeignKey(ClientDetails, on_delete=models.CASCADE, related_name='reconciliations')
    expected_payout = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    actual_payout = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    difference = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_sales_orders = models.IntegerField(default=0)
    total_orders = models.IntegerField(default=0)
    missing_orders_count = models.IntegerField(default=0)
    missing_orders = models.JSONField(default=list)  # Store missing order IDs in JSON format
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('discrepancy', 'Discrepancy Found')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    aggregator = models.CharField(max_length=255)
    from_date = models.DateField(null=True, blank=True)  # Allow null values
    to_date = models.DateField(null=True, blank=True)   # End date of reconciliation period
    restaurant_id = models.CharField(max_length=20)
    

    class Meta:
        unique_together = ('client_name', 'aggregator', 'from_date', 'to_date')  # Prevent duplicate records

    def __str__(self):
        return f"{self.client_name} - {self.aggregator} ({self.from_date} to {self.to_date}) - {self.status}"

    def set_missing_orders(self, missing_orders_list):
        """Store missing orders as JSON."""
        self.missing_orders = json.dumps(missing_orders_list)

    def get_missing_orders(self):
        """Retrieve missing orders from JSON format."""
        return json.loads(self.missing_orders) if self.missing_orders else []


class Aggregator(models.Model):
    PAYMENT_FREQUENCY_CHOICES = [
        ('mon_sun', 'Monday to Sunday'),
        ('sat_sun', 'Saturday to Sunday'),
    ]

    name = models.CharField(max_length=255, unique=True)  # Aggregator Name
    email = models.EmailField(unique=True)  # Aggregator Common Email Address
    payment_frequency = models.CharField(
        max_length=10,
        choices=PAYMENT_FREQUENCY_CHOICES,
        default='mon_sun'
    )
    payment_mechanism_fee = models.CharField(null=True, blank=True, max_length=50)
    payment_mechanism_fee_online = models.CharField(null=True, blank=True, max_length=50)
    delflag = models.IntegerField(default=1)  # 1 (True) means active, 0 (False) means deleted
    created_at = models.DateTimeField(auto_now_add=True)  # Created Date
    updated_at = models.DateTimeField(auto_now=True)  # Updated Date

    def __str__(self):
        return self.name
    
    
    

class Membership(models.Model):
    MEMBERSHIP_CHOICES = [
        ('Monthly', 'Monthly'),
        ('Yearly', 'Yearly'),
        ('One Time', 'One Time'),
    ]
    
    membership_type = models.CharField(max_length=20, choices=MEMBERSHIP_CHOICES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delflag = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.membership_type} - Rs. {self.total_amount}"
    
    
class clients_zomato(models.Model):
    from_date = models.DateTimeField()
    to_date =  models.DateTimeField()
    fp_restaurant_id = models.CharField(max_length=20,)
    client_name = models.CharField(max_length=20,)
    
    
class clients_swiggy(models.Model):
    from_date = models.DateTimeField()
    to_date =  models.DateTimeField()
    fp_restaurant_id = models.CharField(max_length=20,)
    client_name = models.CharField(max_length=20,)


class swiggy_CPC_Ads(models.Model):
    from_date = models.DateTimeField()
    to_date =  models.DateTimeField()
    fp_restaurant_id = models.CharField(max_length=20,)
    client_name = models.CharField(max_length=20,)
    cpc_value = models.DecimalField(max_digits=10, decimal_places=2)  # Changed from CharField to DecimalField

    def __str__(self):
        return f"{self.client_name} ({self.fp_restaurant_id}) - {self.from_date} to {self.to_date}"
    
    class Meta:
        unique_together = ('from_date', 'to_date', 'fp_restaurant_id', 'client_name', 'cpc_value')


class zomato_cpc_ads(models.Model):
    from_date = models.DateTimeField()
    to_date =  models.DateTimeField()
    fp_restaurant_id = models.CharField(max_length=20,)
    client_name = models.CharField(max_length=20,)
    total_ads_inc_gst = models.DecimalField(max_digits=10, decimal_places=2)
    total_dining_ads = models.DecimalField(max_digits=10, decimal_places=2)
    cpc_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ('from_date', 'to_date', 'fp_restaurant_id', 'client_name','total_ads_inc_gst','total_dining_ads', 'cpc_value')
    
    


class SentEmailLog(models.Model):
    subject = models.CharField(max_length=255)         # Email subject
    body = models.TextField()                          # Email content (HTML/text)
    sender = models.EmailField()                       # Who sent the email
    recipients = models.TextField()                    # Comma-separated TO recipients
    cc = models.TextField(blank=True, null=True)       # Comma-separated CC list
    bcc = models.TextField(blank=True, null=True)      # Comma-separated BCC list
    timestamp = models.DateTimeField(auto_now_add=True)  # Auto timestamp when saved
    aggregator = models.CharField(max_length=255)
    restaurant_id = models.CharField(max_length=255)
    date_range = models.CharField(max_length=100)  # NEW
    client_name = models.CharField(max_length=255)
    replies_json = models.JSONField(default=list, blank=True)         # Gmail replies
    user_replies_json = models.JSONField(default=list, blank=True) 
    # order_ids = models.TextField(blank=True, null=True)
    


class SummeryLog(models.Model):
    restaurant_id = models.CharField(max_length=255)
    aggregator = models.CharField(max_length=255)
    order_id = models.CharField(max_length=255)
    
    wrong_payout_settled = models.CharField(max_length=10, default="-")
    wrong_taxes_on_service_payment_fees = models.TextField(default="-")
    wrong_payment_mechanism_fee = models.TextField(default="-")
    wrong_service_fee = models.TextField(default="-")
    cancelled_order_amount_deducted_wrongly = models.TextField(default="-")
    TDS_issue = models.TextField(default="-")
    Wrong_penalty = models.TextField(default="-")
    
    fp_order_date = models.DateTimeField(null=True, blank=True)
    fp_status = models.CharField(max_length=255, default="-")
    

    missing_order_with = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)



# class EmailReplyLog(models.Model):
#     sent_email = models.ForeignKey(SentEmailLog, on_delete=models.CASCADE, related_name="replies")
#     subject = models.CharField(max_length=255)
#     body = models.TextField()
#     sender = models.EmailField()
#     date = models.DateTimeField()


class EmailConversation(models.Model):
    sent_email = models.ForeignKey(SentEmailLog, on_delete=models.CASCADE, related_name='replies')
    from_email = models.EmailField()
    to_email = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    date = models.DateTimeField()