from django.contrib import admin
from django.urls import path, include
from shldataset import views
urlpatterns = [
    path('getdata', views.get_data),
    path('searchdata',views.get_serached_data),
    path('convert',views.convertcsv)
]