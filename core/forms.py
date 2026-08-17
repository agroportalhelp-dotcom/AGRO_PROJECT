from django import forms
from django.contrib.auth.models import User
from .models import Crop, Product, Profile
from .models import Crop, Product, Profile, HelpfulWebsite  # Ensure HelpfulWebsite is imported

class HelpfulWebsiteForm(forms.ModelForm):
    class Meta:
        model = HelpfulWebsite
        fields = ['title', 'description', 'url']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Portal/Website Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description of the resource...'}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
        }
        
CATEGORY_CHOICES = [
    ('', '-- Select Category --'),
    ('Cereals', 'Cereals & Grains'),
    ('Pulses', 'Pulses & Legumes'),
    ('Vegetables', 'Vegetables'),
    ('Fruits', 'Fruits'),
    ('Oilseeds', 'Oilseeds'),
    ('Cash Crops', 'Cash Crops'),
]

CROP_CHOICES = [
    ('', '-- Select Crop Name --'),
    # Cereals
    ('Wheat', 'Wheat'),
    ('Rice', 'Rice / Paddy'),
    ('Maize', 'Maize (Corn)'),
    ('Barley', 'Barley'),
    ('Bajra', 'Pearl Millet (Bajra)'),
    # Pulses
    ('Chickpea', 'Chickpea (Gram)'),
    ('Pigeon Pea', 'Pigeon Pea (Arhar/Tur)'),
    ('Lentils', 'Lentils (Masoor)'),
    ('Moong', 'Green Gram (Moong)'),
    # Vegetables
    ('Tomato', 'Tomato'),
    ('Potato', 'Potato'),
    ('Onion', 'Onion'),
    ('Brinjal', 'Brinjal (Eggplant)'),
    ('Cauliflower', 'Cauliflower'),
    # Fruits
    ('Banana', 'Banana'),
    ('Mango', 'Mango'),
    ('Apple', 'Apple'),
    ('Pomegranate', 'Pomegranate'),
    # Oilseeds & Cash Crops
    ('Mustard', 'Mustard'),
    ('Soybean', 'Soybean'),
    ('Cotton', 'Cotton'),
    ('Sugarcane', 'Sugarcane'),
]

class CropForm(forms.ModelForm):
    class Meta:
        model = Crop
        fields = ['crop_name', 'category', 'sowing_date', 'estimated_yield', 'field_size', 'image']
        widgets = {
            'category': forms.Select(choices=CATEGORY_CHOICES, attrs={'class': 'form-select', 'id': 'id_category'}),
            'crop_name': forms.Select(choices=CROP_CHOICES, attrs={'class': 'form-select', 'id': 'id_crop_name'}),
            'sowing_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estimated_yield': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 50 Quintals'}),
            'field_size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2.5 Acres'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'description', 'price', 'quantity', 'product_image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Crop Name/Product Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Details about quality, harvest time...'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price in ₹'}),
            'quantity': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 150 kg'}),
            'product_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone', 'state', 'district', 'city', 'helpful_website_title', 'helpful_website_url']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter mobile number'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'District'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'helpful_website_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., PM Kisan Portal'}),
            'helpful_website_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://pmkisan.gov.in'}),
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class FarmerCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            # Safely create or retrieve the profile object
            profile, created = Profile.objects.get_or_create(user=user)
            profile.phone = self.cleaned_data["phone"]
            profile.save()
        return user