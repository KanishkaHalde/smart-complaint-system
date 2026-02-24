from django.contrib import admin
from .models import Complaint, ComplaintFile, Notification

class ComplaintFileInline(admin.TabularInline):
    model = ComplaintFile
    extra = 0
    readonly_fields = ['name', 'file', 'uploaded_at']

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['complaint_id', 'user', 'complaint_type', 'status', 'urgency', 'submitted_at']
    list_filter = ['status', 'urgency', 'complaint_type', 'submitted_at']
    search_fields = ['complaint_id', 'user__username', 'user__email', 'details', 'location']
    inlines = [ComplaintFileInline]
    readonly_fields = ['complaint_id', 'submitted_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('complaint_id', 'user', 'name', 'roll')
        }),
        ('Complaint Details', {
            'fields': ('complaint_type', 'urgency', 'location', 'details')
        }),
        ('Status', {
            'fields': ('status', 'reminder_sent', 'reminder_sent_at')
        }),
        ('GPS Location', {
            'fields': ('latitude', 'longitude', 'gps_accuracy'),
            'classes': ('collapse',)
        }),
        ('Feedback', {
            'fields': ('rating', 'feedback', 'feedback_submitted_at'),
            'classes': ('collapse',)
        }),
        ('Reopen Info', {
            'fields': ('reopened', 'reopen_reason', 'reopen_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'type', 'read', 'created_at']
    list_filter = ['type', 'read', 'created_at']
    search_fields = ['title', 'message', 'user__username']
    readonly_fields = ['created_at']