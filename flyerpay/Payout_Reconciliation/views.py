from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
import pandas as pd
from django.core.files.storage import default_storage
from django.contrib import messages
from sqlalchemy import create_engine, text
from .models import zomato_order,sales_report,sales_report_swiggy,SwiggyOrder,ReconciliationSummary, ClientDetails,Aggregator,Membership,clients_zomato,clients_swiggy,swiggy_CPC_Ads,zomato_cpc_ads
from django.http import JsonResponse
from .forms import ClientDetailsForm ,UploadExcelForm_Zomato,AggregatorForm,UploadExcelForm_Swiggy,UploadExcelForm_FlyerEats,MembershipForm
from datetime import datetime
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




logger = logging.getLogger(__name__)

def home_page(request):
    return render(request, "index.html")





def client_details_view(request):
    """Handles adding, displaying, and deleting clients on the same page."""
    clients = ClientDetails.objects.filter(delflag=1)  # Show only active clients
    form = ClientDetailsForm()

    if request.method == "POST":
        form = ClientDetailsForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            # client.created_date = now()
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
        "fp_username": client.fp_username,
        "fp_password": client.fp_password,
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
        pending_orders_result = cursor.fetchall()
        if aggregator == "Zomato":
            for row in pending_orders_result:
                issue_codes = row[16].split(',') if row[16] else []

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
            "cancellation_charge_percentage": row[14],
            "pending_order_difference": row[15],
            "issue_codes": issue_codes,
            "wrong_payout_settled": "Yes" if '1' in issue_codes else "-",
            "wrong_taxes_on_service_payment_fees": f"instead of ₹{row[2]} Deducted ₹{row[6]}, Difference {round((row[2]-row[6]),2)}" if '2' in issue_codes else "-",
            "wrong_payment_mechanism_fee": f"instead of ₹{row[3]} Deducted ₹{row[7]}, Difference {round((row[3]-row[7]),2)}" if '3' in issue_codes else "-",
            "wrong_service_fee": f"instead of ₹{row[4]} Deducted ₹{row[8]}, Difference {round((row[4]-row[8]),3)}" if '4' in issue_codes else "-",
            "cancelled_order_amount_deducted_wrongly": f"instead of {row[14]}% Settled only {round((row[5]/row[11]*100),2)}% Difference ₹{row[15]}" if '5' in issue_codes else "-",
            "TDS_issue": f"TDS Calculated Wrongly instead of {round(row[11]*0.001,2)} Deducted {row[13]}, Difference {round(((row[11]*0.001)-row[13]),2)}" if '6' in issue_codes else "-",
            "Wrong_penalty": f"Wrong penalty Charges Imposed instead of {row[5]} Deducted {round((row[5]/row[11]*100),2)}, Difference {row[15]}" if '7' in issue_codes else "-",
            "fp_order_date": row[9],
            "fp_status": row[10],
            "fp_total_amt": row[11],
            "zo_total_amt": row[12],
            "zo_TDS": row[13]
        })
            pending_orders.append(pending_order)
            print(pending_order,"pending_order555")

        elif aggregator == "Swiggy":
            for row in pending_orders_result:
                issue_codes = row[18].split(',') if row[18] else []
                print(issue_codes,"issue_codes",row[18])

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
            "cancellation_charge_percentage": row[16],
            "pending_order_difference": row[17],
            "issue_codes": issue_codes,
            "wrong_payout_settled": "Yes" if '1' in issue_codes else "-",
            "wrong_taxes_on_service_payment_fees": f"instead of ₹{row[2]} Deducted ₹{row[6]}, Difference {round((row[2]-row[6]),2)}" if '2' in issue_codes else "-",
            "wrong_payment_mechanism_fee": f"instead of ₹{row[3]} Deducted ₹{row[7]}, Difference {round((row[3]-row[7]),2)}" if '3' in issue_codes else "-",
            "wrong_service_fee": f"instead of ₹{row[4]} Deducted ₹{row[8]}, Difference {round((row[4]-row[8]),3)}" if '4' in issue_codes else "-",
            "cancelled_order_amount_deducted_wrongly": f"instead of {row[16]}% Settled only {round((row[5]/row[11]*100),2)}% Difference ₹{row[17]}" if '5' in issue_codes else "-",
            "TDS_issue": f"TDS Calculated Wrongly instead of {round(row[11]*0.001,2)} Deducted {row[13]}, Difference {round(((row[11]*0.001)-row[13]),2)}" if '6' in issue_codes else "-",
            "Wrong_penalty": f"Wrong penalty Charges Imposed instead of {row[16]}% Deducted {round((row[5]/row[11]*100),2)}%, Difference {row[17]}" if '7' in issue_codes else "-",
            "fp_order_date": row[9],
            "fp_status": row[10],
            "fp_total_amt": row[11],
            "zo_total_amt": row[12],
            "zo_TDS": row[13],
            "mfr_accurate": row[14],  # column index 14 is `mfr_accurate`
            "mfr_pressed": row[15]    # column index 15 is `mfr_pressed`
        })

        pending_orders.append(pending_order)
        # print(pending_orders,"pending_orders6666")
        # for i in pending_orders:
        #     print(i["order_id"],i["issue_codes"])

        # Fetch Missing Orders
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

    print( summary_result[2],"6666")
    # print(cpc_ads["cpc_value"],"cpccccc") 
        
    from_date = datetime.strptime(from_date, "%Y-%m-%d")
    to_date = datetime.strptime(to_date, "%Y-%m-%d")

    # Format as needed
    from_date_1 = from_date.strftime("%d-%b-%Y")
    to_date_1 = to_date.strftime("%d-%b-%Y")
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
        
    }

    # Convert Decimal values to float before saving in session
    report_data_serializable = json.loads(json.dumps(report_data, default=convert_decimal_to_float))

    # Store in session
    request.session["report_data"] = report_data_serializable
    request.session.modified = True

    # print("Session Data Stored:", json.dumps(request.session.get("report_data"), indent=2))
    print(report_data["expected_payout"],"expected_payout5555666",report_data["cpc_ads"],"cpc_ads")

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
    else:
        total_ads_inc_gst = total_dining_ads = cpc_value = 0  # Default values
        
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
        print("Inserted or updated CPC Ads data.")
        
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
    return {
        "status": "success",
        "message": "File processed successfully.",
        "min_date": min_date,
        "max_date": max_date,
        "cancelled_orders": cancelled_orders,
        "rejected_orders":rejected_orders,
        "ordinary_order":ordinary_order
    }
    
    
    
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
                elif rejection_status == "Order picked up by rider" or rejection_status ==  "Order ready, not picked up by rider":
                    df.at[idx, "Expected_Payout"] = round(row["Total_Amount"] * 0.80, 2)
            elif order_id in rejected_dict:
                # rejected_stat = rejected_dict[order_id]
                if rejected_dict[order_id]["Cancelled_Rejected_State"] == "Delivery partner arrived":
                    df.at[idx, "Expected_Payout"] = round(-1*(row["Total_Amount"] * commission_percentage), 2)
                elif rejected_dict[order_id]["Cancelled_Rejected_State"]  == "Order accepted":
                    df.at[idx, "Expected_Payout"] = round(-1*(row["Total_Amount"] * 0.105), 2)
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

    # Insert into sales_report table
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
    ["order_id", "cancelled_by", "mfr_accurate", "mfr_pressed","order_payment_type"]
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
            "order_payment_type":order["order_payment_type"]
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
                df.at[idx, "Expected_Payout"] = round(row["Total_Amount"] * 0.80, 2)
                    
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

