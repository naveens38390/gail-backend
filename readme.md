# GAIL - STOCK POINT LOCATION, EX WORK LOCATION, POLYMER PRICE SHEET EXTRACTER AND SERVER

## Installation
!> Note: Install JDK and ghostscript `sudo apt install -y default-jdk && sudo apt install -y ghostscript`

1. `git clone git@github.com:beingtharur/gail-backend.git`

2. `python3 -m venv env`

3. `source env/bin/activate`

4. `pip install -r requirements.txt`

5. `python3 manage.py migrate`

6. `python3 manage.py createsuperuser` [create superuser]

7. `python3 manage.py runserver 0.0.0.0:8000`



## Note

Upload the files

file_types:
    "stock_point_file" --> "STOCK POINT FILE"
    "freight_file"     --> "FREIGHT FILE"
    "ex_work_file"     --> "EX WORK FILE"

To get data of stock point file of november 2024: http://0.0.0.0:8000/api/pdf/file-data/?file_type=stock_point_file&month=november&year=2024

To get data of freight file of november 2024: http://0.0.0.0:8000/api/pdf/file-data/?file_type=freight_file&month=november&year=2024

To get data of freight file of november 2024: http://0.0.0.0:8000/api/pdf/file-data/?file_type=ex_work_file&month=november&year=2024





# Gail App - PDF/Excel Data Extraction API

## Overview

The Gail App is a Django-based REST API designed to:

* Upload and process PDF and Excel files.
* Automatically extract structured JSON data from files.
* Combine data from multiple file types (Stock Point, Ex-Work, and Freight).
* Enrich data with freight charges when all required files are present.

## API Endpoints

### 1. Upload a PDF or Excel File

**POST** `/api/pdf/upload/`

#### Parameters (form-data):

* `file` (File): The file to upload.
* `file_type` (String): One of `stock_point_file`, `ex_work_file`, or `freight_file`.
* `month` (String): The month (e.g., `january`).
* `year` (Integer): The year (e.g., `2024`).

#### Response:

Returns JSON data of the extracted content.

### 2. Retrieve Extracted File Data

**GET** `/api/pdf/file-data/`

#### Query Parameters:

* `file_type` (String): One of `stock_point_file`, `ex_work_file`, or `freight_file`.
* `month` (String): The month.
* `year` (Integer): The year.

#### Response:

Returns the extracted JSON data for the specified file.

## Data Extraction Logic

### Stock Point & Ex-Work Files:

* Parsed using `tabula` or `camelot` (fallback).
* Transforms tabular data into structured JSON with locations, SAP codes, and product pricing.

### Freight File:

* Parsed using `pandas` from an Excel file.
* Extracts city-based freight charge mappings.

### Auto-Merging Freight Data:

When all three file types for a specific month and year are present:

* Freight charges are matched to `stock_point_file` and `ex_work_file` entries based on location.
* Uses string matching and Levenshtein similarity to ensure robust matching.
* Adds a `freight_amount` field to each location entry.

## Models

### `PDFUpload`

Represents each uploaded file.

Fields:

* `file`: Uploaded file.
* `file_type`: Type of file.
* `month`, `year`: Time context.
* `extracted_data`: JSON result of the parsed content.
* `uploaded_at`: Auto-generated timestamp.

## Admin Interface

Custom admin panel allows filtering and searching uploads by:

* File type
* Month
* Year

## Project Structure

```
project/
├── gail_app/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   ├── utils.py
│   └── admin.py
├── project/
│   └── urls.py
└── manage.py
```

## Setup & Dependencies

* Python 3.x
* Django
* Django REST Framework
* tabula-py
* camelot-py
* pandas
* python-Levenshtein

## Notes

* Ensure Java is installed for `tabula-py`.
* Use correct column naming in Excel and PDF templates.

---

Feel free to extend this with authentication, pagination, or frontend support based on project needs.
