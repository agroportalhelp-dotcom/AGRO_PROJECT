from django.contrib import admin
from .models import Profile, Crop, Product, Scheme, SiteUpdate

admin.site.register(Profile)
admin.site.register(Crop)
admin.site.register(Product)
admin.site.register(Scheme)
admin.site.register(SiteUpdate) # Registers updates to control in Admin UI