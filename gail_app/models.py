# models.py
from django.db import models
from .utils import get_stock_json  # Import the extraction function

class PDFUpload(models.Model):
    file = models.FileField(upload_to='pdfs/')
    extracted_data = models.JSONField(blank=True, null=True)  # Store the extracted data as JSON
    uploaded_at = models.DateTimeField(auto_now_add=True)  # Timestamp for the upload

    def save(self, *args, **kwargs):
        # Call the parent save method first
        super().save(*args, **kwargs)

        # If the file is newly uploaded and extraction is needed
        if self.file and not self.extracted_data:
            extracted_data = get_stock_json(pdf_file=self.file.path)  # Automatically extract data
            self.extracted_data = extracted_data
            super().save(*args, **kwargs)  # Save the instance with the extracted data
