from email.utils import parsedate_to_datetime
from itertools import count
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
import pandas as pd
from django.core.files.storage import default_storage
from django.contrib import messages
from sqlalchemy import create_engine, text
from .models import  CustomUser, EmailConversation, PopupLead, SentEmailLog, SummeryLog, UserType, zomato_order,sales_report,sales_report_swiggy,SwiggyOrder,ReconciliationSummary, ClientDetails,Aggregator,Membership,clients_zomato,clients_swiggy,swiggy_CPC_Ads,zomato_cpc_ads
from django.http import HttpResponse, JsonResponse
from .forms import ClientDetailsForm, DemoRequestForm ,UploadExcelForm_Zomato,AggregatorForm,UploadExcelForm_Swiggy,UploadExcelForm_FlyerEats,MembershipForm,UserTypeForm
from datetime import datetime,date, timedelta
from django.db.models import Sum, F
from django.utils.timezone import make_aware        
from django.db import connection,transaction
from django.utils.dateparse import parse_date
import json
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail,EmailMessage,get_connection
from django.conf import settings
import logging
from django.db.models import Q
from sqlalchemy.types import String
import decimal
from django.db.models.functions import TruncDate
from .email_utils import fetch_replies_from_gmail
from collections import Counter
from django.db.models import Count, F, Window
from django.db.models.functions import RowNumber
from django.utils import timezone




logger = logging.getLogger(__name__)

# def home_page(request):
#     return render(request, "index.html")
    # return HttpResponse("Hello from index view!")





def client_details_view(request):
    """Handles adding, displaying, and deleting clients on the same page."""
    clients = ClientDetails.objects.filter(delflag=1)  # Show only active clients
    form = ClientDetailsForm()

    if request.method == "POST":
        form = ClientDetailsForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.created_date = now()
            client.updated_date = now()
            client.save()
            form.save_m2m()  # Save ManyToMany relationships
            return JsonResponse({"message": "Client added successfully!"}, status=200)

        print("Form errors:", form.errors)  # Moved before returning response
        return JsonResponse({"errors": form.errors}, status=400)

    # Ensure GET requests always return JSON when requested via AJAX
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        clients_data = list(clients.values())
        return JsonResponse({"clients": clients_data})

    return render(request, "client_master_form.html", {"form": form, "clients": clients})



def client_edit(request, pk):
    """Handles updating client details via AJAX."""
    client = get_object_or_404(ClientDetails, pk=pk)
    
    print("Client Found:", client.client_name)  # Debugging print

    if request.method == "POST":
        form = ClientDetailsForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save(commit=False)
            client.updated_date = now()

            # Check if membership exists before saving
            membership_id = request.POST.get("membership")
            if membership_id:
                try:
                    client.membership = Membership.objects.get(id=membership_id, delflag=1)  # Only active memberships
                except Membership.DoesNotExist:
                    return JsonResponse({"error": "Selected membership does not exist!"}, status=400)

            client.save()
            form.save_m2m()  # Save ManyToMany fields
            return JsonResponse({"message": "Client updated successfully!"}, status=200)
        else:
            return JsonResponse({"errors": form.errors}, status=400)

    # Ensure membership exists before accessing it
    membership_type = client.membership_type.membership_type if client.membership_type else None
    
    membership_id = client.membership_type.id if client.membership_type else None  

    client_data = {
        "id": client.id,
        "client_name": client.client_name,
        "location": client.location,
        "postal_address": client.postal_address,
        "postel_code": client.postel_code,
        "email": client.email,
        "contact_number": client.contact_number,
        "business_type": client.business_type,
        "partnership_vendor": list(client.partnership_vendor.values_list("id", flat=True)),
        "membership_type": membership_id,  # Handle missing membership safely
        "zomato_finance_poc": client.zomato_finance_poc,
        "zomato_escalation_manager": client.zomato_escalation_manager,
        "swiggy_finance_poc": client.swiggy_finance_poc,
        "swiggy_escalation_manager": client.swiggy_escalation_manager,
        "fe_finance_poc": client.fe_finance_poc,
        "fe_escalation_manager": client.fe_escalation_manager,
        # "fp_username": client.fp_username,
        # "fp_password": client.fp_password,
        "zomato_restaurant_id": client.zomato_restaurant_id,
        "swiggy_restaurant_id": client.swiggy_restaurant_id,
        "flyereats_restaurant_id": client.flyereats_restaurant_id,
        "zomato_commission_percentage": client.zomato_commission_percentage,
        "swiggy_commission_percentage": client.swiggy_commission_percentage,
        "flyereats_commission_percentage": client.flyereats_commission_percentage,
        "email_password": client.email_password,
        "zomato_tax": client.zomato_tax,
        "swiggy_tax": client.swiggy_tax,
        "flyereats_tax": client.flyereats_tax,
    }
    
    print("partnership_vendor", list(client.partnership_vendor.values_list("id", flat=True)))
    print("Client Data:", client_data)  # Debugging print

    return JsonResponse({"client": client_data}, status=200)





def client_delete(request, pk):
    """Soft delete a client."""
    client = get_object_or_404(ClientDetails, pk=pk)
    client.delflag = 0  # Soft delete
    client.save()
    return JsonResponse({"message": "Client deleted successfully!"}, status=200)



#Create User 

# def add_user_type_ajax(request):
#     if request.method == "POST":
#         name = request.POST.get("name")
#         if name:
#             user_type, created = UserType.objects.get_or_create(name=name, delflag=1)
#             return JsonResponse({"success": True, "id": user_type.id, "name": user_type.name})
#     return JsonResponse({"success": False})

# def user_list(request):
#     users = CustomUser.objects.filter(delflag=1)
#     return render(request, 'user_list.html', {'users': users})

# def get_user(request, user_id):
#     user = CustomUser.objects.get(id=user_id)
#     return JsonResponse({
#         "id": user.id,
#         "full_name": user.full_name,
#         "email": user.email,
#         "phone_number": user.phone_number,
#         "username": user.username,
#         "user_type": user.user_type.id if user.user_type else None,
#         "clients": list(user.clients.values_list('id', flat=True)),
#     })

# @csrf_exempt
# def save_user(request):
#     if request.method == 'POST':
#         data = request.POST
#         user_id = data.get("user_id")
#         if user_id:
#             user = CustomUser.objects.get(id=user_id)
#         else:
#             user = CustomUser()

#         user.full_name = data.get("full_name")
#         user.email = data.get("email")
#         user.phone_number = data.get("phone_number")
#         user.username = data.get("username")
#         if data.get("password"):
#             user.password = make_password(data.get("password"))
#         user.user_type_id = data.get("user_type")
#         user.save()
#         if "clients" in data:
#             user.clients.set(data.getlist("clients"))
#         return JsonResponse({"success": True})
#     return JsonResponse({"success": False}, status=400)

# @csrf_exempt
# def delete_user(request, user_id):
#     user = CustomUser.objects.get(id=user_id)
#     user.delflag = 0
#     user.save()
#     return JsonResponse({"success": True})





db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "Flyerpay"
}

def convert_decimal_to_float(data):
    """Recursively convert Decimal values in a dictionary or list to float."""
    if isinstance(data, dict):
        return {key: convert_decimal_to_float(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_decimal_to_float(item) for item in data]
    elif isinstance(data, Decimal):
        return float(data)  # Convert Decimal to float
    elif isinstance(data, datetime):
        return data.strftime('%Y-%m-%d %H:%M:%S')  # Convert datetime to string
    return data



@csrf_exempt

def send_reconciliation_email(request):
    try:
        if request.method == "POST":
            data = json.loads(request.body)
            aggregator = data.get("aggregator")
            restaurant_id = data.get("restaurant_id")
            selected_date_range = data.get("selected_date_range")
            client_name = data.get("client_name")
            email_body = data.get("email_body")  # Editable content from frontend
            email_subject = data.get("email_subject")
            cc_emails = data.get("cc_emails", "").split(",") 
            additional_emails = data.get("additional_emails", "").split(",")  # Get additional emails
            
            print(email_subject,"email_subject")
            
            client_c = ClientDetails.objects.filter(
                Q(zomato_restaurant_id=restaurant_id) | Q(swiggy_restaurant_id=restaurant_id)
            ).first()
            sender_email = client_c.email if client_c.email else "default_sender@example.com"
            recipient_emails = []

            # Fetch recipients based on aggregator
            if aggregator == "Zomato":
                client_details = ClientDetails.objects.filter(zomato_restaurant_id=restaurant_id).first()
                if not client_details:
                    return JsonResponse({"message": "No client details found!"}, status=400)
                recipient_emails = [email for email in [client_details.zomato_finance_poc, client_details.zomato_escalation_manager] if email]
            elif aggregator == "Swiggy":
                client_details = ClientDetails.objects.filter(swiggy_restaurant_id=restaurant_id).first()
                if not client_details:
                    return JsonResponse({"message": "No client details found!"}, status=400)
                recipient_emails = [email for email in [client_details.swiggy_finance_poc, client_details.swiggy_escalation_manager] if email]

            # Combine all recipients
            recipient_emails.extend([email.strip() for email in additional_emails if email.strip()])  # Add additional emails
            if not recipient_emails:
                return JsonResponse({"message": "No recipient emails found!"}, status=400)
            
            # email_subject = f"Issue in {aggregator} Payout for {selected_date_range} - {restaurant_id}"

            # Check if client has custom SMTP settings
            if client_c.email and client_c.email_password:
                connection = get_connection(
                    backend="django.core.mail.backends.smtp.EmailBackend",
                    host="smtp.gmail.com",
                    port=587,
                    username=client_c.email,
                    password=client_c.email_password,
                    use_tls=True,
                )
            else:
                connection = get_connection()

            # Send email
            email = EmailMessage(
                subject=email_subject,
                body=email_body,
                from_email=sender_email,
                to=recipient_emails,
                cc=cc_emails,
                connection=connection
            )
            email.content_subtype = "html"  # Set email format to HTML
            email.send()
            SentEmailLog.objects.create(
                    subject=email_subject,                     # Comes from frontend or generated
                    body=email_body,                           # HTML or text content
                    sender=sender_email,                       # Client's sender email
                    recipients=",".join(recipient_emails),     # Converts list to comma-separated string
                    cc=",".join(cc_emails),                    # Converts list to string for logging
                    bcc="gokulms7885@gmail.com",                # Hardcoded or dynamic BCC for tracking
                    # order_ids=",".join(data.get("order_ids", [])) 
                    aggregator = aggregator,
                    restaurant_id = restaurant_id,
                    date_range = selected_date_range,
                    client_name = client_name,
                )

            add_dispute_raised(aggregator,restaurant_id,selected_date_range)
            print("recipient_emails:",recipient_emails)
            
            if aggregator == "Zomato":
                print(clients_zomato.objects.count())
                print(sales_report.objects.all())
                print("start_processing_update_fp_status")
                date_range = data.get("selected_date_range")  # e.g., "10-Mar-2025 to 16-Mar-2025"
                start_date_str, end_date_str = date_range.split(" to ")
                start_date = datetime.strptime(start_date_str.strip(), "%d-%b-%Y").date()
                end_date = datetime.strptime(end_date_str.strip(), "%d-%b-%Y").date()
                print(type(restaurant_id),type(start_date), end_date,)
                update_sales_status_proc(restaurant_id, start_date, end_date)
            elif aggregator == "Swiggy":
                print(clients_zomato.objects.count())
                print(sales_report.objects.all())
                print("start_processing_update_fp_status")
                date_range = data.get("selected_date_range")  # e.g., "10-Mar-2025 to 16-Mar-2025"
                start_date_str, end_date_str = date_range.split(" to ")
                start_date = datetime.strptime(start_date_str.strip(), "%d-%b-%Y").date()
                end_date = datetime.strptime(end_date_str.strip(), "%d-%b-%Y").date()
                print(type(restaurant_id),type(start_date), end_date,)
                update_sales_status_proc_swiggy(restaurant_id, start_date, end_date)


            return JsonResponse({"message": "Email sent successfully!"})

    except Exception as e:
        logger.exception(f"Error sending email: {e}")
        return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)




def get_payout_and_order_summary(request, client_name, aggregator, from_date, to_date, restaurant_id):
    """Fetch payout reconciliation data based on the selected aggregator."""
    
    from_date = str(from_date) if from_date else None
    to_date = str(to_date) if to_date else None
    print(from_date,"from_date")
    print(to_date,"to_date")
    from_date_f = datetime.strptime(from_date, "%Y-%m-%d")
    to_date_t = datetime.strptime(to_date, "%Y-%m-%d")
    from_date_t = from_date_f.replace(hour=0, minute=0, second=0, microsecond=0)
    to_date_t = to_date_t.replace(hour=23, minute=59, second=59, microsecond=999999)
    cpc_ads = None
    print(from_date,"from_date444")
    print(to_date,"to_date444")
    print(cpc_ads,"print(cpc_ads)")
    client_commission = None
    if aggregator == "Zomato":
        
        client_commission = ClientDetails.objects.filter(zomato_restaurant_id=restaurant_id).values("zomato_commission_percentage").first()
        cpc_ads = zomato_cpc_ads.objects.filter(fp_restaurant_id=restaurant_id,from_date=from_date_t,to_date = to_date_t).values("cpc_value").first()
    if aggregator == "Swiggy":
        
        client_commission = ClientDetails.objects.filter(swiggy_restaurant_id=restaurant_id).values("swiggy_commission_percentage").first()
        cpc_ads = swiggy_CPC_Ads.objects.filter(fp_restaurant_id=restaurant_id,from_date=from_date_t,to_date=to_date_t).values("cpc_value").first()

    client_email = None
    if aggregator == "Zomato":
        client_email = ClientDetails.objects.filter(zomato_restaurant_id=restaurant_id).values("email").first()
    if aggregator == "Swiggy":
        client_email = ClientDetails.objects.filter(swiggy_restaurant_id=restaurant_id).values("email").first()

    procedure_map = {
        "Zomato": "Reconciliation_new",
        "Swiggy": "Reconciliation_Swiggy",
        "FlyerEats": "Reconciliation_FlyerEats"
    }
    
    
    # from_date = str(from_date) if from_date else None
    # to_date = str(to_date) if to_date else None

    if aggregator not in procedure_map:
        return {"error": "Invalid Aggregator"}

    procedure_name = procedure_map[aggregator]

    with connection.cursor() as cursor:
        cursor.callproc(procedure_name, [client_name, restaurant_id, from_date, to_date])
        
        # Fetch Summary Result
        summary_result = cursor.fetchone()
        if not summary_result:
            return {"error": "No data found for the given inputs"}
        
        # Fetch Pending Orders
        cursor.nextset()
        pending_orders = []
        pending_order = []
        total_issue_code = set()
        pending_orders_result = cursor.fetchall()
        if aggregator == "Zomato":
            for row in pending_orders_result:
                issue_codes = row[17].split(',') if row[17] else []
                total_issue_code.update(issue_codes)
                pending_orders.append({
            "order_id": row[0],
            "fp_expected_payout": row[1],
            "fp_taxes_on_service_payment_fees": row[2] if row[2] else 0,
            "fp_payment_mechanism_fee": row[3] if row[3] else 0,
            "fp_service_fee": row[4] if row[4] else 0,
            "zomato_order_level_payout": row[5],
            "zomato_taxes_on_service_payment_mechanism_fees": row[6],
            "zomato_payment_mechanism_fee": row[7],
            "zomato_service_fee": row[8],
            "cancellation_charge_percentage": row[15],
            "pending_order_difference": row[16],
            "issue_codes": issue_codes,
            "wrong_payout_settled": "Yes" if '1' in issue_codes else "-",
            "wrong_taxes_on_service_payment_fees": f"instead of ₹{row[2]} Deducted ₹{row[6]}, Difference {round((row[2]-row[6]),2)}" if '2' in issue_codes else "-",
            "wrong_payment_mechanism_fee": f"instead of ₹{row[3]} Deducted ₹{row[7]}, Difference {round((row[3]-row[7]),2)}" if '3' in issue_codes else "-",
            "wrong_service_fee": f"instead of ₹{row[4]} Deducted ₹{row[8]}, Difference {round((row[4]-row[8]),3)}" if '4' in issue_codes else "-",
            "cancelled_order_amount_deducted_wrongly": f"instead of {row[15]}% Settled only {round((row[5]/row[11]*100),2)}% Difference ₹{row[16]}" if '5' in issue_codes else "-",
            "TDS_issue": f"TDS Calculated Wrongly instead of {round(row[11]*0.001,2)} Deducted {row[13]}, Difference {round(((row[11]*0.001)-row[13]),2)}" if '6' in issue_codes else "-",
            "Wrong_penalty": f"Wrong penalty Charges Imposed instead of {row[5]} Deducted {round((row[5]/row[11]*100),2)}, Difference {row[15]}" if '7' in issue_codes else "-",
            "fp_order_date": row[9],
            "fp_status": row[10],
            "fp_total_amt": row[11],
            "zo_total_amt": row[12],
            "zo_TDS": row[13],
            "Reconcilation_status":row[14],
            "issue":len(issue_codes)
        })
            pending_orders.append(pending_order)
            print(pending_orders,"pending_order555")
        
        
        elif aggregator == "Swiggy":
            
            for row in pending_orders_result:
                issue_codes = row[19].split(',') if row[19] else []
                print(issue_codes,"issue_codes",row[18])
                total_issue_code.update(issue_codes)
                

                pending_orders.append( {
            "order_id": row[0],
            "fp_expected_payout": row[1],
            "fp_taxes_on_service_payment_fees": row[2],
            "fp_payment_mechanism_fee": row[3],
            "fp_service_fee": row[4],
            "zomato_order_level_payout": row[5],
            "zomato_taxes_on_service_payment_mechanism_fees": row[6],
            "zomato_payment_mechanism_fee": row[7],
            "zomato_service_fee": row[8],
            "cancellation_charge_percentage": row[17],
            "pending_order_difference": row[18],
            "issue_codes": issue_codes,
            "wrong_payout_settled": "Yes" if '1' in issue_codes else "-",
            "wrong_taxes_on_service_payment_fees": f"instead of ₹{row[2]} Deducted ₹{row[6]}, Difference {round((row[2]-row[6]),2)}" if '2' in issue_codes else "-",
            "wrong_payment_mechanism_fee": f"instead of ₹{row[3]} Deducted ₹{row[7]}, Difference {round((row[3]-row[7]),2)}" if '3' in issue_codes else "-",
            "wrong_service_fee": f"instead of ₹{row[4]} Deducted ₹{row[8]}, Difference {round((row[4]-row[8]),3)}" if '4' in issue_codes else "-",
            "cancelled_order_amount_deducted_wrongly": f"instead of {row[17]}% Settled only {round((row[5]/row[11]*100),2)}% Difference ₹{row[18]}" if '5' in issue_codes else "-",
            "TDS_issue": f"TDS Calculated Wrongly instead of {round(row[11]*0.001,2)} Deducted {row[13]}, Difference {round(((row[11]*0.001)-row[13]),2)}" if '6' in issue_codes else "-",
            "Wrong_penalty": f"Wrong penalty Charges Imposed instead of {row[17]}% Deducted {round((row[5]/row[11]*100),2)}%, Difference {row[18]}" if '7' in issue_codes else "-",
            "fp_order_date": row[9],
            "fp_status": row[10],
            "fp_total_amt": row[11],
            "zo_total_amt": row[12],
            "zo_TDS": row[13],
            "mfr_accurate": row[14],  # column index 14 is `mfr_accurate`
            "mfr_pressed": row[15],    # column index 15 is `mfr_pressed`
            "issue":len(issue_codes),
            "Reconcilation_status":row[16]
            
        })
        pending_orders.append(pending_order)
        cursor.nextset()
        missing_orders = [
            {
                "order_id": row[0],
                "order_date": row[1],
                "fp_expected_payout": row[2],
                "fp_taxes_on_service_payment_fees": row[3],
                "fp_payment_mechanism_fee": row[4],
                "fp_service_fee": row[5],
                "fp_total_amt": row[6],
                "fp_status_raw": row[7],
            } for row in cursor.fetchall()
        ]
        
        if aggregator == "Swiggy":
            for row in pending_orders_result:
                issue_codes = row[19].split(',')

                if issue_codes and issue_codes != ['']:
                    exists = SummeryLog.objects.filter(
            restaurant_id=restaurant_id,
            aggregator=aggregator,
            order_id=row[0]
        ).exists()

                    if not exists:
                        SummeryLog.objects.create(
                restaurant_id=restaurant_id,
                aggregator=aggregator,
                order_id=row[0],
                wrong_payout_settled=f"instead of ₹{row[1]} Setteled Only ₹{row[5]}" if '1' in issue_codes else "-",
                wrong_taxes_on_service_payment_fees=f"instead of ₹{row[2]} Deducted ₹{row[6]}, Difference {round((row[2]-row[6]), 2)}" if '2' in issue_codes else "-",
                wrong_payment_mechanism_fee=f"instead of ₹{row[3]} Deducted ₹{row[7]}, Difference {round((row[3]-row[7]), 2)}" if '3' in issue_codes else "-",
                wrong_service_fee=f"instead of ₹{row[4]} Deducted ₹{row[8]}, Difference {round((row[4]-row[8]), 3)}" if '4' in issue_codes else "-",
                cancelled_order_amount_deducted_wrongly=f"instead of {row[17]}% Settled only {round((row[5]/row[11]*100), 2)}% Difference ₹{row[18]}" if '5' in issue_codes else "-",
                TDS_issue=f"TDS Calculated Wrongly instead of {round(row[11]*0.001, 2)} Deducted {row[13]}, Difference {round(((row[11]*0.001)-row[13]), 2)}" if '6' in issue_codes else "-",
                Wrong_penalty=f"Wrong penalty Charges Imposed instead of {row[17]}% Deducted {round((row[5]/row[11]*100), 2)}%, Difference {row[18]}" if '7' in issue_codes else "-",
                fp_order_date=row[9],
                fp_status=row[16],
                missing_order_with="-"
            )

        elif aggregator == "Zomato":
            for row in pending_orders_result:
                issue_codes = row[17].split(',')

                if issue_codes and issue_codes != ['']:
                    exists = SummeryLog.objects.filter(
            restaurant_id=restaurant_id,
            aggregator=aggregator,
            order_id=row[0]
        ).exists()

                    if not exists:
                        SummeryLog.objects.create(
                restaurant_id=restaurant_id,
                aggregator=aggregator,
                order_id=row[0],
                wrong_payout_settled=f"instead of ₹{row[1]} Setteled Only ₹{row[5]}" if '1' in issue_codes else "-",
                wrong_taxes_on_service_payment_fees=f"instead of ₹{row[2]} Deducted ₹{row[6]}, Difference {round((row[2]-row[6]), 2)}" if '2' in issue_codes else "-",
                wrong_payment_mechanism_fee=f"instead of ₹{row[3]} Deducted ₹{row[7]}, Difference {round((row[3]-row[7]), 2)}" if '3' in issue_codes else "-",
                wrong_service_fee=f"instead of ₹{row[4]} Deducted ₹{row[8]}, Difference {round((row[4]-row[8]), 3)}" if '4' in issue_codes else "-",
                cancelled_order_amount_deducted_wrongly=f"instead of {row[15]}% Settled only {round((row[5]/row[11]*100), 2)}% Difference ₹{row[16]}" if '5' in issue_codes else "-",
                TDS_issue=f"TDS Calculated Wrongly instead of {round(row[11]*0.001, 2)} Deducted {row[13]}, Difference {round(((row[11]*0.001)-row[13]), 2)}" if '6' in issue_codes else "-",
                Wrong_penalty=f"Wrong penalty Charges Imposed instead of {row[5]} Deducted {round((row[5]/row[11]*100), 2)}, Difference {row[15]}" if '7' in issue_codes else "-",
                fp_order_date=row[9],
                fp_status=row[14],
                missing_order_with="-"
            )

        
        # print(pending_orders,"pending orders555")

        
        for order in missing_orders:
            SummeryLog.objects.get_or_create(
        restaurant_id=restaurant_id,
        aggregator=aggregator,
        order_id=order["order_id"],
        defaults={
            "wrong_payout_settled": "-",
            "wrong_taxes_on_service_payment_fees": "-",
            "wrong_payment_mechanism_fee": "-",
            "wrong_service_fee": "-",
            "cancelled_order_amount_deducted_wrongly": "-",
            "TDS_issue": "-",
            "Wrong_penalty": "-",
            "fp_order_date": order.get("order_date", "-"),
            "fp_status": "Missing",
            "missing_order_with": "Missing in payout but found in internal records"
        }
    )

    print( summary_result[2],"6666")


        
    from_date = datetime.strptime(from_date, "%Y-%m-%d")
    to_date = datetime.strptime(to_date, "%Y-%m-%d")
    # Format as needed
    from_date_1 = from_date.strftime("%d-%b-%Y")
    to_date_1 = to_date.strftime("%d-%b-%Y")
    latest_log = SentEmailLog.objects.filter(
    aggregator=aggregator,
    restaurant_id=restaurant_id,
    date_range=f"{from_date_1} to {to_date_1}"
        ).order_by('-timestamp').last()
    latest_log_1 = SentEmailLog.objects.filter(
    aggregator=aggregator,
    restaurant_id=restaurant_id,
    date_range=f"{from_date_1} to {to_date_1}"
        ).order_by('-timestamp').first()
    print(latest_log_1,"latest_log_one")
    # print(latest_log,"latest_log")
    days_since_email = (date.today() - latest_log.timestamp.date()).days if latest_log else None
    days_since_email_new = (date.today() - latest_log_1.timestamp.date()).days if latest_log_1 else None
    print(days_since_email_new,"days_since_email_new")
    # total_difference=sum(pending_orders["pending_order_difference"])
    total_difference = round(sum(item["pending_order_difference"] for item in pending_orders if "pending_order_difference" in item),2)
    total_missing_order_sum = round(sum(item["fp_expected_payout"] for item in missing_orders if "fp_expected_payout" in item ),2)
    difference = total_missing_order_sum+abs(total_difference)
    report_data = {
        "client_name": summary_result[0],
        "restaurant_id": restaurant_id,
        "aggregator": aggregator,
        "expected_payout": summary_result[2] +(cpc_ads["cpc_value"] if cpc_ads and "cpc_value" in cpc_ads and cpc_ads["cpc_value"] < 0 else -cpc_ads["cpc_value"] if cpc_ads and "cpc_value" in cpc_ads else 0),
        "actual_payout": summary_result[3]+(cpc_ads["cpc_value"] if cpc_ads and "cpc_value" in cpc_ads and cpc_ads["cpc_value"] < 0 else -cpc_ads["cpc_value"] if cpc_ads and "cpc_value" in cpc_ads else 0),
        "difference": summary_result[4] or 0,
        "total_sales_orders": summary_result[5] or 0,
        "total_orders": summary_result[6] or 0,
        "missing_orders_count": summary_result[7] or 0,
        "Pending_Orders_Count": summary_result[8] or 0,
        "status": "completed" if (summary_result[4] or 0) == 0 else "Pending",
        "missing_orders": missing_orders,
        "pending_orders": pending_orders,
        "selected_date_range": f"{from_date_1} to {to_date_1}",
        "selected_date_range_1": f"{from_date} to {to_date}",
        "client_commission":client_commission,
        "client_email":client_email,
        "cpc_ads" : (cpc_ads["cpc_value"] if cpc_ads and cpc_ads["cpc_value"] else 0),
        "total_difference":total_difference,
        "total_missing_order_sum":total_missing_order_sum,    
        "total_issue_code":sorted(list(total_issue_code) ),
        "days_since_last_email": days_since_email,
        "days_since_last_email_new": days_since_email_new,
        
    }
    # print(report_data['days_since_last_email'],"days_since_last_email")
    # print(report_data['missing_orders'],"missing_orders")
    # Convert Decimal values to float before saving in session
    report_data_serializable = json.loads(json.dumps(report_data, default=convert_decimal_to_float))

    # Store in session
    request.session["report_data"] = report_data_serializable
    request.session.modified = True

    # print("Session Data Stored:", json.dumps(request.session.get("report_data"), indent=2))
    print(report_data["expected_payout"],"expected_payout5555666",report_data["cpc_ads"],"cpc_ads")
    print("total_issue_code",report_data["total_issue_code"])

    log = SentEmailLog.objects.last()
    print(log.user_replies_json,"LOG_USER_RE")

    return report_data



def upload_excel(request):
    """Handles file upload and reconciliation report generation."""
    
    # Fetch client name and filters from request
    client_name = request.GET.get("client_name", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")
    selected_aggregator = request.GET.get("aggregator", "")
    restaurant_id = request.GET.get("restaurant_id")
    date_range = request.GET.get("date_range")
    

    message = None
    report_data = None
    reconciliation_date = None  

    # Fetch clients and aggregators dynamically
    clients = ClientDetails.objects.filter(delflag=1)
    aggregators = Aggregator.objects.filter(delflag=1)

    # Initialize forms
    zomato_form = UploadExcelForm_Zomato()
    swiggy_form = UploadExcelForm_Swiggy()
    flyereats_form = UploadExcelForm_FlyerEats()

    if request.method == "POST":
        aggregator_type = request.POST.get("aggregator", "").lower()

        form_map = {
            "zomato": UploadExcelForm_Zomato(request.POST, request.FILES),
            "swiggy": UploadExcelForm_Swiggy(request.POST, request.FILES),
            "flyereats": UploadExcelForm_FlyerEats(request.POST, request.FILES),
        }

        form = form_map.get(aggregator_type)

        if form and form.is_valid():
            client_name = form.cleaned_data["client_name"]

            # Fetch uploaded files safely
            payout_file = request.FILES.get(f"{aggregator_type}_payout_file")
            sales_file = request.FILES.get(f"{aggregator_type}_sales_file")
            
            print(payout_file,"payout_file")

            if payout_file and sales_file:
                # Process files based on aggregator type
                if aggregator_type == "zomato":
                    zomato_restaurant_id = form.cleaned_data["zomato_restaurant_id"]
                    process_zomato_payout(payout_file, client_name,zomato_restaurant_id)
                    result = process_zomato_payout(payout_file, client_name,zomato_restaurant_id)
                    min_date, max_date = result.get("min_date"), result.get("max_date")
                    cancelled_orders = result.get("cancelled_orders")
                    rejected_orders = result.get("rejected_orders")
                    ordinary_order = result.get("ordinary_order")
                    print("555payout_details",cancelled_orders)
                    process_zomato_sales(sales_file,db_config, client_name,zomato_restaurant_id,min_date,max_date,cancelled_orders,rejected_orders,ordinary_order)
                    
                    return JsonResponse({
                    "status": "success",
                    "message": "File processed successfully.",
                    })
                elif aggregator_type == "swiggy":
                    swiggy_restaurant_id = form.cleaned_data["swiggy_restaurant_id"]
                    process_swiggy_payout(payout_file, client_name,db_config,swiggy_restaurant_id)
                    result = process_swiggy_payout(payout_file, client_name, db_config,swiggy_restaurant_id)
                    min_date, max_date = result.get("min_date"), result.get("max_date")
                    cancelled_orders = result.get("cancelled_orders")
                    ordinary_order = result.get("ordinary_order")
                    process_swiggy_sales(sales_file, client_name,min_date, max_date,swiggy_restaurant_id,cancelled_orders,ordinary_order)
                    

                    return JsonResponse({
                    "status": "success",
                    "message": "File processed successfully.",
                    "missing_columns": result["missing_columns"],
                    "newly_added_columns": result["newly_added_columns"]
                    })
                elif aggregator_type == "flyereats":
                    process_flyereats_payout(payout_file, client_name)
                    process_flyereats_sales(sales_file, client_name)

                message = f"{aggregator_type.capitalize()} files uploaded successfully!"
            else:
                message = "Both payout and sales files are required!"
        else:
            message = "Invalid form submission. Please check your inputs."

    from_date = to_date = None
    if date_range:
        try:
            # Extracting from_date and to_date from the "03-Mar-2025 to 09-Mar-2025" format
            from_date_str, to_date_str = date_range.split(" to ")
            from_date = datetime.strptime(from_date_str, "%d-%b-%Y").date()
            to_date = datetime.strptime(to_date_str, "%d-%b-%Y").date()
        except ValueError:
            print("Error: Invalid date format received!")

    # Check if required parameters exist
    if client_name and from_date and to_date:
        # Call the function with extracted values
        report_data = get_payout_and_order_summary(request,client_name, selected_aggregator, from_date, to_date,restaurant_id)
        reconciliation_date = datetime.now().strftime('%d-%b-%Y')  # Format: 06-March-2025

    return render(request, "file_uploading.html", {
        "clients": clients,
        "aggregators": aggregators,
        "selected_aggregator": selected_aggregator,
        "zomato_form": zomato_form,
        "swiggy_form": swiggy_form,
        "flyereats_form": flyereats_form,
        "message": message,
        "client_name": client_name,
        "from_date": from_date,
        "to_date": to_date,
        "report_data": report_data,
        "total_missing_orders": report_data["missing_orders_count"] if report_data else 0,
        "missing_orders": report_data["missing_orders"] if report_data else [],
        "reconciliation_date": reconciliation_date
    })

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "Flyerpay"
}



    
    
def process_zomato_payout(file_path, client_name,zomato_restaurant_id):
    """Process Zomato Aggregator Payout Settlement Annexure data and store it in zomato_order and clients_zomato."""

    # Load Excel file
    xls = pd.ExcelFile(file_path)
    df = pd.read_excel(xls, sheet_name=2, skiprows=1, header=None)

    df_cpc_ads = pd.read_excel(xls, sheet_name=1, skiprows=41, nrows=2, usecols=[5], header=None)

    print(df_cpc_ads,"df_cpc_ads")
    # Define column names
    column_names = [
        "S_No", "order_id", "Order_Date", "Week_No", "Res_name", "Res_ID",
        "Discount_Construct", "Mode_of_payment", "Order_status", "Cancellation_policy",
        "Cancellation_Rejection_Reason", "Cancelled_Rejected_State", "Order_type", 
        "Delivery_State_code", "Subtotal", "Packaging_charge",
        "Delivery_charge_for_restaurants_on_self_logistics", "Restaurant_discount_Promo", 
        "Restaurant_Discount", "Brand_pack_subscription_fee", 
        "Delivery_charge_discount_Relisting_discount", "Total_GST_collected_from_customers", 
        "Net_order_value", "Commissionable_value", "Service_fees", "Service_fee", 
        "Payment_mechanism_fee", "Service_fee_payment_mechanism_fees", 
        "Taxes_on_service_payment_mechanism_fees", "Applicable_amount_for_TCS", 
        "Applicable_amount_for", "Tax_collected_at_source", "TCS_IGST_amount", 
        "TDS_194O_amount", "GST_paid_by_Zomato_on_behalf_of_restaurant_under_section", 
        "GST_to_be_paid_by_Restaurant_partner_to_Govt", "Government_charges", 
        "Customer_Compensation_Recoupment", "Delivery_Charges_Recovery", 
        "Amount_received_in_cash", "Credit_note_adjustment", "Promo_recovery_adjustment", 
        "Extra_Inventory_Ads_and_Misc", "Brand_loyalty_points_redemption", 
        "Express_Order_Fee", "Other_order_level_deductions", "Net_Deductions", 
        "Net_Additions", "Order_level_Payout", "Settlement_status", "Settlement_date", 
        "Bank_UTR", "Unsettled_Amount", "Customer_ID",
    ]

    df.columns = column_names
    df["Client_Name"] = str(client_name)
    df["fp_restaurant_id"] = str(zomato_restaurant_id)
    # print(df["Client_Name"],"df6666")
    df["order_id"] = pd.to_numeric(df["order_id"], errors="coerce").fillna(0).astype(int)
    df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
    
     # Get min and max order dates from the uploaded file
    min_date = df["Order_Date"].min().replace(hour=0, minute=0, second=0, microsecond=0)
    max_date = df["Order_Date"].max().replace(hour=23, minute=59, second=59, microsecond=999999)
    # Connect to MySQL
    if df_cpc_ads.shape[0] >= 2:  # Ensure at least 2 rows exist
        total_ads_inc_gst = df_cpc_ads.iloc[0, 0]  # First row
        total_dining_ads = df_cpc_ads.iloc[1, 0]  # Second row
        cpc_value = total_ads_inc_gst + total_dining_ads
        print("cpc:",cpc_value)
    else:
        total_ads_inc_gst = total_dining_ads = cpc_value = 0
        print("cpc=0")  # Default values
        
    engine = create_engine(f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}")

    with engine.connect() as conn:

        existing_order_ids = pd.read_sql("SELECT order_id FROM zomato_order", con=engine)
        existing_order_ids_set = set(existing_order_ids["order_id"].astype(int))

        df_new_orders = df[~df["order_id"].isin(existing_order_ids_set)]
        if not df_new_orders.empty:
            df_new_orders.to_sql("zomato_order", con=engine, if_exists="append", index=False)
            print(f"Inserted {len(df_new_orders)} new records into zomato_order.")
        else:
            print("No new orders to insert (all already exist in zomato_order).")
        
        client_name = str(client_name)
        min_date = min_date.to_pydatetime()
        max_date = max_date.to_pydatetime()
        
        
        cpc_insert_query = text("""
            INSERT INTO payout_reconciliation_zomato_cpc_ads 
            (from_date, to_date, fp_restaurant_id, client_name, total_ads_inc_gst, total_dining_ads, cpc_value)
            VALUES (:from_date, :to_date, :fp_restaurant_id, :client_name, :total_ads_inc_gst, :total_dining_ads, :cpc_value)
            ON DUPLICATE KEY UPDATE 
                total_ads_inc_gst = VALUES(total_ads_inc_gst),
                total_dining_ads = VALUES(total_dining_ads),
                cpc_value = VALUES(cpc_value);
        """)

        conn.execute(cpc_insert_query, {
            "from_date": min_date,
            "to_date": max_date,
            "fp_restaurant_id": zomato_restaurant_id,
            "client_name": client_name,
            "total_ads_inc_gst": float(total_ads_inc_gst),
            "total_dining_ads": float(total_dining_ads),
            "cpc_value": float(cpc_value)
        })
        conn.commit()
        print("Inserted or updated CPC Ads data :",cpc_value)
        
        # Insert CPC Ads Data
        # cpc_insert_query = text("""
        #     INSERT INTO payout_reconciliation_zomato_cpc_ads (from_date, to_date, fp_restaurant_id, client_name, total_ads_inc_gst,total_dining_ads,total_cpc)
        #     SELECT :from_date, :to_date, :fp_restaurant_id, :client_name, :total_ads_inc_gst, :total_dining_ads, :total_cpc
        #     FROM DUAL
        #     WHERE NOT EXISTS (
        #         SELECT 1 FROM payout_reconciliation_swiggy_cpc_ads
        #         WHERE from_date = :from_date
        #         AND to_date = :to_date
        #         AND fp_restaurant_id = :fp_restaurant_id
        #         AND client_name = :client_name
        #     )
        # """)
        # conn.execute(cpc_insert_query, {
        #     "from_date": min_date,
        #     "to_date": max_date,
        #     "fp_restaurant_id": zomato_restaurant_id,
        #     "client_name": client_name,
        #     "total_ads_inc_gst": float(total_ads_inc_gst),
        #     "total_dining_ads":float(total_dining_ads),
        #     "total_cpc":float(total_cpc)
        # })
        # conn.commit()
        # print("Inserted CPC Ads data.")

   
       
    engine.dispose()
    # print(min_date,max_date,"max_date")
    # Extract cancelled orders
    cancelled_orders = df[df["Order_status"] == "CANCELLED"][["order_id", "Cancelled_Rejected_State"]].to_dict(orient="records")
    rejected_orders = df[df["Order_status"] == "REJECTED"][["order_id","Cancelled_Rejected_State", "Cancellation_Rejection_Reason"]].to_dict(orient="records")
    ordinary_order = df[df["Order_status"] == "DELIVERED"][["order_id", "Customer_Compensation_Recoupment"]].to_dict(orient="records")
    print(cancelled_orders,"cancelled_orders")
    print(rejected_orders,"rejected_orders")
    print(ordinary_order,"ordinary_order")
    return {
        "status": "success",
        "message": "File processed successfully.",
        "min_date": min_date,
        "max_date": max_date,
        "cancelled_orders": cancelled_orders,
        "rejected_orders":rejected_orders,
        "ordinary_order":ordinary_order
    }




# def process_zomato_payout(file_path, client_name, zomato_restaurant_id):
#     """Process Zomato Aggregator Payout Settlement Annexure data and store it in zomato_order and clients_zomato."""

#     try:
#         # Load Excel file
#         xls = pd.ExcelFile(file_path)
#         df = pd.read_excel(xls, sheet_name=2, skiprows=1, header=None)
#         df_cpc_ads = pd.read_excel(xls, sheet_name=1, skiprows=41, nrows=2, usecols=[5], header=None)

#         # Define column names
#         column_names = [
#             "S_No", "order_id", "Order_Date", "Week_No", "Res_name", "Res_ID",
#             "Discount_Construct", "Mode_of_payment", "Order_status", "Cancellation_policy",
#             "Cancellation_Rejection_Reason", "Cancelled_Rejected_State", "Order_type", 
#             "Delivery_State_code", "Subtotal", "Packaging_charge",
#             "Delivery_charge_for_restaurants_on_self_logistics", "Restaurant_discount_Promo", 
#             "Restaurant_Discount", "Brand_pack_subscription_fee", 
#             "Delivery_charge_discount_Relisting_discount", "Total_GST_collected_from_customers", 
#             "Net_order_value", "Commissionable_value", "Service_fees", "Service_fee", 
#             "Payment_mechanism_fee", "Service_fee_payment_mechanism_fees", 
#             "Taxes_on_service_payment_mechanism_fees", "Applicable_amount_for_TCS", 
#             "Applicable_amount_for", "Tax_collected_at_source", "TCS_IGST_amount", 
#             "TDS_194O_amount", "GST_paid_by_Zomato_on_behalf_of_restaurant_under_section", 
#             "GST_to_be_paid_by_Restaurant_partner_to_Govt", "Government_charges", 
#             "Customer_Compensation_Recoupment", "Delivery_Charges_Recovery", 
#             "Amount_received_in_cash", "Credit_note_adjustment", "Promo_recovery_adjustment", 
#             "Extra_Inventory_Ads_and_Misc", "Brand_loyalty_points_redemption", 
#             "Express_Order_Fee", "Other_order_level_deductions", "Net_Deductions", 
#             "Net_Additions", "Order_level_Payout", "Settlement_status", "Settlement_date", 
#             "Bank_UTR", "Unsettled_Amount", "Customer_ID",
#         ]

#         df.columns = column_names
#         df["fp_Client_Name"] = str(client_name)
#         df["fp_restaurant_id"] = str(zomato_restaurant_id)

#         df["order_id"] = pd.to_numeric(df["order_id"], errors="coerce").fillna(0).astype(int)
#         df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")

#         min_date = df["Order_Date"].min().replace(hour=0, minute=0, second=0, microsecond=0)
#         max_date = df["Order_Date"].max().replace(hour=23, minute=59, second=59, microsecond=999999)

#         # Extract CPC values
#         if df_cpc_ads.shape[0] >= 2:
#             total_ads_inc_gst = df_cpc_ads.iloc[0, 0]
#             total_dining_ads = df_cpc_ads.iloc[1, 0]
#             cpc_value = total_ads_inc_gst + total_dining_ads
#         else:
#             total_ads_inc_gst = total_dining_ads = cpc_value = 0

#         print("CPC Value:", cpc_value)

#         # Connect to DB
#         engine = create_engine(f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}")

#         with engine.begin() as conn:
#             # Get existing order IDs
#             existing_order_ids = pd.read_sql("SELECT order_id FROM payout_reconciliation_zomato_order", con=conn)
#             existing_order_ids_set = set(existing_order_ids["order_id"].astype(int))

#             df_new_orders = df[~df["order_id"].isin(existing_order_ids_set)]

#             if not df_new_orders.empty:
#                 df_new_orders.to_sql("payout_reconciliation_zomato_order", con=conn, if_exists="append", index=False)
#                 print(f"Inserted {len(df_new_orders)} new records into payout_reconciliation_zomato_order.")
#             else:
#                 print("No new orders to insert.")

#             # Insert/Update CPC Ads Data
#             cpc_insert_query = text("""
#                 INSERT INTO payout_reconciliation_zomato_cpc_ads 
#                 (from_date, to_date, fp_restaurant_id, client_name, total_ads_inc_gst, total_dining_ads, cpc_value)
#                 VALUES (:from_date, :to_date, :fp_restaurant_id, :client_name, :total_ads_inc_gst, :total_dining_ads, :cpc_value)
#                 ON DUPLICATE KEY UPDATE 
#                     total_ads_inc_gst = VALUES(total_ads_inc_gst),
#                     total_dining_ads = VALUES(total_dining_ads),
#                     cpc_value = VALUES(cpc_value);
#             """)

#             conn.execute(cpc_insert_query, {
#                 "from_date": min_date,
#                 "to_date": max_date,
#                 "fp_restaurant_id": zomato_restaurant_id,
#                 "client_name": client_name,
#                 "total_ads_inc_gst": float(total_ads_inc_gst),
#                 "total_dining_ads": float(total_dining_ads),
#                 "cpc_value": float(cpc_value)
#             })

#             print("CPC Ads data inserted or updated.")

#         engine.dispose()

#         # Extract orders for response
#         cancelled_orders = df[df["Order_status"] == "CANCELLED"][["order_id", "Cancelled_Rejected_State"]].to_dict(orient="records")
#         rejected_orders = df[df["Order_status"] == "REJECTED"][["order_id", "Cancelled_Rejected_State", "Cancellation_Rejection_Reason"]].to_dict(orient="records")
#         ordinary_order = df[df["Order_status"] == "DELIVERED"][["order_id", "Customer_Compensation_Recoupment"]].to_dict(orient="records")
#         print(cancelled_orders,"cancelled_orders")
#         print(rejected_orders,"rejected_orders")        
#         # print(rejected_orders,"rejected_orders")        
#         return {
#             "status": "success",
#             "message": "File processed successfully.",
#             "min_date": min_date,
#             "max_date": max_date,
#             "cancelled_orders": cancelled_orders,
#             "rejected_orders": rejected_orders,
#             "ordinary_order": ordinary_order
#         }

#     except Exception as e:
#         print("Error in process_zomato_payout:", str(e))
#         return {
#             "status": "error",
#             "message": str(e)
#         }



    
def process_zomato_sales(file_path, db_config, client_name, zomato_restaurant_id, min_date, max_date, cancelled_orders, rejected_orders, ordinary_order):
    """Process Zomato Merchant Sales Report and apply payout calculation based on order rejection status"""

    # Load Excel file
    xls = pd.ExcelFile(file_path)
    df = pd.read_excel(xls, sheet_name=0,skiprows=5,header=None)

    # Define column names
    column_names = [
        "Date", "Invoice_Date", "Client_Order_No", "Order_From", 
        "Virtual_Brand_Name", "Outlet_Display_Name", "Order_Type", 
        "Customer_Name", "Customer_Phone", "Payment_Type", "Status", 
        "Total_Amount", "Invoice_No", "Cancellation_By"
    ]

    df.columns = column_names
    df["Client_Name"] = str(client_name)
    df["fp_restaurant_id"] = str(zomato_restaurant_id)

    # Convert data types
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Invoice_Date"] = pd.to_datetime(df["Invoice_Date"], errors="coerce")
    df["Total_Amount"] = pd.to_numeric(df["Total_Amount"], errors="coerce").fillna(0)
    
    if min_date is not None and max_date is not None:
        min_date = pd.Timestamp(min_date).replace(hour=0, minute=0, second=0, microsecond=0)
        max_date = pd.Timestamp(max_date).replace(hour=23, minute=59, second=59, microsecond=999999)
        df = df[(df["Date"] >= min_date) & (df["Date"] <= max_date) & (df["Order_From"] == "Zomato")]

    # Convert cancelled orders to dictionaries for lookup
    cancelled_dict = {order["order_id"]: order["Cancelled_Rejected_State"] for order in cancelled_orders}
    # rejected_dict = {order["order_id"]: order["Cancelled_Rejected_State"] for order in rejected_orders}
    ordinary_dict = {order["order_id"]: order["Customer_Compensation_Recoupment"] for order in ordinary_order}
    rejected_dict = {
        order["order_id"]: {
            "Cancelled_Rejected_State": order["Cancelled_Rejected_State"],
            "Cancellation_Rejection_Reason": order["Cancellation_Rejection_Reason"],
            
        }
        for order in rejected_orders
    }    
    print(rejected_dict,"rejected_dict")
    print(cancelled_dict,"cancelled_dict")
    print(ordinary_dict,"ordinary_dict")
    # Initialize Expected_Payout column
    df["Expected_Payout"] = 0.0
    df["fp_status"] = "PENDING"

    client_tax = ClientDetails.objects.filter(zomato_restaurant_id=zomato_restaurant_id).first()
    commission_percentage = float(client_tax.zomato_commission_percentage) / 100
    
    payment_mechanism_charge = Aggregator.objects.filter(name="Zomato").first()
    # print(payment_mechanism_charge.payment_mechanism_fee_online,"payment_mechanism_charge")
    payment_charge_online = float(payment_mechanism_charge.payment_mechanism_fee_online)/100
    if client_tax and client_tax.zomato_tax:  
        # Process payout logic if zomato_tax exists
        for idx, row in df.iterrows():
            order_id = row["Client_Order_No"]

            if order_id in cancelled_dict:
                rejection_status = cancelled_dict[order_id]
                if rejection_status == "Order accepted":
                    df.at[idx, "Expected_Payout"] = round(row["Total_Amount"] * 0.40, 2)
                elif rejection_status == "Order picked up by rider" or rejection_status ==  "Order ready, not picked up by rider" or rejection_status ==  "Delivery partner arrived":
                    df.at[idx, "Expected_Payout"] = round(row["Total_Amount"] * 0.80, 2)
            elif order_id in rejected_dict:
                # rejected_stat = rejected_dict[order_id]
                if rejected_dict[order_id]["Cancelled_Rejected_State"] == "Delivery partner arrived":
                    df.at[idx, "Expected_Payout"] = round(-1*(row["Total_Amount"] * 0.25), 2)
                elif rejected_dict[order_id]["Cancelled_Rejected_State"]  == "Order accepted":
                    df.at[idx, "Expected_Payout"] = round(-1*(row["Total_Amount"] * 0.25), 2)
            elif order_id not in cancelled_dict and order_id not in rejected_dict and row["Status"] == "Cancelled":
                df.at[idx, "Expected_Payout"] = round(row["Total_Amount"] * 0.80, 2)
            else:
                customer_compensation_recoupment = ordinary_dict.get(order_id, 0)
                print(customer_compensation_recoupment,"customer_compensation_recoupment")
                df.at[idx, "Service_Fee"] = round(row["Total_Amount"] * commission_percentage, 2)
                df.at[idx, "Payment_Mechanism_Fee"] = round(row["Total_Amount"] * payment_charge_online, 2)
                df.at[idx, "Taxes_on_Service_Payment_Fees"] = round(
                    (df.at[idx, "Service_Fee"] + df.at[idx, "Payment_Mechanism_Fee"]) * 0.18, 2
                )
                df.at[idx, "Expected_Payout"] = round(
                    row["Total_Amount"]
                    - df.at[idx, "Service_Fee"]
                    - df.at[idx, "Payment_Mechanism_Fee"]
                    - df.at[idx, "Taxes_on_Service_Payment_Fees"]
                    - row["Total_Amount"] * 0.001
                    -customer_compensation_recoupment,
                    2,
                )
    else:
        # Alternative logic when zomato_tax does not exist
        for idx, row in df.iterrows():
            order_id = row["Client_Order_No"]

            if order_id in cancelled_dict:
                rejection_status = cancelled_dict[order_id]
                if rejection_status == "Order accepted":
                    df.at[idx, "Expected_Payout"] = round(row["Total_Amount"] * 0.40, 2)
                elif rejection_status == "Order picked up by rider":
                    df.at[idx, "Expected_Payout"] = round(row["Total_Amount"] * 0.80, 2)
            elif order_id in rejected_dict:
                rejected_stat = rejected_dict[order_id]
                if rejected_stat == "Item Out of Stock":
                    df.at[idx, "Expected_Payout"] = round(row["Total_Amount"] * 0.105, 2)
            else:
                df.at[idx, "Service_Fee"] = round(row["Total_Amount"] * commission_percentage, 2)
                df.at[idx, "Payment_Mechanism_Fee"] = round(row["Total_Amount"] * payment_charge_online, 2)
                df.at[idx, "Taxes_on_Service_Payment_Fees"] = round(
                    (df.at[idx, "Service_Fee"] + df.at[idx, "Payment_Mechanism_Fee"]) * 0.18, 2
                )
                df.at[idx, "Expected_Payout"] = round(
                    row["Total_Amount"] - df.at[idx, "Service_Fee"],
                    2,
                )

    client_name = str(client_name.client_name)

    # Convert pandas Timestamps to Python datetime
    from_date = min_date.to_pydatetime() if hasattr(min_date, "to_pydatetime") else min_date
    to_date = max_date.to_pydatetime() if hasattr(max_date, "to_pydatetime") else max_date

    # Connect to MySQL
    engine = create_engine(
        f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"
    )

    # Insert into sales_report_zomato table
    df.to_sql("sales_report", con=engine, if_exists="append", index=False)
    print(f"Inserted {len(df)} new records into sales_report.")

    with engine.connect() as conn:
        query = text(
            """
            INSERT INTO payout_reconciliation_clients_zomato (client_name, fp_restaurant_id, from_date, to_date) 
            VALUES (:client_name, :fp_restaurant_id, :from_date, :to_date)
            ON DUPLICATE KEY UPDATE from_date = VALUES(from_date), to_date = VALUES(to_date);
            """
        )

        conn.execute(
            query,
            {
                "client_name": client_name,
                "fp_restaurant_id": zomato_restaurant_id,
                "from_date": from_date,
                "to_date": to_date,
            },
        )

    engine.dispose()





def clean_column_name(column_name):
    """Clean column names: remove spaces, newlines, and special characters."""
    return column_name.strip().replace("\n", " ").replace("\r", "")


def process_swiggy_payout(file_path, client_name, db_config,swiggy_restaurant_id):
    """Process Swiggy Aggregator Payout Settlement data and avoid duplicate order_id entries"""
    
    print("Processing file...")

    # Load Excel file
    xls = pd.ExcelFile(file_path)
    df = pd.read_excel(xls, sheet_name=2, skiprows=1, header=None)
    
    # Extract CPC Ads Value
    cpc_df = pd.read_excel(xls, sheet_name=1, skiprows=27, nrows=1, usecols=lambda x: x == 5, header=None)
    cpc_value = cpc_df.iloc[0, 0] if not cpc_df.empty else None

    # Define expected column names
    if (len(df.columns.tolist()) == 49):
        column_names = [
        "order_id", "parent_order_id", "fp_order_date", "order_status", "order_category",
        "order_payment_type", "cancelled_by", "coupon_type_applied_by_customer", "item_total",
        "packaging_charges", "restaurant_discounts_promo_freebies", "swiggy_one_exclusive_offer_discount",
        "restaurant_discount_share", "net_bill_value_before_taxes", "gst_collected", "total_customer_paid",
        "commission_charged_on", "service_fees", "commission", "long_distance_charges",
        "discount_on_long_distance_fee", "pocket_hero_fees", "swiggy_one_fees", "payment_collection_charges",
        "restaurant_cancellation_charges", "call_center_charges", "delivery_fee_sponsored_by_restaurant",
        "gst_on_service_fee", "total_swiggy_fees", "customer_cancellations", "customer_complaints",
        "complaint_cancellation_charges", "gst_deduction", "tcs", "tds", "total_taxes",
        "net_payout_for_order_after_taxes", "long_distance_order", "last_mile_km", "mfr_accurate",
        "mfr_pressed", "coupon_code_sourced", "discount_campaign_id", "replicated_order",
        "base_order_id", "cancellation_time", "pick_up_status", "swiggy_one_customer",
        "pocket_hero_order"
        ]
    elif(len(df.columns.tolist()) == 50):
        column_names = [
        "order_id", "parent_order_id", "fp_order_date", "order_status", "order_category",
        "order_payment_type", "cancelled_by", "coupon_type_applied_by_customer", "item_total",
        "packaging_charges", "restaurant_discounts_promo_freebies", "swiggy_one_exclusive_offer_discount",
        "restaurant_discount_share", "net_bill_value_before_taxes", "gst_collected", "total_customer_paid",
        "commission_charged_on", "service_fees", "commission", "long_distance_charges",
        "discount_on_long_distance_fee", "pocket_hero_fees", "swiggy_one_fees", "payment_collection_charges",
        "restaurant_cancellation_charges", "call_center_charges", "delivery_fee_sponsored_by_restaurant","Bolt_Fees",
        "gst_on_service_fee", "total_swiggy_fees", "customer_cancellations", "customer_complaints",
        "complaint_cancellation_charges", "gst_deduction", "tcs", "tds", "total_taxes",
        "net_payout_for_order_after_taxes", "long_distance_order", "last_mile_km", "mfr_accurate",
        "mfr_pressed", "coupon_code_sourced", "discount_campaign_id", "replicated_order",
        "base_order_id", "cancellation_time", "pick_up_status", "swiggy_one_customer",
        "pocket_hero_order"
        ]

    file_columns = df.columns.tolist()

    print("file_columns",df.columns.tolist())
    # Print column count info
    print(f"Number of columns in DataFrame: {df.shape[1]}")
    print(f"Expected number of columns: {len(column_names)}")

    # if len(column_names) > df.shape[1]:
    #     column_names = column_names[:df.shape[1]]
    
    # Assign column names
    while len(column_names) < df.shape[1]:  
        column_names.append(f"extra_col_{len(column_names) + 1}")  # Assign generic names to extra columns
    
    df.columns = column_names

    # Add client name and format columns
    df["fp_client_name"] = str(client_name)
    df["fp_order_date"] = pd.to_datetime(df["fp_order_date"], errors="coerce")
    df["order_id"] = pd.to_numeric(df["order_id"], errors="coerce").fillna(0).astype(int)
    df["fp_restaurant_id"] = str(swiggy_restaurant_id)
    # Fetch min/max order dates from the SwiggyOrder table
    min_date = df["fp_order_date"].min().replace(hour=0, minute=0, second=0, microsecond=0)
    max_date = df["fp_order_date"].max().replace(hour=23, minute=59, second=59, microsecond=999999)
    print("Unique order statuses:", df["order_status"].unique())  
    print("Cancelled orders count:", df[df["order_status"] == "cancelled"].shape[0])  
    print("Cancelled orders sample:\n", df[df["order_status"] == "cancelled"].head())  
    cancelled_orders = df[df["order_status"] == "cancelled"][
    ["order_id", "cancelled_by", "mfr_accurate", "mfr_pressed","order_payment_type","pick_up_status"]
                    ].to_dict(orient="records")
    ordinary_order = df[df["order_status"] == "delivered"][["order_id", "customer_complaints"]].to_dict(orient="records")

    print("cancelled_dict555",cancelled_orders)

    # Connect to MySQL
    engine = create_engine(f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}")

    with engine.connect() as conn:
        # Get existing columns in the SwiggyOrder table
        table_check_query = text(f"""
            SELECT COLUMN_NAME 
            FROM information_schema.columns 
            WHERE table_schema = '{db_config['database']}' 
            AND table_name = 'SwiggyOrder'
        """)
        
        existing_columns = pd.read_sql(table_check_query, conn)["COLUMN_NAME"].tolist()

        # Identify new columns that need to be added
        new_columns = [col for col in column_names if col not in existing_columns]

        # Identify missing columns (expected columns that don't exist in the DB)
        missing_columns = [col for col in existing_columns if col not in column_names]

        # Add missing columns
        if new_columns:
            print(f"Adding new columns: {new_columns}")
            for col in new_columns:
        # Double-check again before adding (avoid race conditions)
                table_check_query = text(f"""
            SELECT COLUMN_NAME 
            FROM information_schema.columns 
            WHERE table_schema = '{db_config['database']}' 
            AND table_name = 'SwiggyOrder'
            AND COLUMN_NAME = '{col}'
        """)
        
        result = conn.execute(table_check_query).fetchall()
        
        if not result:  #  Ensure the column truly doesn't exist before adding
            alter_query = text(f"ALTER TABLE SwiggyOrder ADD COLUMN `{col}` VARCHAR(255) DEFAULT NULL;")
            conn.execute(alter_query)
            conn.commit()
            print(f"Added column: {col}")
        else:
            print(f"Column '{col}' already exists, skipping.")

                

        # Fetch min/max order dates from the SwiggyOrder table
        
        
        # Fetch existing order IDs from DB to avoid duplicates
        existing_order_ids_query = text("SELECT order_id FROM SwiggyOrder")
        existing_order_ids = pd.read_sql(existing_order_ids_query, conn)
        existing_order_ids_set = set(existing_order_ids["order_id"].dropna().astype(int)) if not existing_order_ids.empty else set()

        
        # Remove duplicates
        df = df[~df["order_id"].isin(existing_order_ids_set)]

        if not df.empty:
            df.to_sql("SwiggyOrder", con=engine, if_exists="append", index=False)
            print(f" Inserted {len(df)} new records into SwiggyOrder.")
        else:
            print(" No new records inserted (all orders already exist).")
        
        
        client_name = str(client_name)
        min_date = min_date.to_pydatetime()
        max_date = max_date.to_pydatetime()
        
        # Insert CPC Ads Data
        cpc_insert_query = text("""
            INSERT INTO payout_reconciliation_swiggy_cpc_ads (from_date, to_date, fp_restaurant_id, client_name, cpc_value)
            SELECT :from_date, :to_date, :fp_restaurant_id, :client_name, :cpc_value
            FROM DUAL
            WHERE NOT EXISTS (
                SELECT 1 FROM payout_reconciliation_swiggy_cpc_ads
                WHERE from_date = :from_date
                AND to_date = :to_date
                AND fp_restaurant_id = :fp_restaurant_id
                AND client_name = :client_name
            )
        """)
        conn.execute(cpc_insert_query, {
            "from_date": min_date,
            "to_date": max_date,
            "fp_restaurant_id": swiggy_restaurant_id,
            "client_name": client_name,
            "cpc_value": float(cpc_value)
        })
        conn.commit()
        print("Inserted CPC Ads data.")

        
    engine.dispose()
   

    return {
        "status": "success",
        "message": "File processed successfully.",
        "newly_added_columns": new_columns,
        "missing_columns": missing_columns,
        "min_date": min_date,
        "max_date": max_date,
        "cancelled_orders":cancelled_orders,
        "ordinary_order":ordinary_order
        
    }

def process_swiggy_sales(file_path, client_name,min_date,max_date,swiggy_restaurant_id,cancelled_orders,ordinary_order):
    """Process Swiggy Merchant Sales Report and avoid duplicate Client_Order_No entries"""

    print(f" Processing file for client: {client_name}")

    # Load Excel file
    try:
        xls = pd.ExcelFile(file_path)
        df = pd.read_excel(xls, sheet_name=0,skiprows=5,header=None)
    except Exception as e:
        print(f" Error reading Excel file: {e}")
        return

    # Standard column names
    expected_columns = [
        "Date", "Invoice_Date", "Client_Order_No", "Order_From", 
        "Virtual_Brand_Name", "Outlet_Display_Name", "Order_Type", 
        "Customer_Name", "Customer_Phone", "Payment_Type", "Status", 
        "Total_Amount", "Invoice_No", "Cancellation_By"
    ]

    # Check for missing columns
    # missing_columns = [col for col in expected_columns if col not in df.columns]
    # if missing_columns:
    #     print(f" Missing columns: {missing_columns}")
    #     return

    # Rename columns properly
    df.columns = expected_columns

    # Add client info
    df["fp_Client_Name"] = str(getattr(client_name, "client_name", client_name))
    df["fp_restaurant_id"] = str(swiggy_restaurant_id)

    # Convert date columns
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Invoice_Date"] = pd.to_datetime(df["Invoice_Date"], errors="coerce")

    # Drop invalid dates before filtering
    df = df.dropna(subset=["Date"])

    # Convert numeric fields
    df["Total_Amount"] = pd.to_numeric(df["Total_Amount"], errors="coerce").fillna(0)

    # Date range filtering
    if min_date and max_date:
        min_date = pd.Timestamp(min_date).replace(hour=0, minute=0, second=0)
        max_date = pd.Timestamp(max_date).replace(hour=23, minute=59, second=59)
        df = df[(df["Date"] >= min_date) & (df["Date"] <= max_date) & (df["Order_From"] == "Swiggy")]

    
    cancelled_dict = {
        order["order_id"]: {
            "cancelled_by": order["cancelled_by"],
            "mfr_accurate": order["mfr_accurate"],
            "mfr_pressed": order["mfr_pressed"],
            "order_payment_type":order["order_payment_type"],
            "pick_up_status":order["pick_up_status"]
        }
        for order in cancelled_orders
    }       
    ordinary_dict = {order["order_id"]: order["customer_complaints"] for order in ordinary_order}

    print("cancelled_dict",cancelled_dict)
    
    # Fetch client commission details
    client_tax = ClientDetails.objects.filter(client_name=client_name).first()
    commission_percentage = float(client_tax.swiggy_commission_percentage) / 100
    payment_mechanism_charge = Aggregator.objects.filter(name="Swiggy").first()
    # print(payment_mechanism_charge.payment_mechanism_fee_online,"payment_mechanism_charge")
    payment_charge_online = float(payment_mechanism_charge.payment_mechanism_fee_online)/100
    payment_charge_cod = float(payment_mechanism_charge.payment_mechanism_fee)/100
    
    
    if client_tax.swiggy_tax:
        for index, row in df.iterrows():
            order_id = row["Client_Order_No"]
            # Apply additional conditions for cancelled orders
            if order_id in cancelled_dict:
                cancelled_by = cancelled_dict[order_id]
                if order_id in cancelled_dict and cancelled_dict[order_id]["cancelled_by"] == "MERCHANT":
                    df.at[index, "Net_Bill"] = 0
                    df.at[index, "Net_Bill_GST"] = 0
                    df.at[index, "Service_Fee"] =0
                    df.at[index, "Payment_Mechanism_Fee"] = 0                    
                    tax_on_service_payment_fees = round((row["Total_Amount"] * 0.105) * 0.18, 2)
                    df.at[index, "Taxes_on_Service_Payment_Fees"] = tax_on_service_payment_fees
                    df.at[index, "Expected_Payout"] = round(-1 * (tax_on_service_payment_fees + (row["Total_Amount"] * 0.105)), 2)

                elif order_id in cancelled_dict and cancelled_dict[order_id]["cancelled_by"] == "SWIGGY" :

                    if order_id in cancelled_dict and cancelled_dict[order_id]["mfr_accurate"] == "Yes" and cancelled_dict[order_id]["mfr_pressed"] == "Yes":
                        print("test666",order_id in cancelled_dict and cancelled_dict[order_id]["order_payment_type"] == "cash")
                        if order_id in cancelled_dict and cancelled_dict[order_id]["order_payment_type"] == "cash":
                            df.at[index, "Net_Bill"] = round(row["Total_Amount"] * 0.80, 2)
                            df.at[index, "Net_Bill_GST"] =round((df.at[index, "Net_Bill"]*0.05) , 2)
                            df.at[index, "Service_Fee"] = round(df.at[index, "Net_Bill"]  * commission_percentage, 2)
                            df.at[index, "Payment_Mechanism_Fee"] = round(df.at[index, "Net_Bill"] * payment_charge_online, 2)
                            df.at[index, "Taxes_on_Service_Payment_Fees"] = round((df.at[index, "Service_Fee"] + df.at[index, "Payment_Mechanism_Fee"]) * 0.18, 2)

                            df.at[index, "Expected_Payout"] = round(df.at[index, "Net_Bill"]  - (
                            df.at[index, "Net_Bill_GST"] + df.at[index, "Service_Fee"] +
                            df.at[index, "Payment_Mechanism_Fee"] + df.at[index, "Taxes_on_Service_Payment_Fees"] +
                            row["Total_Amount"] * 0.001
                            ), 2)
                        else:
                            df.at[index, "Net_Bill"] = round(row["Total_Amount"] * 0.80, 2)
                            df.at[index, "Net_Bill_GST"] = round((df.at[index, "Net_Bill"]*0.05) , 2)
                            df.at[index, "Service_Fee"] = round(df.at[index, "Net_Bill"] * commission_percentage, 2)
                            df.at[index, "Payment_Mechanism_Fee"] = round(df.at[index, "Net_Bill"]  * payment_charge_online, 2)
                            df.at[index, "Taxes_on_Service_Payment_Fees"] = round((df.at[index, "Service_Fee"] + df.at[index, "Payment_Mechanism_Fee"]) * 0.18, 2)

                            df.at[index, "Expected_Payout"] = round(df.at[index, "Net_Bill"]  - (
                            df.at[index, "Net_Bill_GST"] + df.at[index, "Service_Fee"] +
                            df.at[index, "Payment_Mechanism_Fee"] + df.at[index, "Taxes_on_Service_Payment_Fees"] +
                            row["Total_Amount"] * 0.001
                            ), 2)
                            
                    elif order_id in cancelled_dict and cancelled_dict[order_id]["mfr_accurate"] == "Yes" and cancelled_dict[order_id]["mfr_pressed"] == "No":
                        print("test666",order_id in cancelled_dict and cancelled_dict[order_id]["order_payment_type"] == "cash")
                        if order_id in cancelled_dict and cancelled_dict[order_id]["order_payment_type"] == "cash":
                            df.at[index, "Net_Bill"] = round(row["Total_Amount"] * 0.40, 2)
                            df.at[index, "Net_Bill_GST"] =0
                            df.at[index, "Service_Fee"] = 0
                            df.at[index, "Payment_Mechanism_Fee"] = 0
                            df.at[index, "Taxes_on_Service_Payment_Fees"] = 0

                            df.at[index, "Expected_Payout"] = round(df.at[index, "Net_Bill"]  - (
                            df.at[index, "Net_Bill_GST"] + df.at[index, "Service_Fee"] +
                            df.at[index, "Payment_Mechanism_Fee"] + df.at[index, "Taxes_on_Service_Payment_Fees"]
                            ), 2)
                        else:
                            df.at[index, "Net_Bill"] = round(row["Total_Amount"] * 0.40, 2)
                            df.at[index, "Net_Bill_GST"] = 0
                            df.at[index, "Service_Fee"] = 0
                            df.at[index, "Payment_Mechanism_Fee"] = 0
                            df.at[index, "Taxes_on_Service_Payment_Fees"] = 0

                            df.at[index, "Expected_Payout"] = round(df.at[index, "Net_Bill"] - ( 
                            df.at[index, "Net_Bill_GST"] + df.at[index, "Service_Fee"] +
                            df.at[index, "Payment_Mechanism_Fee"] + df.at[index, "Taxes_on_Service_Payment_Fees"] +
                            0
                            ), 2)
                            
                        

                elif order_id in cancelled_dict and cancelled_dict[order_id]["cancelled_by"] == "CUSTOMER":
                    if order_id in cancelled_dict and cancelled_dict[order_id]["mfr_accurate"] == "Yes" and cancelled_dict[order_id]["mfr_pressed"] == "No":
                        df.at[index, "Net_Bill"] = round(row["Total_Amount"] * 0.40, 2)
                        df.at[index, "Net_Bill_GST"] = 0
                        df.at[index, "Service_Fee"] =0
                        df.at[index, "Payment_Mechanism_Fee"] = 0
                        df.at[index, "Taxes_on_Service_Payment_Fees"] = 0
                        df.at[index, "Expected_Payout"] = round((row["Total_Amount"] * 0.40 )-df.at[index, "Net_Bill_GST"], 2)
                        

                    elif order_id in cancelled_dict and cancelled_dict[order_id]["mfr_accurate"] == "Yes" and cancelled_dict[order_id]["mfr_pressed"] == "Yes" and cancelled_dict[order_id]["order_payment_type"] == "prepaid'":
                        df.at[index, "Net_Bill"] = round(row["Total_Amount"] * 0.80, 2)
                        df.at[index, "Net_Bill_GST"] = round((df.at[index, "Net_Bill"]*0.05) , 2)
                        df.at[index, "Service_Fee"] = round(df.at[index, "Net_Bill"]  * commission_percentage, 2)
                        df.at[index, "Payment_Mechanism_Fee"] = round(df.at[index, "Net_Bill"] * payment_charge_online, 2)
                        df.at[index, "Taxes_on_Service_Payment_Fees"] = round((df.at[index, "Service_Fee"] + df.at[index, "Payment_Mechanism_Fee"]) * 0.18, 2)

                        df.at[index, "Expected_Payout"] = round(df.at[index, "Net_Bill"]  - (
                        df.at[index, "Net_Bill_GST"] + df.at[index, "Service_Fee"] +
                        df.at[index, "Payment_Mechanism_Fee"] + df.at[index, "Taxes_on_Service_Payment_Fees"] +
                        row["Total_Amount"] * 0.001
                        ), 2)
                    elif order_id in cancelled_dict and cancelled_dict[order_id]["mfr_accurate"] == "Yes" and cancelled_dict[order_id]["mfr_pressed"] == "Yes" and cancelled_dict[order_id]["pick_up_status"] == "picked up":
                        df.at[index, "Net_Bill"] = round(row["Total_Amount"] - (row["Total_Amount"] * 0.05), 2)
                        df.at[index, "Net_Bill_GST"] = round(df.at[index, "Net_Bill"] * 0.05, 2)
                        df.at[index, "Service_Fee"] = round(row["Total_Amount"] * commission_percentage, 2)
                        df.at[index, "Payment_Mechanism_Fee"] = round(row["Total_Amount"] * payment_charge_online, 2)
                        df.at[index, "Taxes_on_Service_Payment_Fees"] = round((df.at[index, "Service_Fee"] + df.at[index, "Payment_Mechanism_Fee"]) * 0.18, 2)

                    # Default Expected Payout Calculation
                        df.at[index, "Expected_Payout"] = round(row["Total_Amount"] - (
                        df.at[index, "Net_Bill_GST"] + df.at[index, "Service_Fee"] + 
                        df.at[index, "Payment_Mechanism_Fee"] + df.at[index, "Taxes_on_Service_Payment_Fees"] + 
                            row["Total_Amount"] * 0.001 + customer_complaints_Charge
                                    ), 2)
                        
                    elif order_id in cancelled_dict and cancelled_dict[order_id]["mfr_accurate"] == "Yes" and cancelled_dict[order_id]["mfr_pressed"] == "Yes" and cancelled_dict[order_id]["order_payment_type"] == "cash":
                        print("test000",order_id in cancelled_dict and cancelled_dict[order_id]["order_payment_type"] == "cash")

                        df.at[index, "Net_Bill"] = round(row["Total_Amount"] * 0.80, 2)
                        df.at[index, "Net_Bill_GST"] =round((df.at[index, "Net_Bill"]*0.05) , 2)
                        df.at[index, "Service_Fee"] = round(df.at[index, "Net_Bill"]  * commission_percentage, 2)
                        df.at[index, "Payment_Mechanism_Fee"] = round(df.at[index, "Net_Bill"]  * payment_charge_cod, 2)
                        df.at[index, "Taxes_on_Service_Payment_Fees"] = round((df.at[index, "Service_Fee"] + df.at[index, "Payment_Mechanism_Fee"]) * 0.18, 2)

                        df.at[index, "Expected_Payout"] = round(df.at[index, "Net_Bill"]  - (
                        df.at[index, "Net_Bill_GST"] + df.at[index, "Service_Fee"] +
                        df.at[index, "Payment_Mechanism_Fee"] + df.at[index, "Taxes_on_Service_Payment_Fees"] +
                        row["Total_Amount"] * 0.001
                        ), 2)
            
            elif order_id not in cancelled_dict and row["Status"] == "Cancelled":
                df.at[index, "Expected_Payout"] = round(row["Total_Amount"] * 0.80, 2)
                    
            else:
                customer_complaints_Charge = ordinary_dict.get(order_id, 0)
                print(customer_complaints_Charge,"customer_complaints_Charge")
                df.at[index, "Net_Bill"] = round(row["Total_Amount"] - (row["Total_Amount"] * 0.05), 2)
                df.at[index, "Net_Bill_GST"] = round(df.at[index, "Net_Bill"] * 0.05, 2)
                df.at[index, "Service_Fee"] = round(row["Total_Amount"] * commission_percentage, 2)
                df.at[index, "Payment_Mechanism_Fee"] = round(row["Total_Amount"] * payment_charge_online, 2)
                df.at[index, "Taxes_on_Service_Payment_Fees"] = round((df.at[index, "Service_Fee"] + df.at[index, "Payment_Mechanism_Fee"]) * 0.18, 2)

            # Default Expected Payout Calculation
                df.at[index, "Expected_Payout"] = round(row["Total_Amount"] - (
                    df.at[index, "Net_Bill_GST"] + df.at[index, "Service_Fee"] + 
                    df.at[index, "Payment_Mechanism_Fee"] + df.at[index, "Taxes_on_Service_Payment_Fees"] + 
                row["Total_Amount"] * 0.001 + customer_complaints_Charge
                ), 2)

    else:
        for index, row in df.iterrows():
            df.at[index, "Service_Fee"] = round(row["Total_Amount"] * commission_percentage, 2)
            df.at[index, "Expected_Payout"] = round(row["Total_Amount"] - df.at[index, "Service_Fee"], 2)

    


    # Connect to MySQL
    engine = create_engine(f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}")

    # Ensure 'fp_Client_Name' exists in MySQL
    with engine.connect() as conn:
        result = conn.execute(text("SHOW COLUMNS FROM sales_report_swiggy;"))
        table_columns = [row[0] for row in result]
        if "fp_Client_Name" not in table_columns:
            conn.execute(text("ALTER TABLE sales_report_swiggy ADD COLUMN fp_Client_Name VARCHAR(255);"))

    # Fetch existing orders for the given date range
    existing_orders = pd.read_sql(f"SELECT Client_Order_No FROM sales_report_swiggy WHERE Date BETWEEN '{min_date}' AND '{max_date}'", con=engine)
    existing_orders_set = set(existing_orders["Client_Order_No"].astype(str))

    # Filter out duplicates
    df_filtered = df[~df["Client_Order_No"].astype(str).isin(existing_orders_set)]
    if not df_filtered.empty:
        df_filtered.to_sql("sales_report_swiggy", con=engine, if_exists="append", index=False)
        print(f" Inserted {len(df_filtered)} new records.")
    else:
        print(" No new records to insert.")

    
    
    client_name = str(client_name.client_name)

    # Convert pandas Timestamps to Python datetime
    from_date = min_date.to_pydatetime() if hasattr(min_date, "to_pydatetime") else min_date
    to_date = max_date.to_pydatetime() if hasattr(max_date, "to_pydatetime") else max_date
    # Update reconciliation table
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO payout_reconciliation_clients_swiggy (client_name, fp_restaurant_id, from_date, to_date) 
            VALUES (:client_name, :fp_restaurant_id, :from_date, :to_date)
            ON DUPLICATE KEY UPDATE from_date = VALUES(from_date), to_date = VALUES(to_date);
        """), {"client_name": client_name, "fp_restaurant_id": swiggy_restaurant_id, "from_date": from_date, "to_date": to_date})

    engine.dispose()



def aggregator_list(request):
    aggregators = Aggregator.objects.filter(delflag=1)  # Fetch active aggregators

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
        # AJAX request for fetching aggregators
        data = list(aggregators.values("id", "name", "email", "payment_frequency","payment_mechanism_fee","payment_mechanism_fee_online"))
        return JsonResponse({"aggregators": data})

    if request.method == "POST":
        form = AggregatorForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True, "message": "Aggregator added successfully!"})
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    form = AggregatorForm()
    return render(request, 'aggregator_list.html', {'form': form, 'aggregators': aggregators})


def aggregator_add(request):
    if request.method == "POST":
        form = AggregatorForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True, "message": "Aggregator added successfully!"})
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)


def aggregator_edit(request, pk):
    aggregator = get_object_or_404(Aggregator, pk=pk)

    if request.method == "POST":
        form = AggregatorForm(request.POST, instance=aggregator)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True, "message": "Aggregator updated successfully!"})
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Returning JSON response for AJAX GET request
        form_data = {
            "name": aggregator.name,
            "email": aggregator.email,
            "payment_frequency": aggregator.payment_frequency,
            "payment_mechanism_fee":aggregator.payment_mechanism_fee,
            "payment_mechanism_fee_online":aggregator.payment_mechanism_fee_online
        }
        return JsonResponse(form_data)

    # Default (fallback) for non-AJAX requests
    form = AggregatorForm(instance=aggregator)
    return render(request, 'aggregator_edit.html', {'form': form, 'aggregator': aggregator})



# @csrf_exempt  # Remove this in production; use CSRF tokens in AJAX
def aggregator_delete(request, pk):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method!"})
    
    aggregator = get_object_or_404(Aggregator, pk=pk)
    aggregator.delflag = 0  # Soft delete
    aggregator.save()
    
    return JsonResponse({"success": True, "message": "Aggregator deleted successfully!"})




def membership_list(request):
    memberships = Membership.objects.filter(delflag=1)
    form = MembershipForm()
    return render(request, 'membership_list.html', {'memberships': memberships, 'form': form})



def membership_add(request):
    if request.method == 'POST':
        form = MembershipForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Membership added successfully!'})
        return JsonResponse({'success': False, 'message': 'Invalid data!'})
    
    
    
def membership_edit(request, pk):
    membership = get_object_or_404(Membership, pk=pk, delflag=1)
    
    if request.method == 'POST':
        form = MembershipForm(request.POST, instance=membership)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Membership updated successfully!'})
        return JsonResponse({'success': False, 'message': 'Invalid data!'})

    return JsonResponse({'success': False, 'message': 'Invalid request!'})




def membership_delete(request, pk):
    membership = get_object_or_404(Membership, pk=pk)
    
    if request.method == 'POST':
        membership.delflag = 0  # Soft delete
        membership.save()
        return JsonResponse({'success': True, 'message': 'Membership deleted successfully!'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request!'})



def get_restaurant_ids(request):
    client_id = request.GET.get('client_id')
    restaurants = ClientDetails.objects.filter(id=client_id).values_list('zomato_restaurant_id', flat=True)
    return JsonResponse({'restaurants': list(restaurants)})



def get_dates_for_restaurant(request):
    restaurant_id = request.GET.get("restaurant_id")

    if restaurant_id:
        date_ranges = clients_zomato.objects.filter(fp_restaurant_id=restaurant_id).values_list("from_date", "to_date")

        formatted_dates = [
            f"{from_date.strftime('%d-%b-%Y')} to {to_date.strftime('%d-%b-%Y')}"
            for from_date, to_date in date_ranges
        ]

        return JsonResponse({"dates": formatted_dates})

    return JsonResponse({"dates": []})

def get_restaurants_for_client(request):
    client_name = request.GET.get("client_name")

    if client_name:
        # Fetch unique restaurant IDs for the given client
        restaurants = clients_zomato.objects.filter(client_name=client_name).values("fp_restaurant_id").distinct()

        restaurant_list = [{"id": r["fp_restaurant_id"], "name": f"Restaurant {r['fp_restaurant_id']}"} for r in restaurants]

        return JsonResponse({"restaurants": restaurant_list})

    return JsonResponse({"restaurants": []})



def get_swiggy_restaurant_id(request):
    client_id = request.GET.get('client_id')
    restaurants = ClientDetails.objects.filter(id=client_id).values_list('swiggy_restaurant_id', flat=True)
    return JsonResponse({"restaurants": list(restaurants)})


def get_swiggy_dates_for_restaurant(request):
    restaurant_id = request.GET.get("restaurant_id")

    if restaurant_id:
        date_ranges = clients_swiggy.objects.filter(fp_restaurant_id=restaurant_id).values_list("from_date", "to_date")

        formatted_dates = [
            f"{from_date.strftime('%d-%b-%Y')} to {to_date.strftime('%d-%b-%Y')}"
            for from_date, to_date in date_ranges
        ]

        return JsonResponse({"dates": formatted_dates})

    return JsonResponse({"dates": []})


def get_swiggy_restaurants_for_client(request):
    client_name = request.GET.get("client_name")

    if client_name:
        # Fetch unique restaurant IDs for the given client
        restaurants = clients_swiggy.objects.filter(client_name=client_name).values("fp_restaurant_id").distinct()

        restaurant_list = [{"id": r["fp_restaurant_id"], "name": f"Restaurant {r['fp_restaurant_id']}"} for r in restaurants]

        return JsonResponse({"restaurants": restaurant_list})

    return JsonResponse({"restaurants": []})



@csrf_exempt
def update_reconciliation_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            new_status = data.get('reconciliation_status')
            aggregator = data.get('aggregator')
            restaurant_id = data.get('restaurant_id')
            print(new_status,"new_statue")
            print(order_id,"order_id")
            print(aggregator,"aggregator")


            # Update the correct row in sales_report
            # Raw SQL Update
            if aggregator == "Zomato":
                with connection.cursor() as cursor:
                    cursor.execute("""
                    UPDATE sales_report
                    SET fp_status = %s
                    WHERE Client_Order_No = %s
                """, [new_status, order_id])
            if aggregator == "Swiggy":
                with connection.cursor() as cursor:
                    cursor.execute("""
                    UPDATE sales_report_swiggy
                    SET fp_status = %s
                    WHERE Client_Order_No = %s
                """, [new_status, order_id])
                    
            latest_log = SummeryLog.objects.filter(order_id=order_id, aggregator=aggregator).last()

            if latest_log:
                # Create new entry with updated fp_status
                SummeryLog.objects.create(
                    restaurant_id=latest_log.restaurant_id,
                    aggregator=latest_log.aggregator,
                    order_id=latest_log.order_id,
                    wrong_payout_settled=latest_log.wrong_payout_settled,
                    wrong_taxes_on_service_payment_fees=latest_log.wrong_taxes_on_service_payment_fees,
                    wrong_payment_mechanism_fee=latest_log.wrong_payment_mechanism_fee,
                    wrong_service_fee=latest_log.wrong_service_fee,
                    cancelled_order_amount_deducted_wrongly=latest_log.cancelled_order_amount_deducted_wrongly,
                    TDS_issue=latest_log.TDS_issue,
                    Wrong_penalty=latest_log.Wrong_penalty,
                    fp_order_date=latest_log.fp_order_date,
                    fp_status=new_status,
                    missing_order_with=latest_log.missing_order_with
                )

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


def update_sales_status_proc(restaurant_id, start_date, end_date):
    print("HIIIII")
    with connection.cursor() as cursor:
        print("HIIIII")
        cursor.callproc("UpdateSalesStatusByRestaurant", [restaurant_id, start_date, end_date])
def update_sales_status_proc_swiggy(restaurant_id, start_date, end_date):
    print("HIIIII")
    with connection.cursor() as cursor:
        print("HIIIII")
        cursor.callproc("UpdateSalesStatusByRestaurant_swiggy", [restaurant_id, start_date, end_date])

def update_sales_status_proc_dispute_in_clar(restaurant_id, start_date, end_date):
    print("DISPUTE IN CLar in zo")
    # print("HIIIII")
    with connection.cursor() as cursor:
        # print("HIIIII")
        print("DISPUTE IN CLar in zo")
        cursor.callproc("update_sales_status_proc_dispute_in_clar", [restaurant_id, start_date, end_date])
def update_sales_status_proc_dispute_in_clar_swiggy(restaurant_id, start_date, end_date):
    # print("HIIIII")
    with connection.cursor() as cursor:
        # print("HIIIII")
        print("DISPUTE IN CLar in zo")
        cursor.callproc("update_sales_status_proc_dispute_in_clar_swiggy", [restaurant_id, start_date, end_date])


def get_sent_email(request):
    print("get_sent_email in")
    aggregator = request.GET.get("aggregator")
    restaurant_id = request.GET.get("restaurant_id")
    date_range = request.GET.get("selected_date_range")
    print(date_range,"report_data.selected_date_range")
    print(restaurant_id,"restaurant_id")

    email_log = SentEmailLog.objects.filter(
        aggregator=aggregator,
        restaurant_id=restaurant_id,
        date_range=date_range
    ).order_by("-timestamp").first()

    if email_log:
        return JsonResponse({
            "subject": email_log.subject,
            "body": email_log.body,
            "to": email_log.recipients,
            "recipients": email_log.recipients,
            "cc": email_log.cc,
            "timestamp": email_log.timestamp.strftime("%d-%b-%Y %H:%M")
        })
    else:
        return JsonResponse({"message": "No email found!"}, status=404)


def add_dispute_raised(aggregator, restaurant_id, date_range):
    start_date_str, end_date_str = date_range.split(" to ")
    start_date = datetime.strptime(start_date_str.strip(), "%d-%b-%Y").date()
    end_date = datetime.strptime(end_date_str.strip(), "%d-%b-%Y").date()

    print(start_date,"add_dipute")

    print("add_dispute_raised")

    # fp_order_date__range=(start_date, end_date)
    # Get entries with fp_status="Pending" for the given range
    pending_entries = SummeryLog.objects.filter(
        aggregator=aggregator,
        restaurant_id=restaurant_id,
        fp_status="PENDING",
        fp_order_date__date__range=(start_date, end_date)
        
    )
    print("GOKUL",pending_entries,"GOKUL")

    for pending in pending_entries:
        # Check if Dispute Raised already exists for the same order_id
        already_exists = SummeryLog.objects.filter(
            order_id=pending.order_id,
            aggregator=aggregator,
            restaurant_id=restaurant_id,
            fp_status="Dispute Raised"
        ).exists()
        already_exists_1 = SummeryLog.objects.filter(
            order_id=pending.order_id,
            aggregator=aggregator,
            restaurant_id=restaurant_id,
            fp_status="Dispute Raised"
        )
        # print(already_exists,"already_exists000")
        print(already_exists_1,"already_exists111")

        if not already_exists:
            SummeryLog.objects.create(
                order_id=pending.order_id,
                aggregator=aggregator,
                restaurant_id=restaurant_id,
                fp_status="Dispute Raised",
                fp_order_date=pending.fp_order_date,
                wrong_payout_settled=pending.wrong_payout_settled,
                wrong_taxes_on_service_payment_fees=pending.wrong_taxes_on_service_payment_fees,
                wrong_payment_mechanism_fee=pending.wrong_payment_mechanism_fee,
                wrong_service_fee=pending.wrong_service_fee,
                cancelled_order_amount_deducted_wrongly=pending.cancelled_order_amount_deducted_wrongly,
                TDS_issue=pending.TDS_issue,
                Wrong_penalty=pending.Wrong_penalty,
                missing_order_with=pending.missing_order_with,
            )
def add_dispute_in_clarification(aggregator, restaurant_id, date_range):
    start_date_str, end_date_str = date_range.split(" to ")
    start_date = datetime.strptime(start_date_str.strip(), "%d-%b-%Y").date()
    end_date = datetime.strptime(end_date_str.strip(), "%d-%b-%Y").date()

    print(start_date,"add_dipute")

    print("add_dispute_raised")

    # fp_order_date__range=(start_date, end_date)
    # Get entries with fp_status="Pending" for the given range
    pending_entries = SummeryLog.objects.filter(
        aggregator=aggregator,
        restaurant_id=restaurant_id,
        fp_status="Dispute Raised",
        fp_order_date__date__range=(start_date, end_date)
        
    )
    print("GOKUL",pending_entries,"GOKUL")

    for pending in pending_entries:
        # Check if Dispute Raised already exists for the same order_id
        already_exists = SummeryLog.objects.filter(
            order_id=pending.order_id,
            aggregator=aggregator,
            restaurant_id=restaurant_id,
            fp_status="Dispute in Clarification"
        ).exists()
        already_exists_1 = SummeryLog.objects.filter(
            order_id=pending.order_id,
            aggregator=aggregator,
            restaurant_id=restaurant_id,
            fp_status="Dispute in Clarification"
        )
        # print(already_exists,"already_exists000")
        print(already_exists_1,"already_exists111")

        if not already_exists:
            SummeryLog.objects.create(
                order_id=pending.order_id,
                aggregator=aggregator,
                restaurant_id=restaurant_id,
                fp_status="Dispute in Clarification",
                fp_order_date=pending.fp_order_date,
                wrong_payout_settled=pending.wrong_payout_settled,
                wrong_taxes_on_service_payment_fees=pending.wrong_taxes_on_service_payment_fees,
                wrong_payment_mechanism_fee=pending.wrong_payment_mechanism_fee,
                wrong_service_fee=pending.wrong_service_fee,
                cancelled_order_amount_deducted_wrongly=pending.cancelled_order_amount_deducted_wrongly,
                TDS_issue=pending.TDS_issue,
                Wrong_penalty=pending.Wrong_penalty,
                missing_order_with=pending.missing_order_with,
            )


def log_page(request):
    return render(request, 'log_page.html')



@csrf_exempt
def get_summery_logs(request):
    if request.method == "POST":
        data = json.loads(request.body)
        restaurant_id = data.get("restaurant_id")
        aggregator = data.get("aggregator")
        from_date = parse_date(data.get("from_date")) if data.get("from_date") else None
        to_date = parse_date(data.get("to_date")) if data.get("to_date") else None
        search = data.get("search", "").lower()
        print(from_date,to_date,"Freom and To")

        logs = SummeryLog.objects.all()

        if restaurant_id:
            logs = logs.filter(restaurant_id=restaurant_id)
        if aggregator:
            logs = logs.filter(aggregator=aggregator)
        if from_date and to_date:
            logs = logs.filter(fp_order_date__range=(from_date, to_date))
        if search:
            logs = logs.filter(
                Q(order_id__icontains=search) |
                Q(fp_status__icontains=search)
            )

        issue_rows = []
        for log in logs.order_by("-fp_order_date"):
            issues = {
                "Wrong Payout Settled": log.wrong_payout_settled,
                "Wrong Taxes on Service Payment Fees": log.wrong_taxes_on_service_payment_fees,
                "Wrong Payment Mechanism Fee": log.wrong_payment_mechanism_fee,
                "Wrong Service Fee": log.wrong_service_fee,
                "Cancelled Order Amount Deducted Wrongly": log.cancelled_order_amount_deducted_wrongly,
                "TDS Issue": log.TDS_issue,
                "Wrong Penalty": log.Wrong_penalty
            }
            for issue_type, detail in issues.items():
                days_since_email = (date.today() - log.created_at.date()).days if log else None
                # print(days_since_email,"days_since_email")

                if detail and detail != "-":
                    issue_rows.append({
                        "order_id": log.order_id,
                        "issue_type": issue_type,
                        "details": detail,
                        "fp_status": log.fp_status,
                        "fp_order_date": log.fp_order_date if log.fp_order_date else "",
                        "reconcilation_date":log.created_at,
                        "restaurant_id":log.restaurant_id,
                        "Aging":days_since_email,

                    })

        return JsonResponse({"logs": issue_rows})
    
    return JsonResponse({"success": False, "error": "Invalid request method"})



@csrf_exempt
def get_dropdown_options(request):
    if request.method == "GET":
        restaurant_ids = SummeryLog.objects.values_list("restaurant_id", flat=True).distinct()
        aggregators = SummeryLog.objects.values_list("aggregator", flat=True).distinct()

        print(restaurant_ids,"restaurant_ids")

        return JsonResponse({
            "restaurant_ids": list(restaurant_ids),
            "aggregators": list(aggregators)
        })
    



# def get_email_replies(request):
#     aggregator = request.GET.get("aggregator")
#     restaurant_id = request.GET.get("restaurant_id")
#     client_name = request.GET.get("client_name")
#     selected_date_range = request.GET.get("selected_date_range")
#     print("get_email_replies in")

#     client = ClientDetails.objects.filter(
#         Q(zomato_restaurant_id=restaurant_id) | Q(swiggy_restaurant_id=restaurant_id)
#     ).first()

#     if not client or not client.email or not client.email_password:
#         return JsonResponse({"replies": [], "error": "No client credentials found"}, status=400)

#     subject_obj = SentEmailLog.objects.filter(
#         aggregator=aggregator,
#         restaurant_id=restaurant_id,
#         date_range=selected_date_range,
#     ).order_by('-timestamp').first()

#     if not subject_obj:
#         return JsonResponse({"replies": [], "error": "No sent email found for this filter"}, status=404)

#     subject_filter = subject_obj.subject.strip()

#     if aggregator == "Zomato" or aggregator == "Swiggy":
#         replies = fetch_replies_from_gmail(
#             client.email, 
#             client.email_password, 
#             subject_filter=subject_filter,
#             sender_filter="@gmail.com"
#         )

#     stored_replies = []

#     for reply in replies:
#         # date_obj = datetime.strptime(reply["date"], "%a, %d %b %Y %H:%M:%S %z")

#         try:
#             date_obj = parsedate_to_datetime(reply["date"])  # Use parsedate_to_datetime from email.utils
#         except Exception as e:
#             print("Failed to parse date:", reply["date"], e)
#             continue

#         EmailConversation.objects.get_or_create(
#         sent_email=subject_obj,
#         from_email=reply["from"],
#         to_email=client.email,
#         subject=reply["subject"],
#         body=reply["body"],
#         date=date_obj
#     )

#         # Check if already exists
#         # reply_obj, created = EmailReplyLog.objects.get_or_create(
#         #     sent_email=subject_obj,
#         #     subject=reply["subject"],
#         #     sender=reply["from"],
#         #     date=date_obj,
#         #     defaults={"body": reply["body"]}
#         # )

#         # stored_replies.append({
#         #     "from": reply_obj.sender,
#         #     "subject": reply_obj.subject,
#         #     "date": reply_obj.date.strftime("%d-%b-%Y %H:%M"),
#         #     "body": reply_obj.body
#         # })

#     return JsonResponse({"replies": stored_replies})





def get_email_replies(request):
    aggregator = request.GET.get("aggregator")
    restaurant_id = request.GET.get("restaurant_id")
    client_name = request.GET.get("client_name")
    selected_date_range = request.GET.get("selected_date_range")
    print("get_email_replies in")

    client = ClientDetails.objects.filter(
        Q(zomato_restaurant_id=restaurant_id) | Q(swiggy_restaurant_id=restaurant_id)
    ).first()

    if not client or not client.email or not client.email_password:
        return JsonResponse({"replies": [], "error": "No client credentials found"}, status=400)
    
    
    # Construct subject pattern to search
    subject_obj = SentEmailLog.objects.filter(
        aggregator=aggregator,
        restaurant_id=restaurant_id,
        date_range=selected_date_range,
    ).order_by('-timestamp').first()

    print(subject_obj.subject.strip(),"subject_obj.subject.strip()")
    latest_log = SentEmailLog.objects.filter(
    aggregator=aggregator,
    restaurant_id=restaurant_id,
    date_range=selected_date_range,
        ).order_by('-timestamp').last()
    
    days_since_email = (date.today() - latest_log.timestamp.date()).days if latest_log else None


    if not subject_obj:
        return JsonResponse({"replies": [], "error": "No sent email found for this filter"}, status=404)

    subject_filter = subject_obj.subject.strip()
    # subject_filter = f"Issue in {aggregator} Payout from {selected_date_range}-{restaurant_id } ({client_name})"
    # print(subject_filter,"subject_filter_get")
    if aggregator == "Zomato":
        replies = fetch_replies_from_gmail(client.email, client.email_password, subject_filter=subject_filter,sender_filter="@zomato.com",since_days=days_since_email)
    if aggregator == "Swiggy":
        replies = fetch_replies_from_gmail(client.email, client.email_password, subject_filter=subject_filter,sender_filter="@swiggy.com",since_days=days_since_email)
    # replies = fetch_replies_from_gmail(aggregator,restaurant_id)
    print(replies,"function_Called")
    for reply in replies:
#         # date_obj = datetime.strptime(reply["date"], "%a, %d %b %Y %H:%M:%S %z")

        try:
            date_obj = parsedate_to_datetime(reply["date"])  # Use parsedate_to_datetime from email.utils
        except Exception as e:
            print("Failed to parse date:", reply["date"], e)
            continue

        EmailConversation.objects.get_or_create(
        sent_email=subject_obj,
        from_email=reply["from"],
        to_email=client.email,
        subject=reply["subject"],
        body=reply["body"],
        date=date_obj
    )
        
        log = SentEmailLog.objects.filter(
            aggregator=aggregator,
            restaurant_id=restaurant_id,
            date_range=selected_date_range
        ).order_by("-timestamp").first()

        if replies:
            log.replies_json = replies
            log.save()
            print(f"Gmail replies saved to log ID: {log.id}")

    return JsonResponse({"replies": replies})

def clean_email_header(text):
    if not text:
        return ""
    # Keep removing prefixes like Re:, Fwd: from the start
    while True:
        new_subject = re.sub(r"^(re:|fwd:)\s*", "", text, flags=re.IGNORECASE)
        if new_subject == text:
            break
        text = new_subject

    # Collapse multiple spaces/newlines to a single space
    cleaned = re.sub(r"\s+", " ", text)
    print(cleaned)
    return cleaned.strip()


@csrf_exempt 
def send_reply_email(request):
    try:
        if request.method == "POST":
            data = json.loads(request.body)
            to_emails = [email.strip() for email in data.get("to", "").split(",") if email.strip()]
            subject = data.get("subject")
            message = data.get("body")
            aggregator = data.get("aggregator")
            restaurant_id = data.get("restaurant_id")
            user_email = data.get("user_email")  # 👈 Make sure this comes from frontend
            date_range=None


            cleaned_subject = clean_email_header(subject)
            print(cleaned_subject,"Cleaned_subject")
            match = re.search(r'from (\d{2}-[A-Za-z]{3}-\d{4} to \d{2}-[A-Za-z]{3}-\d{4})', cleaned_subject)
            if match:
                date_range = match.group(1)
                print(date_range,"date_range")  # Output: 24-Mar-2025 to 30-Mar-2025
            else:
                print("Date range not found")

            # Get client
            if aggregator == "Zomato":
                client = ClientDetails.objects.filter(zomato_restaurant_id=restaurant_id).first()
            elif aggregator == "Swiggy":
                client = ClientDetails.objects.filter(swiggy_restaurant_id=restaurant_id).first()
            else:
                return JsonResponse({"message": "Invalid aggregator"}, status=400)

            if not client or not client.email or not client.email_password:
                return JsonResponse({"message": "Client SMTP config missing"}, status=400)

            # Send email
            connection = get_connection(
                backend="django.core.mail.backends.smtp.EmailBackend",
                host="smtp.gmail.com",
                port=587,
                username=client.email,
                password=client.email_password,
                use_tls=True,
            )

            email = EmailMessage(
                subject=cleaned_subject,
                body=message,
                from_email=client.email,
                to=to_emails,
                connection=connection
            )
            email.content_subtype = "html"
            email.send()
            # subject=cleaned_subject,
            #  Save reply to SentEmailLog
            log = SentEmailLog.objects.filter(
                subject=cleaned_subject,
                aggregator=aggregator,
                restaurant_id=restaurant_id
            ).order_by("-timestamp").first()
            print(log,"LOG_LOG")
            if aggregator == "Zomato":
                print("DISPUTE IN CLar in zo")
                print(clients_zomato.objects.count())
                print(sales_report.objects.all())
                print("start_processing_update_fp_status")
                date_range = date_range # e.g., "10-Mar-2025 to 16-Mar-2025"
                start_date_str, end_date_str = date_range.split(" to ")
                start_date = datetime.strptime(start_date_str.strip(), "%d-%b-%Y").date()
                end_date = datetime.strptime(end_date_str.strip(), "%d-%b-%Y").date()
                print(type(restaurant_id),type(start_date), end_date,)
                update_sales_status_proc_dispute_in_clar(restaurant_id, start_date, end_date)
            elif aggregator == "Swiggy":
                print("DISPUTE IN CLar in sw")
                print(clients_zomato.objects.count())
                print(sales_report.objects.all())
                print("start_processing_update_fp_status")
                date_range = date_range  # e.g., "10-Mar-2025 to 16-Mar-2025"
                start_date_str, end_date_str = date_range.split(" to ")
                start_date = datetime.strptime(start_date_str.strip(), "%d-%b-%Y").date()
                end_date = datetime.strptime(end_date_str.strip(), "%d-%b-%Y").date()
                print(type(restaurant_id),type(start_date), end_date,)
                update_sales_status_proc_dispute_in_clar_swiggy(restaurant_id, start_date, end_date)

            add_dispute_in_clarification(aggregator, restaurant_id, date_range)
            if log:
                new_user_reply = {
                    "from": user_email,
                    "body": message,
                    "date": now().strftime("%d-%b-%Y %H:%M")
                }
                replies = log.user_replies_json or []
                replies.append(new_user_reply)
                log.user_replies_json = replies
                log.save()
                print("Saved user reply in log id:", log.id)
            
            

            return JsonResponse({"message": "Reply sent and stored successfully!"})
        return JsonResponse({"error": "Invalid method"}, status=405)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



# @csrf_exempt
# def send_reply_email(request):
#     try:
#         if request.method == "POST":
#             data = json.loads(request.body)
#             to_emails = [email.strip() for email in data.get("to", "").split(",") if email.strip()]
#             subject = data.get("subject")
#             message = data.get("body")
#             aggregator = data.get("aggregator")
#             restaurant_id = data.get("restaurant_id")

#             cleaned_subject = clean_email_header(subject)

#             # Get client details based on aggregator and restaurant_id
#             if aggregator == "Zomato":
#                 client = ClientDetails.objects.filter(zomato_restaurant_id=restaurant_id).first()
#             elif aggregator == "Swiggy":
#                 client = ClientDetails.objects.filter(swiggy_restaurant_id=restaurant_id).first()
#             else:
#                 return JsonResponse({"message": "Invalid aggregator"}, status=400)

#             if not client or not client.email or not client.email_password:
#                 return JsonResponse({"message": "Client SMTP config missing"}, status=400)
            

#             # Combine all recipients
#             # to_emails.extend([email.strip() for email in to_emails if email.strip()]) 

#             # Create SMTP connection
#             connection = get_connection(
#                 backend="django.core.mail.backends.smtp.EmailBackend",
#                 host="smtp.gmail.com",
#                 port=587,
#                 username=client.email,
#                 password=client.email_password,
#                 use_tls=True,
#             )

#             # Compose and send email
#             email = EmailMessage(
#                 subject=cleaned_subject,
#                 body=message,
#                 from_email=client.email,
#                 to=to_emails,
#                 connection=connection
#             )
#             email.content_subtype = "html"
#             email.send()

#             return JsonResponse({"message": "Reply sent successfully!"})
#         return JsonResponse({"error": "Invalid method"}, status=405)
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)



@csrf_exempt
def resend_email(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            subject = data.get("subject")
            recipients = data.get("recipients", "").split(",")
            cc = data.get("cc", "").split(",") if data.get("cc") else []
            body = data.get("body")

            # Fetch from session
            aggregator = request.session.get("aggregator")
            restaurant_id = request.session.get("restaurant_id")

            if not subject or not recipients or not body or not aggregator or not restaurant_id:
                return JsonResponse({"error": "Missing required fields"}, status=400)

            # Get the correct sender email based on aggregator
            from_email = None
            try:
                client = ClientDetails.objects.get(**{
                    f"{aggregator.lower()}_restaurant_id": restaurant_id
                })
                from_email = getattr(client, f"{aggregator.lower()}_finance_poc", None)
            except ClientDetails.DoesNotExist:
                return JsonResponse({"error": "ClientDetails not found for this aggregator and restaurant"}, status=404)

            if not from_email:
                return JsonResponse({"error": "Sender email not found in ClientDetails"}, status=404)

            if client.email and client.email_password:
                connection = get_connection(
                    backend="django.core.mail.backends.smtp.EmailBackend",
                    host="smtp.gmail.com",
                    port=587,
                    username=client.email,
                    password=client.email_password,
                    use_tls=True,
                )
            else:
                connection = get_connection()

            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=from_email,
                to=recipients,
                cc=cc,
                connection=connection
            )
            email.content_subtype = "html"
            email.send()

            return JsonResponse({"message": "Email resent successfully"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


def business_type_summary(request):
    business_types = list(ClientDetails.objects.filter(delflag=1).values_list('business_type', flat=True))
    total = len(business_types)
    count = Counter(business_types)

    summary = [
        {
            "category": category,
            "count": count.get(category, 0),
            "percentage": round((count.get(category, 0) / total) * 100, 2) if total > 0 else 0
        }
        for category, _ in ClientDetails.BUSINESS_TYPES
    ]

    return JsonResponse({"data": summary})



# def clients_by_business_type(request):
#     business_type = request.GET.get('type')
#     clients = ClientDetails.objects.filter(delflag=1, business_type=business_type)

#     data = [
#         {
#             "client_name": c.client_name,
#             "location": c.location,
#             "email": c.email,
#             "contact_number": c.contact_number,
#             "membership_type": str(c.membership_type) if c.membership_type else "N/A"
#         }
#         for c in clients
#     ]

#     return JsonResponse({"clients": data})

def get_filter_options(request):
    locations = ClientDetails.objects.filter(delflag=1).values_list('location', flat=True).distinct()
    clients = ClientDetails.objects.filter(delflag=1).values_list('client_name', flat=True).distinct()

    return JsonResponse({
        "locations": list(locations),
        "clients": list(clients),
    })

# def clients_by_filters(request):
#     business_type = request.GET.get('business_type')
#     location = request.GET.get('location')
#     client_name = request.GET.get('client_name')

#     # Filter based on the provided query parameters
#     clients = ClientDetails.objects.filter(delflag=1)

#     if business_type:
#         clients = clients.filter(business_type=business_type)
#     if location:
#         clients = clients.filter(location__icontains=location)  # Case insensitive match
#     if client_name:
#         clients = clients.filter(client_name__icontains=client_name)  # Case insensitive match

#     data = [
#         {
#             "client_id":c.id,
#             "client_name": c.client_name,
#             "location": c.location,
#             "email": c.email,
#             "contact_number": c.contact_number,
#             "membership_type": str(c.membership_type) if c.membership_type else "N/A"
            
#         }
#         for c in clients
        
#     ]
#     for i in data:
#         print(i)
#     # for i in clients:
#     #     print("client_ids",i.id)

#     return JsonResponse({"clients": data})


def clients_by_filters(request):
    business_type = request.GET.get('business_type')
    location = request.GET.get('location')  # Comma-separated
    client_name = request.GET.get('client_name')  # Comma-separated

    clients = ClientDetails.objects.filter(delflag=1)

    if business_type:
        clients = clients.filter(business_type=business_type)
    if location:
        loc_list = location.split(',')
        clients = clients.filter(location__in=loc_list)
    if client_name:
        name_list = client_name.split(',')
        clients = clients.filter(client_name__in=name_list)

    client_data = [{
        "client_id": c.id,
        "client_name": c.client_name,
        "location": c.location,
        "email": c.email,
        "contact_number": c.contact_number,
        "membership_type": str(c.membership_type) if c.membership_type else "N/A"
    } for c in clients]

    return JsonResponse({"clients": client_data})



def home_page(request):
    print("form_business")
    business_types = [bt[0] for bt in ClientDetails.BUSINESS_TYPES]
    aggregators = Aggregator.objects.filter(delflag=1) 
    print("Business types:", business_types)
    return render(request, 'index.html', {'business_types': business_types,'aggregators': aggregators})


def get_restaurant_id(request):
    client_id = request.GET.get('client_id')
    aggregator = request.GET.get('aggregator')
    if not client_id or not client_id.isdigit():
        return JsonResponse({"error": "Invalid client ID"}, status=400)

    client_id = int(client_id)
    client = ClientDetails.objects.get(id=client_id)
    # print(client,"Client")
    # print(client_id,"client_id")
    
    restaurant_id = None
    if aggregator == 'Zomato':
        restaurant_id = client.zomato_restaurant_id
    elif aggregator == 'Swiggy':
        restaurant_id = client.swiggy_restaurant_id

    return JsonResponse({"restaurant_id": restaurant_id})

# def get_summary_by_date_range(request):
#     aggregator = request.GET.get('aggregator')
#     restaurant_id = request.GET.get('restaurant_id')
#     start = request.GET.get('start_date')
#     end = request.GET.get('end_date')

#     logs = SummeryLog.objects.filter(
#         aggregator=aggregator,
#         restaurant_id=restaurant_id,
#         date__range=[start, end]
#     )

#     summary = Counter(log.fp_status for log in logs)

#     return JsonResponse({
#         "summary": summary,
#         "total": sum(summary.values())
#     })


# def get_summary(request):
#     aggregator = request.GET.get('aggregator')
#     restaurant_id = request.GET.get('restaurant_id')
#     start_date = request.GET.get('start_date')
#     end_date = request.GET.get('end_date')
#     # print(start_date,end_date,"start_date")

#     model_map = {
#         "zomato": "clients_zomato",
#         "swiggy": "clients_swiggy"
#     }

#     try:
#         start = datetime.strptime(start_date, "%d-%b-%Y").date()
#         end = datetime.strptime(end_date, "%d-%b-%Y").date()
#         print(start_date,end_date,"start_date")
#     except Exception:
#         return JsonResponse({"summary": {}})

#     summary_qs = SummeryLog.objects.filter(
#         aggregator=aggregator,
#         restaurant_id=restaurant_id,
#         fp_order_date__date__range=(start, end)
#     ).values('fp_status').annotate(count=Count('fp_status'))
#     print(start_date,end_date,"start_date")

#     summary = {entry['fp_status']: entry['count'] for entry in summary_qs}

#     print(summary,"summery")

#     return JsonResponse({"summary": summary})


def get_summary_all(request):
    aggregator = request.GET.get('aggregator')
    restaurant_id = request.GET.get('restaurant_id')

    if not aggregator or not restaurant_id:
        return JsonResponse({"summary": {}})

    # Step 1: Filter all records for given aggregator and restaurant (no date filter)
    base_qs = SummeryLog.objects.filter(
        aggregator=aggregator,
        restaurant_id=restaurant_id,
    )

    # Step 2: Annotate with row number (latest per order_id)
    annotated_qs = base_qs.annotate(
        row_num=Window(
            expression=RowNumber(),
            partition_by=[F('order_id')],
            order_by=F('created_at').desc()
        )
    ).filter(row_num=1)

    # Step 3: Count fp_status manually
    status_list = annotated_qs.values_list('fp_status', flat=True)
    summary = dict(Counter(status_list))

    return JsonResponse({"summary": summary})


def get_summary(request):
    aggregator = request.GET.get('aggregator')
    restaurant_id = request.GET.get('restaurant_id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    print(start_date,"start_date",end_date)


    try:


        start = datetime.strptime(start_date, "%d-%b-%Y").date()
        end = datetime.strptime(end_date, "%d-%b-%Y").date()
        
    except Exception:
        print("except")
        return JsonResponse({"summary": {}})

    print(start,"start","end",end)
    # Step 1: Filter relevant records
    base_qs = SummeryLog.objects.filter(
        aggregator=aggregator,
        restaurant_id=restaurant_id,
        fp_order_date__date__range=(start, end)
    )

    # Step 2: Annotate with row number
    annotated_qs = base_qs.annotate(
        row_num=Window(
            expression=RowNumber(),
            partition_by=[F('order_id')],
            order_by=F('created_at').desc()
        )
    ).filter(row_num=1)

    # Step 3: Count fp_status manually
    status_list = annotated_qs.values_list('fp_status', flat=True)
    summary = dict(Counter(status_list))

    return JsonResponse({"summary": summary})



def get_dates_for_restaurant_admin(request):
    restaurant_id = request.GET.get("restaurant_id")
    aggregator = request.GET.get("aggregator")

    if restaurant_id and aggregator:
        if aggregator == "Zomato":
            date_ranges = clients_zomato.objects.filter(fp_restaurant_id=restaurant_id).values_list("from_date", "to_date")
        elif aggregator == "Swiggy":
            date_ranges = clients_swiggy.objects.filter(fp_restaurant_id=restaurant_id).values_list("from_date", "to_date")
        else:
            return JsonResponse({"dates": []})

        formatted_dates = [
            f"{from_date.strftime('%d-%b-%Y')} to {to_date.strftime('%d-%b-%Y')}"
            for from_date, to_date in date_ranges
        ]

        return JsonResponse({"dates": formatted_dates})

    return JsonResponse({"dates": []})




def get_multi_summary(request):
    aggregator = request.GET.get('aggregator')
    restaurant_id = request.GET.get('restaurant_id')
    mode = request.GET.get('mode')  # this_month, last_month, q1, q2, q3, q4, this_year

    c_name = None
    # Choose the correct model based on aggregator
    if aggregator.lower() == 'zomato':
        model = clients_zomato
        c_name = ClientDetails.objects.filter(zomato_restaurant_id = restaurant_id).first()
    elif aggregator.lower() == 'swiggy' :
        model = clients_swiggy
        c_name = ClientDetails.objects.filter(swiggy_restaurant_id = restaurant_id).first()
    # Determine the date ranges based on the mode
    if mode == 'this_month':
        print(mode,"mode")
        start_date, end_date = get_this_month_range()
    elif mode == 'last_month':
        print(mode,"mode")
        start_date, end_date = get_last_month_range()
    elif mode == 'this_year':
        print(mode,"mode")
        start_date, end_date = get_this_year_range()
    elif mode in ['q1', 'q2', 'q3', 'q4']:
        print(mode,"mode")
        start_date, end_date = get_quarter_range(mode)
    else:
        return JsonResponse({"error": "Invalid mode"})

    # Step 1: Filter clients for matching restaurant_id and date ranges
    print(start_date,end_date,"start_date")
    client_qs = model.objects.filter(
        fp_restaurant_id=restaurant_id,
        from_date__lte=end_date,
        to_date__gte=start_date
    )

    bars = []

    # Step 2: Loop through each matching date range and get summary
    for client in client_qs:
        # Fetch the summary for the specific date range
        summary = get_summary_for_date_range(client.from_date, client.to_date, aggregator, restaurant_id)
        bars.append({
            
            'label': f'{client.from_date.strftime("%d-%b-%Y")} to {client.to_date.strftime("%d-%b-%Y")}',
            'summary': summary,
            'res_id':restaurant_id,
            'client_name':c_name.client_name
        })
        print(bars,"bars")

    return JsonResponse({"bars": bars})

def get_summary_for_date_range(from_date, to_date, aggregator, restaurant_id):
    # Convert date range to start and end dates
    start = from_date.date()
    end = to_date.date()

    # Step 1: Filter SummeryLog entries for the date range
    base_qs = SummeryLog.objects.filter(
        aggregator=aggregator,
        restaurant_id=restaurant_id,
        fp_order_date__date__range=(start, end)
    )

    # Step 2: Annotate with RowNumber to get latest entry per order_id
    annotated_qs = base_qs.annotate(
        row_num=Window(
            expression=RowNumber(),
            partition_by=[F('order_id')],
            order_by=F('created_at').desc()
        )
    ).filter(row_num=1)

    # Step 3: Count latest fp_status values only
    status_list = annotated_qs.values_list('fp_status', flat=True)
    return dict(Counter(status_list))



# def get_summary_for_date_range(from_date, to_date, aggregator, restaurant_id):
#     # Convert date range to start and end dates
#     start = from_date.date()
#     end = to_date.date()

#     # Step 1: Filter SummeryLog entries for the date range
#     base_qs = SummeryLog.objects.filter(
#         aggregator=aggregator,
#         restaurant_id=restaurant_id,
#         fp_order_date__date__range=(start, end)
#     )

#     # Step 2: Count fp_status for each log
#     status_list = base_qs.values_list('fp_status', flat=True)
#     return dict(Counter(status_list))


# Helper functions for date ranges
def get_this_month_range():
    today = datetime.today()
    start_date = today.replace(day=1)
    end_date = today.replace(day=28) + timedelta(days=4)  # Go to next month, then subtract days
    end_date = end_date.replace(day=1) - timedelta(days=1)  # Get last day of the month
    return start_date, end_date

def get_last_month_range():
    now = timezone.now()
    first_day_current_month = now.replace(day=1)

    # Last day of last month = day before first day of this month
    last_day_last_month = first_day_current_month - timedelta(days=1)

    # First day of last month
    first_day_last_month = last_day_last_month.replace(day=1)

    # Now you have correct order
    start_date = first_day_last_month
    end_date = last_day_last_month
    return start_date, last_day_last_month

def get_this_year_range():
    today = datetime.today()
    start_date = today.replace(month=1, day=1)
    end_date = today.replace(month=12, day=31)
    return start_date, end_date

def get_quarter_range(quarter):
    today = datetime.today()
    if quarter == 'q1':
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=3, day=31)
    elif quarter == 'q2':
        start_date = today.replace(month=4, day=1)
        end_date = today.replace(month=6, day=30)
    elif quarter == 'q3':
        start_date = today.replace(month=7, day=1)
        end_date = today.replace(month=9, day=30)
    elif quarter == 'q4':
        start_date = today.replace(month=10, day=1)
        end_date = today.replace(month=12, day=31)
    return start_date, end_date



# create user_type


def usertype_list(request):
    usertypes = UserType.objects.filter(delflag=1)  # Active only

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = list(usertypes.values("id", "user_type"))
        return JsonResponse({"usertypes": data})

    if request.method == "POST":
        form = UserTypeForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True, "message": "User Type added successfully!"})
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    form = UserTypeForm()
    return render(request, 'user_list.html', {'form': form, 'usertypes': usertypes})

def usertype_add(request):
    if request.method == "POST":
        form = UserTypeForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True, "message": "User Type added successfully!"})
        return JsonResponse({"success": False, "errors": form.errors}, status=400)
    
    return JsonResponse({"error": "Invalid request"}, status=400)

def usertype_edit(request, pk):
    usertype = get_object_or_404(UserType, pk=pk)

    if request.method == "POST":
        form = UserTypeForm(request.POST, instance=usertype)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True, "message": "User Type updated successfully!"})
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form_data = {
            "user_type": usertype.user_type
        }
        return JsonResponse(form_data)

    form = UserTypeForm(instance=usertype)
    return render(request, 'usertype_edit.html', {'form': form, 'usertype': usertype})

def usertype_delete(request, pk):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method!"})
    
    usertype = get_object_or_404(UserType, pk=pk)
    usertype.delflag = 0  # Soft delete
    usertype.save()
    
    return JsonResponse({"success": True, "message": "User Type deleted successfully!"})


#For Flutter App 

@csrf_exempt
def client_login(request):
    
    pass
    # if request.method == "POST":
    #     data = json.loads(request.body)
    #     username = data.get("username")
    #     password = data.get("password")

    #     try:
    #         client = ClientDetails.objects.get(fp_username=username, fp_password=password, delflag=1)
    #         response = {
    #             "status": "success",
    #             "message": "Login successful",
    #             "client_id": client.id,
    #             "client_name": client.client_name,
    #             "email": client.email,
    #             "business_type": client.business_type,
    #         }
    #     except ClientDetails.DoesNotExist:
    #         response = {
    #             "status": "error",
    #             "message": "Invalid username or password"
    #         }

    #     return JsonResponse(response)
    
    
    
# For Landing Page 

@csrf_exempt
def request_demo(request):
    print("Request_demo.....")
    if request.method == 'POST':
        form = DemoRequestForm(request.POST)
        if form.is_valid():
            demo_request = form.save()
            phone_number = demo_request.phone_number  # e.g., "+91 9876543210"
            # country_code = demo_request.country_code  # e.g., "+91"
            demo_request.phone_number = phone_number
            # demo_request.country_code = country_code
            # Extract phone number and country code
            demo_request.save()

            subject = f"Demo Request from {demo_request.full_name} - {demo_request.reason.replace('-', ' ').title()}"
            message = (
                f"New Request Received:\n\n"
                f"Full Name: {demo_request.full_name}\n"
                f"Email: {demo_request.email}\n"
                f"Phone:{demo_request.phone_number}\n"
                f"Reason: {demo_request.reason.replace('-', ' ').title()}\n\n"
                f"Message:\n{demo_request.message}"
            )
            from_email = demo_request.email
            recipient_list = ["gokulms7885@gmail.com"]

            send_mail(subject, message, from_email, recipient_list)

            return JsonResponse({'status': 'success', 'message': 'Demo request submitted successfully'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid form data'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@csrf_exempt
def submit_popup_form(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        PopupLead.objects.create(name=name, email=email)
        return JsonResponse({'message': 'Form submitted successfully!'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

# @csrf_exempt 
# def request_demo(request):
#     print("Request_demo.....")
#     if request.method == 'POST':
#         form = DemoRequestForm(request.POST)
#         if form.is_valid():
#             demo_request = form.save()

#             # Send email
#             subject = f"Demo Request from {demo_request.full_name}"
#             message = f"New Demo Request:\n\n{demo_request.message}\n\nContact: {demo_request.phone_number}\n\nEmail: {demo_request.email}"
#             from_email = demo_request.email  # You can make this dynamic as per your need
#             recipient_list = ["gokulms7885@gmail.com"] 

#             send_mail(subject, message, from_email, recipient_list)

#             return JsonResponse({'status': 'success', 'message': 'Demo request submitted successfully'})
#         else:
#             return JsonResponse({'status': 'error', 'message': 'Invalid form data'})

#     return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


# @csrf_exempt
# def request_demo(request):
#     if request.method == "POST":
#         full_name = request.POST.get("full_name")
#         email = request.POST.get("email")
#         phone_number = request.POST.get("phone_number")
#         user_type = request.POST.get("user_type")
#         message = request.POST.get("message")

#         # For now, skip email sending — just return the data
#         return JsonResponse({
#             "status": "success",
#             "message": "Request received",
#             "data": {
#                 "full_name": full_name,
#                 "email": email,
#                 "phone": phone_number,
#                 "user_type": user_type,
#                 "message": message
#             }
#         })

#     return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)
