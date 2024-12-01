from django.contrib import admin
from .models import WatchList

# Register your models here.


@admin.register(WatchList)
class WatchListAdmin(admin.ModelAdmin):
    list_display = ("telegram_user", "contract_address", "symbol")
