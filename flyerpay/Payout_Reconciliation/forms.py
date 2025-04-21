from django import forms
from .models import ClientDetails,Aggregator,Membership

class ClientDetailsForm(forms.ModelForm):

    partnership_vendor = forms.ModelMultipleChoiceField(
        queryset=Aggregator.objects.filter(delflag=1),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    # zomato_tax = forms.BooleanField(required=False, label="Zomato Tax Applicable")
    # swiggy_tax = forms.BooleanField(required=False, label="Swiggy Tax Applicable")
    # flyereats_tax = forms.BooleanField(required=False, label="Swiggy Tax Applicable")
    class Meta:
        model = ClientDetails
        exclude = ["create_date", "updated_date", "delflag"]  # Exclude these fields
        widgets = {
            "client_name" : forms.TextInput(attrs={"class": "form-control", "id": "client_name", "placeholder": "Enter Client Name*"}),
            "location": forms.TextInput(attrs={"class": "form-control", "id": "location", "placeholder": "Enter Location*"}),
            "postal_address": forms.TextInput(attrs={"class": "form-control", "id": "postal_address", "placeholder": "Enter Postal Address*"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "id": "email", "placeholder": "Enter Email*"}),
            "contact_number": forms.TextInput(attrs={"class": "form-control", "id": "contact_number", "placeholder": "Enter Contact Number*"}),
            "business_type": forms.Select(attrs={"class": "form-control", "id": "business_type"}),
            # "partnership_vendor": forms.TextInput(attrs={"class": "form-control", "id": "partnership_vendor", "placeholder": "Enter Vendor"}),
            "membership_type": forms.Select(attrs={"class": "form-control", "id": "membership_type"}),
            "zomato_finance_poc": forms.EmailInput(attrs={"class": "form-control", "id": "zomato_finance_poc","placeholder": "Enter Finance Poc Mail"}),
            "zomato_escalation_manager": forms.EmailInput(attrs={"class": "form-control", "id": "zomato_escalation_manager","placeholder": "Enter Escalation Manager Mail"}),
            "swiggy_finance_poc": forms.EmailInput(attrs={"class": "form-control", "id": "swiggy_finance_poc","placeholder": "Enter Finance Poc Mail"}),
            "swiggy_escalation_manager": forms.EmailInput(attrs={"class": "form-control", "id": "swiggy_escalation_manager","placeholder": "Enter Escalation Manager Mail"}),
            "fe_finance_poc": forms.EmailInput(attrs={"class": "form-control", "id": "fe_finance_poc","placeholder": "Enter Finance Poc Mail "}),
            "fe_escalation_manager": forms.EmailInput(attrs={"class": "form-control", "id": "fe_escalation_manager","placeholder": "Enter Escalation Manager Mail"}),
            "fp_username": forms.TextInput(attrs={"class": "form-control", "id": "fp_username","placeholder": "Enter Username*"}),
            "fp_password": forms.PasswordInput(attrs={"class": "form-control", "id": "fp_password","placeholder": "Enter Password*"}),
            "postel_code": forms.TextInput(attrs={"class": "form-control", "id": "postel_code","placeholder": "Enter Postal Code*"}),
            "zomato_restaurant_id": forms.TextInput(attrs={"class": "form-control", "id": "zomato_res_id","placeholder": "Enter restaurant Id*"}),
            "swiggy_restaurant_id": forms.TextInput(attrs={"class": "form-control", "id": "swiggy_res_id","placeholder": "Enter restaurant Id*"}),
            "flyereats_restaurant_id": forms.TextInput(attrs={"class": "form-control", "id": "flyereats_res_id","placeholder": "Enter restaurant Id*"}),
            "zomato_commission_percentage": forms.TextInput(attrs={"class": "form-control", "id": "zomato_commission_percentage","placeholder": "Enter Zomato Commission %"}),
            "swiggy_commission_percentage": forms.TextInput(attrs={"class": "form-control", "id": "swiggy_commission_percentage","placeholder": "Enter Swiggy Commission %"}),
            "flyereats_commission_percentage": forms.TextInput(attrs={"class": "form-control", "id": "flyereats_commission_percentage","placeholder": "Enter FlyerEats Commission %"}),
            "email_password": forms.TextInput(attrs={"class": "form-control", "id": "email_password","placeholder": "Enter Email Password"}),
            "zomato_tax": forms.CheckboxInput(attrs={"class": "form-check-input","id": "zomato_tax"}),
            "swiggy_tax": forms.CheckboxInput(attrs={"class": "form-check-input","id": "swiggy_tax"}),
            "flyereats_tax": forms.CheckboxInput(attrs={"class": "form-check-input","id": "flyereats_tax"}),
            
        }


class UploadExcelForm_Zomato(forms.Form):
    zomato_payout_file = forms.FileField(label="Upload Zomato Payout Settlement Annexure")
    zomato_sales_file = forms.FileField(label="Upload Zomato Merchant Sales Report")

    # Dropdown for selecting Client_Name
    client_name = forms.ModelChoiceField(
        queryset=ClientDetails.objects.filter(delflag=1),
        empty_label="Select Client", 
        label="Client Name"
    )

    # Dropdown for selecting the correct Zomato Restaurant ID
    zomato_restaurant_id = forms.ChoiceField(
        label="Zomato Restaurant ID",
        required=True,
        choices=[("", "Select a restaurant")],  # Initially empty, filled via AJAX
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'client_name' in self.data:
            try:
                client_id = int(self.data.get('client_name'))
                restaurant_choices = [
                    (c.zomato_restaurant_id, c.zomato_restaurant_id)
                    for c in ClientDetails.objects.filter(id=client_id)
                ]
                self.fields['zomato_restaurant_id'].choices += restaurant_choices
            except (ValueError, ClientDetails.DoesNotExist):
                pass





class UploadExcelForm_Swiggy(forms.Form):
    swiggy_payout_file = forms.FileField(label="Upload Swiggy Payout Settlement Annexure")
    swiggy_sales_file = forms.FileField(label="Upload Swiggy Merchant Sales Report")

    # Dropdown for selecting Client_Name
    client_name = forms.ModelChoiceField(
        queryset=ClientDetails.objects.filter(delflag=1), 
        empty_label="Select Client", 
        label="Client Name"
    )

    # Dropdown for selecting the correct Swiggy Restaurant ID
    swiggy_restaurant_id = forms.ChoiceField(
        label="Swiggy Restaurant ID",
        required=True,
        choices=[("", "Select a restaurant")],  # Initially empty, filled dynamically
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'client_name' in self.data:
            try:
                client_id = int(self.data.get('client_name'))
                restaurant_choices = [
                    (c.swiggy_restaurant_id, c.swiggy_restaurant_id)
                    for c in ClientDetails.objects.filter(id=client_id)
                ]
                self.fields['swiggy_restaurant_id'].choices += restaurant_choices
            except (ValueError, ClientDetails.DoesNotExist):
                pass
# UploadExcelForm_FlyerEats
class UploadExcelForm_FlyerEats(forms.Form):
    flyereats_payout_file = forms.FileField(label="Upload FlyerEats Payout Settlement Annexure")
    flyereats_sales_file = forms.FileField(label="Upload FlyerEats Merchant Sales Report")

    # Dropdown for selecting Client_Name
    client_name = forms.ModelChoiceField(
        queryset=ClientDetails.objects.filter(delflag=1), 
        empty_label="Select Client", 
        label="Client Name"
    )


class AggregatorForm(forms.ModelForm):
    class Meta:
        model = Aggregator
        fields = ['name', 'email', 'payment_frequency','payment_mechanism_fee','payment_mechanism_fee_online']  # Excluding `delflag`, `created_at`, `updated_at`
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Aggregator Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter Email Address'}),
            'payment_mechanism_fee': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Payment Mechanism Fee'}),
            'payment_mechanism_fee_online': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Payment Mechanism Fee online'}),
            'payment_frequency': forms.Select(attrs={'class': 'form-select'}),
        }






class MembershipForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ['membership_type', 'total_amount']  # Excluding `delflag`, `created_at`, `updated_at`
        widgets = {
            'membership_type': forms.Select(attrs={'class': 'form-select'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Total Amount in Rs.'}),
        }


