from datetime import date
from django.db import models
from .utils import get_stock_json, add_freight, extract_freight, FILE_TYPE_MAPPING, MONTH_MAPPING  # Import the extraction functions




class PDFUpload(models.Model):
    file = models.FileField(upload_to='pdfs/')
    extracted_data = models.JSONField(blank=True, null=True)  # Store the extracted data as JSON
    uploaded_at = models.DateTimeField(auto_now_add=True)  # Timestamp for the upload
    file_type = models.CharField(max_length=64, choices=FILE_TYPE_MAPPING.items(), blank=True, null=False)
    month = models.CharField(max_length=64, choices=MONTH_MAPPING.items(), blank=True, null=False)
    year = models.PositiveIntegerField(blank=True, default=date.today().year)

    def save(self, *args, **kwargs):
        # Call the parent save method first
        add_freight_flag = kwargs.pop('add_freight_flag', False)
        super().save(*args, **kwargs)

        # Perform data extraction after the record is saved
        if self.file and not self.extracted_data:
            if self.file_type == "freight_file":
                self.extracted_data = extract_freight(self.file.path)  # Extract freight data
            elif self.file_type == "stock_point_file" or self.file_type == "ex_work_file":
                self.extracted_data = get_stock_json(self.file.path, file_type=self.file_type)  # Extract stock point data
            # Add other conditions for additional file types as needed
            self.save(update_fields=['extracted_data'])  # Save the extracted data

        # Check for the presence of all file types of the same month and year
        if not add_freight_flag:
            same_month_year_files = PDFUpload.objects.filter(month=self.month, year=self.year)
            if same_month_year_files.count() >= 3:
                add_freight(same_month_year_files)
