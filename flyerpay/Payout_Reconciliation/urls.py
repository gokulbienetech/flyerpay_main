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
from django.urls import path

from .views import client_details_form,home_page,upload_excel,get_reconciliation_report

urlpatterns = [
    path('admin/', admin.site.urls),
    # path("", home_page, name="home_page"),
    # path("add-client/", client_details_form, name="add_client"),
    # path("upload-excel/", upload_excel, name="upload_excel"),
    # path("get_reconciliation_report/",get_reconciliation_report,name="get_reconciliation_report")   

    
]
