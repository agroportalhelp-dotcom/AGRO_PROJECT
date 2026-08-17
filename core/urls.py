from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Main Navigation Pages
    path('', views.homepage_view, name='index'),
    path('about/', views.about_view if hasattr(views, 'about_view') else views.homepage_view, name='about'),
    path('marketplace/', views.marketplace_view if hasattr(views, 'marketplace_view') else views.homepage_view, name='marketplace'),
    path('schemes/', views.schemes_view if hasattr(views, 'schemes_view') else views.homepage_view, name='schemes'),
    path('contact/', views.contact_view if hasattr(views, 'contact_view') else views.homepage_view, name='contact'),
    path('dashboard/', views.dashboard_view if hasattr(views, 'dashboard_view') else views.homepage_view, name='dashboard'),
    path('profile/', views.profile_view if hasattr(views, 'profile_view') else views.homepage_view, name='profile'),

    # Operations & Forms
    path('add-crop/', views.add_crop_view if hasattr(views, 'add_crop_view') else views.homepage_view, name='add_crop'),
    path('add-product/', views.add_product_view if hasattr(views, 'add_product_view') else views.homepage_view, name='add_product'),
    path('add-farmer/', views.add_farmer_view if hasattr(views, 'add_farmer_view') else views.homepage_view, name='add_farmer'),

    # Registration & Gmail OTP
    path('register/', views.register_view, name='register'),
    path('verify-email-otp/', views.verify_email_otp_view, name='verify_email_otp'),
    
    # Password Reset Routes
    path('forgot-password/', views.forgot_password_request_view if hasattr(views, 'forgot_password_request_view') else views.homepage_view, name='forgot_password_request'),
    path('forgot-password/verify/', views.forgot_password_verify_view if hasattr(views, 'forgot_password_verify_view') else views.homepage_view, name='forgot_password_verify'),
    
    # Authentication (Login / Logout)
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),
    
    # Marketplace Ownership Actions
    path('product/<int:product_id>/edit/', views.edit_product_view, name='edit_product'),
    path('product/<int:product_id>/delete/', views.delete_product_view, name='delete_product'),
    
    # Admin User/Farmer Management
    path('admin-panel/farmers/', views.farmer_list_view if hasattr(views, 'farmer_list_view') else views.homepage_view, name='farmer_list'),
    path('admin-panel/user/<int:user_id>/toggle-block/', views.toggle_user_block_view, name='toggle_user_block'),
    path('admin-panel/user/<int:user_id>/delete/', views.delete_user_view, name='delete_user'),
    path('crops/', views.crop_list_view, name='crop_list'),
    path('helpful-sites/', views.helpful_sites_view, name='helpful_sites'),
    path('admin-panel/helpful-sites/add/', views.add_helpful_site_view, name='add_helpful_site'),
    path('admin-panel/helpful-sites/<int:site_id>/delete/', views.delete_helpful_site_view, name='delete_helpful_site'),
]