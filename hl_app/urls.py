from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.oauth_login, name='oauth_login'),
    path('', views.oauth_callback, name='oauth_callback'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('update-contact/', views.update_contact, name='update_contact'),  
]
