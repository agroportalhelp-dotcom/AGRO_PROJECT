import socket
from socket import gaierror
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import password_validation
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction

from .models import Profile, Crop, Product, ProductImage, Scheme, SiteUpdate, HelpfulWebsite
from .forms import CropForm, FarmerCreationForm, UserUpdateForm, ProfileForm, HelpfulWebsiteForm


def is_admin(user):
    """Helper check for superusers or staff members."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# ==========================================
# HELPFUL SITES MANAGEMENT
# ==========================================

def helpful_sites_view(request):
    sites = HelpfulWebsite.objects.all()
    return render(request, 'core/helpful_sites.html', {'sites': sites})


@user_passes_test(is_admin)
def add_helpful_site_view(request):
    if request.method == 'POST':
        form = HelpfulWebsiteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Helpful website added successfully!")
            return redirect('helpful_sites')
    else:
        form = HelpfulWebsiteForm()
    return render(request, 'core/add_helpful_site.html', {'form': form})


@user_passes_test(is_admin)
def delete_helpful_site_view(request, site_id):
    site = get_object_or_404(HelpfulWebsite, id=site_id)
    site.delete()
    messages.success(request, "Helpful website removed successfully.")
    return redirect('helpful_sites')


# ==========================================
# GENERAL PAGES
# ==========================================

def homepage_view(request):
    updates = SiteUpdate.objects.all().order_by('-created_at') if hasattr(SiteUpdate, 'created_at') else SiteUpdate.objects.all()
    return render(request, 'core/index.html', {'updates': updates})


def about_view(request):
    return render(request, 'core/about.html')


def contact_view(request):
    if request.method == 'POST':
        messages.success(request, "Your message has been sent successfully!")
        return redirect('contact')
    return render(request, 'core/contact.html')


def schemes_view(request):
    schemes = Scheme.objects.all()
    return render(request, 'core/schemes.html', {'schemes': schemes})


# ==========================================
# AUTHENTICATION & GMAIL OTP REGISTRATION
# ==========================================

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        full_name = request.POST.get('full_name', '').strip().split(' ', 1)
        first_name = full_name[0]
        last_name = full_name[1] if len(full_name) > 1 else ''
        phone = request.POST.get('phone', '').strip()
        state = request.POST.get('state', '')
        district = request.POST.get('district', '')
        city = request.POST.get('city', '')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email address is already registered.")
            return redirect('register')

        # Use atomic transaction to prevent dangling users if email fails
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=False
                )
                
                profile, created = Profile.objects.get_or_create(
                    user=user,
                    defaults={
                        'phone': phone,
                        'state': state,
                        'district': district,
                        'city': city
                    }
                )

                otp = profile.generate_otp()

                send_mail(
                    subject="AGRO Portal - Verify Your Email",
                    message=f"Hello {user.first_name or user.username},\n\nYour OTP for registration on AGRO Portal is: {otp}\n\nThank you!",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                
                request.session['verify_user_id'] = user.id
                messages.success(request, f"OTP sent to {email}. Please check your inbox.")
                return redirect('verify_email_otp')

        except (socket.gaierror, Exception) as e:
            messages.error(request, "Unable to send verification email. Please check your network connection and credentials.")
            return redirect('register')

    return render(request, 'core/register.html')


def verify_email_otp_view(request):
    user_id = request.session.get('verify_user_id')
    if not user_id:
        return redirect('register')

    user = get_object_or_404(User, id=user_id)
    profile = getattr(user, 'profile', None)

    if not profile:
        messages.error(request, "Profile not found. Please register again.")
        return redirect('register')

    if request.method == 'POST':
        input_otp = request.POST.get('otp', '').strip()
        if input_otp and input_otp == profile.email_otp:
            user.is_active = True
            profile.is_email_verified = True
            profile.email_otp = None
            user.save()
            profile.save()
            
            request.session.pop('verify_user_id', None)
            messages.success(request, "Email verified successfully! You can now log in.")
            return redirect('login')
        else:
            messages.error(request, "Invalid OTP code. Please try again.")

    return render(request, 'core/verify_otp.html', {'email': user.email})


# ==========================================
# USER DASHBOARD & PROFILE
# ==========================================

@login_required
def dashboard_view(request):
    crops = Crop.objects.filter(farmer=request.user)
    products = Product.objects.filter(farmer=request.user).prefetch_related('images')
    return render(request, 'core/dashboard.html', {
        'crops': crops,
        'products': products
    })


@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileForm(request.POST, instance=profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileForm(instance=profile)

    return render(request, 'core/profile.html', {
        'u_form': u_form,
        'p_form': p_form,
        'profile': profile
    })


# ==========================================
# MARKETPLACE & PRODUCT MANAGEMENT
# ==========================================

def marketplace_view(request):
    products = Product.objects.all().prefetch_related('images').select_related('farmer', 'farmer__profile').order_by('-id')
    return render(request, 'core/marketplace.html', {'products': products})


@login_required
def add_product_view(request):
    if request.method == 'POST':
        seller_name = request.POST.get('seller_name', '').strip()
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price', '').strip()
        unit = request.POST.get('unit', 'kg')
        quantity = request.POST.get('quantity', '').strip()
        contact_number = request.POST.get('contact_number', '').strip()
        whatsapp_number = request.POST.get('whatsapp_number', '').strip()
        uploaded_images = request.FILES.getlist('images')

        primary_image = request.FILES.get('product_image')
        if not uploaded_images and primary_image:
            uploaded_images = [primary_image]

        if not title or not price or not quantity or not contact_number:
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'core/add-product.html', {
                'seller_name': seller_name,
                'title': title,
                'description': description,
                'price': price,
                'unit': unit,
                'quantity': quantity,
                'contact_number': contact_number,
                'whatsapp_number': whatsapp_number,
            })

        try:
            product = Product.objects.create(
                farmer=request.user,
                seller_name=seller_name,
                title=title,
                description=description,
                price=price,
                unit=unit,
                quantity=quantity,
                contact_number=contact_number,
                whatsapp_number=whatsapp_number,
                product_image=uploaded_images[0] if uploaded_images else None
            )

            for img in uploaded_images:
                ProductImage.objects.create(product=product, image=img)

            messages.success(request, "Product listed in marketplace successfully!")
            return redirect('marketplace')

        except Exception as e:
            messages.error(request, f"Error creating product listing: {str(e)}")
            return redirect('add_product')

    return render(request, 'core/add-product.html')


@login_required
def edit_product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.farmer != request.user and not is_admin(request.user):
        messages.error(request, "You do not have permission to edit this listing.")
        return redirect('marketplace')

    if request.method == 'POST':
        product.seller_name = request.POST.get('seller_name', product.seller_name)
        product.title = request.POST.get('title', product.title)
        product.price = request.POST.get('price', product.price)
        product.unit = request.POST.get('unit', product.unit)
        product.quantity = request.POST.get('quantity', product.quantity)
        product.description = request.POST.get('description', product.description)
        product.contact_number = request.POST.get('contact_number', product.contact_number)
        product.whatsapp_number = request.POST.get('whatsapp_number', product.whatsapp_number)

        uploaded_images = request.FILES.getlist('images')
        single_image = request.FILES.get('product_image')

        if single_image:
            product.product_image = single_image

        product.save()

        for img in uploaded_images:
            ProductImage.objects.create(product=product, image=img)

        messages.success(request, "Product listing updated successfully!")
        return redirect('marketplace')

    return render(request, 'core/edit_product.html', {'product': product})


@login_required
def delete_product_image_view(request, image_id):
    image = get_object_or_404(ProductImage, id=image_id)
    product = image.product

    if product.farmer == request.user or is_admin(request.user):
        image.delete()
        messages.success(request, "Image deleted successfully.")
    else:
        messages.error(request, "Permission denied.")

    return redirect('edit_product', product_id=product.id)


@login_required
def delete_product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.farmer == request.user or is_admin(request.user):
        product.delete()
        messages.success(request, "Product listing deleted.")
    else:
        messages.error(request, "Permission denied.")
    return redirect('marketplace')


# ==========================================
# CROP MANAGEMENT
# ==========================================

@login_required
def add_crop_view(request):
    if request.method == 'POST':
        form = CropForm(request.POST, request.FILES)
        if form.is_valid():
            crop = form.save(commit=False)
            crop.farmer = request.user
            crop.save()
            messages.success(request, "Crop registered successfully!")
            return redirect('dashboard')
    else:
        form = CropForm()

    return render(request, 'core/add-crop.html', {'form': form})


@login_required
def crop_list_view(request):
    crops = Crop.objects.filter(farmer=request.user)
    return render(request, 'core/crop-list.html', {'crops': crops})


# ==========================================
# ADMIN & USER CONTROL PANEL
# ==========================================

@user_passes_test(is_admin)
def farmer_list_view(request):
    farmers = User.objects.filter(is_superuser=False).select_related('profile')
    return render(request, 'core/farmer-list.html', {'farmers': farmers})


@user_passes_test(is_admin)
def add_farmer_view(request):
    if request.method == 'POST':
        form = FarmerCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Farmer created successfully!")
            return redirect('farmer_list')
    else:
        form = FarmerCreationForm()

    return render(request, 'core/add_farmer.html', {'form': form})


@user_passes_test(is_admin)
def toggle_user_block_view(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if not target_user.is_superuser:
        target_user.is_active = not target_user.is_active
        target_user.save()
        status = "unblocked" if target_user.is_active else "blocked"
        messages.success(request, f"User {target_user.username} has been {status}.")
    return redirect('farmer_list')


@user_passes_test(is_admin)
def delete_user_view(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if not target_user.is_superuser:
        target_user.delete()
        messages.success(request, "User account deleted successfully.")
    return redirect('farmer_list')


# ==========================================
# SITE UPDATES / NEWS MANAGEMENT (ADMIN)
# ==========================================

@user_passes_test(is_admin)
def add_site_update_view(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        if title and content:
            SiteUpdate.objects.create(title=title, content=content)
            messages.success(request, "New site update published!")
            return redirect('homepage')
        else:
            messages.error(request, "Title and Content are required.")
    return render(request, 'core/add_site_update.html')


@user_passes_test(is_admin)
def delete_site_update_view(request, update_id):
    update = get_object_or_404(SiteUpdate, id=update_id)
    update.delete()
    messages.success(request, "Site update removed.")
    return redirect('homepage')


# ==========================================
# PASSWORD RESET VIA EMAIL OTP
# ==========================================

def forgot_password_request_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        # Look up user by email address
        user = User.objects.filter(email__iexact=email).first()
        
        if user and user.email:
            profile, _ = Profile.objects.get_or_create(user=user)
            otp = profile.generate_otp()  # Generates 6-digit OTP
            
            try:
                # Send email via Gmail SMTP
                send_mail(
                    subject="AGRO Portal - Password Reset OTP",
                    message=f"Hello {user.first_name or user.username},\n\nYour OTP code to reset your password is: {otp}\n\nIf you did not request this, please ignore this message.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],  # <--- Sends directly to Gmail
                    fail_silently=False,
                )
                
                request.session['reset_user_id'] = user.id
                messages.success(request, f"Password reset OTP sent to Gmail ({user.email}).")
                return redirect('forgot_password_verify')
                
            except Exception as e:
                messages.error(request, f"Failed to send email: {str(e)}. Please check your network connection.")
                return redirect('forgot_password_request')
        else:
            messages.error(request, "No account found with that email address.")
            
    return render(request, 'core/forgot_password_request.html')


def forgot_password_verify_view(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('forgot_password_request')
        
    user = get_object_or_404(User, id=user_id)
    profile = getattr(user, 'profile', None)

    if not profile:
        messages.error(request, "Profile record error.")
        return redirect('forgot_password_request')

    if request.method == 'POST':
        input_otp = request.POST.get('otp', '').strip()
        new_password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if input_otp != profile.email_otp:
            messages.error(request, "Invalid OTP code.")
        elif new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
        else:
            try:
                password_validation.validate_password(new_password, user)
                user.set_password(new_password)
                user.save()
                profile.email_otp = None
                profile.save()
                
                request.session.pop('reset_user_id', None)
                messages.success(request, "Password reset successfully! You can now log in.")
                return redirect('login')
            except ValidationError as err:
                for error in err.messages:
                    messages.error(request, error)

    return render(request, 'core/forgot_password_verify.html', {'email': user.email})