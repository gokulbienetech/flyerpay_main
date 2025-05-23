"""
URL configuration for flyerpay project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from Payout_Reconciliation.views import  business_type_summary, client_login, clients_by_filters, get_dates_for_restaurant_admin, get_dropdown_options, get_email_replies, get_filter_options, get_multi_summary, get_restaurant_id, get_sent_email, get_summary, get_summary_all, get_summery_logs, log_page, request_demo, resend_email, send_reply_email, submit_popup_form, update_reconciliation_status, upload_excel,home_page,get_payout_and_order_summary,aggregator_list, aggregator_edit, aggregator_delete,client_details_view, client_edit, client_delete,aggregator_add,membership_list,membership_add,membership_edit,membership_delete,get_restaurant_ids,get_dates_for_restaurant,get_restaurants_for_client,send_reconciliation_email,get_swiggy_restaurant_id,get_swiggy_dates_for_restaurant,get_swiggy_restaurants_for_client, usertype_add, usertype_delete, usertype_edit, usertype_list
# from flyerpay.Payout_Reconciliation import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path("", home_page, name="home_page"),
    # path("client_details_form/", client_details_form, name="client_details_form"),
    path("clients/", client_details_view, name="client_details_view"),
    path("clients/edit/<int:pk>/", client_edit, name="client_edit"),
    path("clients/delete/<int:pk>/", client_delete, name="client_delete"),
    path("upload_excel/", upload_excel, name="upload_excel"),
    path("get_payout_and_order_summary/", get_payout_and_order_summary, name="get_payout_and_order_summary"),
    path('aggregators/', aggregator_list, name='aggregator_list'),
    path('aggregators/add/', aggregator_add, name='aggregator_add'),  # Add this!
    path('aggregators/edit/<int:pk>/', aggregator_edit, name='aggregator_edit'),
    path('aggregators/delete/<int:pk>/', aggregator_delete, name='aggregator_delete'),
    #  path("get_reconciliation_report/",get_reconciliation_report,name="get_reconciliation_report"),
    path('membership_list/', membership_list, name='membership_list'),
    path('memberships/add/', membership_add, name='membership_add'),
    path('memberships/edit/<int:pk>/', membership_edit, name='membership_edit'),
    path('memberships/delete/<int:pk>/', membership_delete, name='membership_delete'),
    path('get_restaurant_ids/', get_restaurant_ids, name='get_restaurant_ids'),
    path("get_dates/", get_dates_for_restaurant, name="get_dates_for_restaurant"),
    path("get_restaurants/", get_restaurants_for_client, name="get_restaurants_for_client"),
    path('send-reconciliation-email/', send_reconciliation_email, name='send_reconciliation_email'),
    path('get_swiggy_restaurant_id/', get_swiggy_restaurant_id, name='get_swiggy_restaurant_id'),
    path('get_swiggy_dates_for_restaurant/', get_swiggy_dates_for_restaurant, name='get_swiggy_dates_for_restaurant'),
    path('get_swiggy_restaurants_for_client/', get_swiggy_restaurants_for_client, name='get_swiggy_restaurants_for_client'),
    path('update-reconciliation-status/', update_reconciliation_status, name='update_reconciliation_status'),
    path('get_sent_email/', get_sent_email, name='get_sent_email'),
    path('log_page/', log_page, name='log_page'),
    path('get_summery_logs/', get_summery_logs, name='get_summery_logs'),
    path("get_dropdown_options/",get_dropdown_options, name="get_dropdown_options"),
    path("get_email_replies/", get_email_replies, name="get_email_replies"),
    path("send_reply_email/", send_reply_email, name="send_reply_email"),
    path("resend_email/", resend_email, name="resend_email"),
    path('api/business-type-summary/',business_type_summary, name='business_type_summary'),
    path('api/clients-by-filters/', clients_by_filters, name='clients_by_filters'),
    path('api/get-restaurant-id/', get_restaurant_id, name='get_restaurant_id'),
    path('api/get-summary/', get_summary, name='get_summary'),
    path('api/get_dates_for_restaurant_admin/', get_dates_for_restaurant_admin, name='get_dates_for_restaurant_admin'),
    path('api/filter-options/', get_filter_options, name='get_filter_options'),
    path('api/get-summary-all/', get_summary_all, name='get_summary_all'), 
    # path('api/get-restaurant-id/', get_restaurant_id, name='get_restaurant_id'),
    # path('api/get_dates_for_restaurant_admin/', get_dates_for_restaurant_admin, name='get_dates_for_restaurant_admin'),
    # path('api/get-summary/',get_summary, name='get_summary'),
    # path('api/get-summary-all/', get_summary_all, name='get_summary_all'),
    path('api/get-multi-summary/', get_multi_summary, name='get_multi_summary'),

    # path('api/clients-by-business-type/', clients_by_business_type, name='clients_by_business_type'),

    # path('get_restaurants_for_client_file/', get_restaurants_for_client_file, name='get_restaurants_for_client_file'),
    path('api/client-login/', client_login, name='client_login'),
    
    path('api/request-demo/', request_demo, name='request_demo'),
    path('submit-popup-form/', submit_popup_form, name='submit_popup_form'),
    
    path('usertype_list/', usertype_list, name='usertype_list'),          # List + Create
    path('usertype/add/', usertype_add, name='usertype_add'),
    path('usertype/edit/<int:pk>/', usertype_edit, name='usertype_edit'),  # Edit
    path('usertype/delete/<int:pk>/',usertype_delete, name='usertype_delete'),  # Delete
    
    # path("ajax/add-user-type/", add_user_type_ajax, name="user_type_add_ajax"),
    # path('users/', user_list, name='users'),
    # path('users/get/<int:user_id>/', get_user),
    # path('users/save/', save_user),
    # path('users/delete/<int:user_id>/', delete_user),

]
