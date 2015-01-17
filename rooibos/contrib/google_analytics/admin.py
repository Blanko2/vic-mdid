from django.contrib import admin
from django.contrib.sites.admin import SiteAdmin
from django.contrib.sites.models import Site
from google_analytics.models import Analytics

class AnalyticsAdmin(admin.TabularInline):
    model = Analytics
    extra = 1
    max_num = 1
    #fk_name = 'user'

class AnalyticsSiteAdmin(SiteAdmin):
    inlines = [AnalyticsAdmin]

admin.site.unregister(Site)
admin.site.register(Site, AnalyticsSiteAdmin)
