import random
import re
from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    
    # Helpful website link fields
    helpful_website_title = models.CharField(max_length=200, blank=True, null=True)
    helpful_website_url = models.URLField(max_length=500, blank=True, null=True)
    
    email_otp = models.CharField(max_length=6, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)

    def generate_otp(self):
        otp = str(random.randint(100000, 999999))
        self.email_otp = otp
        self.save()
        return otp

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Crop(models.Model):
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crops')
    crop_name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True, null=True)
    sowing_date = models.DateField()
    estimated_yield = models.CharField(max_length=100, blank=True, null=True)
    field_size = models.CharField(max_length=50, blank=True, null=True)
    image = models.ImageField(upload_to='crop_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.crop_name} - {self.farmer.username}"


class Product(models.Model):
    UNIT_CHOICES = [
        ('kg', 'per KG'),
        ('gram', 'per Gram'),
        ('quintal', 'per Quintal'),
        ('ton', 'per Ton'),
        ('piece', 'per Piece'),
        ('pack', 'per Pack'),
    ]

    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    seller_name = models.CharField(max_length=150, blank=True, null=True, help_text="Custom name for the seller/farmer")
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='kg')
    quantity = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    whatsapp_number = models.CharField(max_length=15, blank=True, null=True)
    product_image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def get_seller_name(self):
        """Returns custom seller name if set, else full name, else username."""
        if self.seller_name and self.seller_name.strip():
            return self.seller_name
        full_name = self.farmer.get_full_name()
        return full_name if full_name.strip() else self.farmer.username

    @property
    def get_contact_number(self):
        """Returns product contact number, or falls back to farmer's profile phone."""
        if self.contact_number:
            return self.contact_number
        if hasattr(self.farmer, 'profile') and self.farmer.profile.phone:
            return self.farmer.profile.phone
        return "N/A"

    @property
    def get_whatsapp_number(self):
        if self.whatsapp_number:
            return re.sub(r'\D', '', str(self.whatsapp_number))
        return ''

    def __str__(self):
        return f"{self.title} - ₹{self.price}/{self.unit}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.title}"


class Scheme(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    eligibility = models.TextField()
    benefits = models.TextField()
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title


class SiteUpdate(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
class HelpfulWebsite(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    url = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title