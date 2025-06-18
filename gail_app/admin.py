# gail_app/admin.py
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from .models import PDFUpload, ExcelUpload, CrossReference
import os

class PDFUploadForm(ModelForm):
    class Meta:
        model = PDFUpload
        fields = '__all__'
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in ['.pdf']:
                raise ValidationError('Only PDF files are allowed. Please use Excel Upload for .xlsx, .xls, or .csv files.')
        return file

class ExcelUploadForm(ModelForm):
    class Meta:
        model = ExcelUpload
        fields = '__all__'
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in ['.xlsx', '.xls', '.csv']:
                raise ValidationError('Only Excel (.xlsx, .xls) and CSV files are allowed. Please use PDF Upload for .pdf files.')
        return file

@admin.register(PDFUpload)
class PDFUploadAdmin(admin.ModelAdmin):
    form = PDFUploadForm
    list_display = ['id', 'file', 'file_type', 'month', 'year', 'uploaded_at', 'has_extracted_data']
    list_filter = ['file_type', 'month', 'year', 'uploaded_at']
    search_fields = ['file_type', 'month', 'year']
    readonly_fields = ['uploaded_at']
    
    fieldsets = (
        (None, {
            'fields': ('file', 'file_type', 'month', 'year')
        }),
        ('Extracted Data', {
            'fields': ('extracted_data',),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',),
        }),
    )
    
    def has_extracted_data(self, obj):
        return bool(obj.extracted_data)
    has_extracted_data.boolean = True
    has_extracted_data.short_description = 'Data Extracted'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['extracted_data']
        return self.readonly_fields

@admin.register(ExcelUpload)
class ExcelUploadAdmin(admin.ModelAdmin):
    form = ExcelUploadForm
    list_display = ['id', 'file', 'file_type', 'is_active', 'uploaded_at', 'has_extracted_data', 'total_mappings']
    list_filter = ['file_type', 'is_active', 'uploaded_at']
    search_fields = ['file_type']
    readonly_fields = ['uploaded_at']
    actions = ['activate_selected', 'deactivate_selected']
    
    fieldsets = (
        (None, {
            'fields': ('file', 'file_type', 'is_active')
        }),
        ('Extracted Data', {
            'fields': ('extracted_data',),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',),
        }),
    )
    
    def has_extracted_data(self, obj):
        return bool(obj.extracted_data)
    has_extracted_data.boolean = True
    has_extracted_data.short_description = 'Data Extracted'
    
    def total_mappings(self, obj):
        if obj.extracted_data and 'metadata' in obj.extracted_data:
            return obj.extracted_data['metadata'].get('total_mappings', 0)
        return 0
    total_mappings.short_description = 'Total Mappings'
    
    def activate_selected(self, request, queryset):
        # Deactivate all other files of the same type first
        for obj in queryset:
            ExcelUpload.objects.filter(file_type=obj.file_type).update(is_active=False)
            obj.is_active = True
            obj.save()
        self.message_user(request, f"Activated {queryset.count()} files and deactivated others of the same type.")
    activate_selected.short_description = "Activate selected files (deactivates others)"
    
    def deactivate_selected(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {queryset.count()} files.")
    deactivate_selected.short_description = "Deactivate selected files"
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['extracted_data']
        return self.readonly_fields

@admin.register(CrossReference)
class CrossReferenceAdmin(admin.ModelAdmin):
    list_display = ['id', 'gail_grade', 'competitor_name', 'competitor_grade', 'location', 'excel_upload', 'created_at']
    list_filter = ['competitor_name', 'excel_upload', 'created_at']
    search_fields = ['gail_grade', 'competitor_name', 'competitor_grade', 'location']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        # Show only cross-references from active uploads by default
        qs = super().get_queryset(request)
        return qs.select_related('excel_upload')