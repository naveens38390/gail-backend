import json
import tabula  # Correct import for tabula-py
import camelot
import pandas as pd
from pprint import pprint
from Levenshtein import ratio
from collections import defaultdict
import os


FILE_TYPE_MAPPING = {
    "stock_point_file": "STOCK POINT FILE",
    "freight_file": "FREIGHT FILE",
    "ex_work_file": "EX WORK FILE",
    "competitor_file": "CROSS REFERENC FILE"
}

MONTH_MAPPING = {
    "january"    : "january",
    "february"   : "february",
    "march"      : "march",
    "april"      : "april",
    "may"        : "may",
    "june"       : "june",
    "july"       : "july",
    "august"     : "august",
    "september"  : "september",
    "october"    : "october",
    "november"   : "november",
    "december"   : "december"
}


def word_similarity(word1, word2):
    """
    Computes the similarity score between two words based on Levenshtein Ratio.

    Args:
        word1 (str): The first word.
        word2 (str): The second word.

    Returns:
        float: A similarity score between 0 and 1. Higher scores indicate more similarity.
    """
    # Ensure both inputs are strings
    word1, word2 = str(word1), str(word2)
    # Calculate similarity ratio
    similarity = ratio(word1, word2)
    return similarity

def ordered_combinations(word_list, spacer:str=" "):
    # A, B, C, D, E
    # AB, AC, AD, AE
    # BC, BD, BE
    # CD, CE
    # DE
    # E
    all_ordered_words = []
    for j in range(len(word_list)-1):
        for i in range(1, len(word_list)):
            if i < len(word_list) and i > j:
                all_ordered_words.append(word_list[j]+spacer+word_list[i])
    all_ordered_words.append(word_list[-1])
    return all_ordered_words

def clean_header(row):
    """
    Cleans the header row by identifying predefined strings and fixing their structure.

    Args:
        row (list): A list representing the header row.

    Returns:
        list: A cleaned list with predefined column names properly separated.
    """
    predefined_headers = ['Sl. No.', 'SAP CODE', 'LOCATION/GRADE', 'STOCKPOINT LOCATION']
    cleaned_row = []

    print("row (clean_header): ", row)

    for col in row:
        col_str = str(col).strip()
        if col_str and col_str != 'nan':  # Ignore empty strings and NaN values
            # Check if predefined headers exist in the string and add them individually
            if any(header in col_str for header in predefined_headers):
                for header in predefined_headers:
                    if max([word_similarity(header, col_word) for col_word in ordered_combinations(col_str.split(" "))]) > 0.8:
                        cleaned_row.append(header)
            else:
                cleaned_row.append(col_str)  # Add other valid elements
    return cleaned_row


def detect_file_format(file_path):
    """
    Detect the format of the uploaded file based on extension.
    """
    _, ext = os.path.splitext(file_path.lower())
    if ext in ['.xlsx', '.xls']:
        return 'excel'
    elif ext == '.csv':
        return 'csv'
    else:
        return 'unknown'


def extract_cross_reference(file_path):
    """
    Extract cross-reference data from Excel/CSV files.
    Fixed to handle the exact structure of your Excel file.
    
    Args:
        file_path (str): Path to the Excel/CSV file.
    
    Returns:
        dict: Dictionary containing cross-reference mappings and metadata.
    """
    print(f"=== EXTRACTING CROSS-REFERENCE DATA ===")
    print(f"File path: {file_path}")
    
    try:
        file_format = detect_file_format(file_path)
        print(f"File format: {file_format}")
        
        if file_format == 'excel':
            df = pd.read_excel(file_path)
        elif file_format == 'csv':
            df = pd.read_csv(file_path)
        else:
            return {"error": f"Unsupported file format: {file_format}"}
        
        print(f"File loaded successfully. Shape: {df.shape}")
        print(f"Original columns: {df.columns.tolist()}")
        
        # Clean column names and remove extra spaces
        df.columns = df.columns.astype(str).str.strip()
        print(f"Cleaned columns: {df.columns.tolist()}")
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        print(f"After removing empty rows - Shape: {df.shape}")
        
        cross_reference_data = {
            "companies": [],
            "mappings": {},
            "metadata": {
                "total_companies": 0,
                "total_mappings": 0,
                "file_format": file_format
            }
        }
        
        if df.empty or len(df.columns) < 5:
            print(f"❌ Not enough columns or empty DataFrame")
            return cross_reference_data
        
        
        gail_column = df.columns[1]  # "GAIL Grade" column
        competitor_columns = df.columns[4:11].tolist()  # Columns 4-10 are the competitors
        
        print(f"GAIL column: '{gail_column}'")
        print(f"Competitor columns: {competitor_columns}")
        
        # Clean competitor column names and store them
        competitor_columns = [col.strip() for col in competitor_columns if col.strip()]
        cross_reference_data["companies"] = competitor_columns
        cross_reference_data["metadata"]["total_companies"] = len(competitor_columns)
        
        print(f"Processing {len(competitor_columns)} competitor columns...")
        
        mappings_count = 0
        b56_found = False
        
        for index, row in df.iterrows():
            # Get GAIL grade (product code)
            gail_grade = str(row[gail_column]).strip()
            
            # Debug B56A003A specifically
            if 'B56A003' in gail_grade:
                print(f"Row {index}: Found B56A003 variant: '{gail_grade}'")
                b56_found = True
                
                # Check all competitor values for this row
                for comp_col in competitor_columns:
                    if comp_col in df.columns:
                        comp_value = str(row[comp_col]).strip() if pd.notna(row[comp_col]) else 'NaN'
                        print(f"  {comp_col}: '{comp_value}'")
            
            # Skip if GAIL grade is empty or invalid
            if (pd.isna(row[gail_column]) or 
                not gail_grade or 
                gail_grade.lower() in ['nan', 'null', '', 'gail grade']):
                continue
            
            if gail_grade not in cross_reference_data["mappings"]:
                cross_reference_data["mappings"][gail_grade] = {}
            
            # Process each competitor column
            for competitor in competitor_columns:
                if competitor not in df.columns:
                    print(f"Warning: Competitor column '{competitor}' not found in DataFrame")
                    continue
                    
                competitor_grade = str(row[competitor]).strip()
                
                # Skip if competitor grade is empty, NaN, or "No equivalent"
                if (pd.isna(row[competitor]) or 
                    not competitor_grade or 
                    competitor_grade.lower() in ['nan', 'null', '', 'no equivalent', '(blank)']):
                    continue
                
                # Handle multiple grades with various delimiters
                competitor_grades = []
                for delimiter in [',', ';', '|', '\n', '/']:
                    if delimiter in competitor_grade:
                        competitor_grades = [grade.strip() for grade in competitor_grade.split(delimiter)]
                        break
                else:
                    competitor_grades = [competitor_grade]
                
                # Filter out empty and invalid grades
                competitor_grades = [
                    grade for grade in competitor_grades 
                    if grade and grade.lower() not in ['nan', 'null', '', 'no equivalent', 'n/a', '(blank)']
                ]
                
                if competitor_grades:
                    cross_reference_data["mappings"][gail_grade][competitor] = competitor_grades
                    mappings_count += len(competitor_grades)
        
        print(f"B56A003A variants found during processing: {b56_found}")
        print(f"Final mappings for B56A003A: {cross_reference_data['mappings'].get('B56A003A', 'NOT FOUND')}")
        
        cross_reference_data["metadata"]["total_mappings"] = mappings_count
        
        print(f"=== EXTRACTION RESULTS ===")
        print(f"- Total grades: {len(cross_reference_data['mappings'])}")
        print(f"- Total mappings: {mappings_count}")
        print(f"- Companies: {cross_reference_data['companies']}")
        
        # Show sample of mappings
        sample_grades = list(cross_reference_data['mappings'].keys())[:5]
        print(f"- Sample grades: {sample_grades}")
        
        return cross_reference_data
        
    except Exception as e:
        print(f"❌ Error extracting cross-reference data: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Failed to extract cross-reference data: {str(e)}"}
    
def save_cross_reference_to_db(excel_upload_instance):
    """
    Save cross-reference data to individual CrossReference model instances.
    This makes querying much faster and more efficient.
    """
    from .models import CrossReference  # Import here to avoid circular imports
    
    if not excel_upload_instance.extracted_data or 'mappings' not in excel_upload_instance.extracted_data:
        return
    
    # Clear existing cross-references for this upload
    CrossReference.objects.filter(excel_upload=excel_upload_instance).delete()
    
    # Create new cross-reference entries
    cross_references = []
    mappings = excel_upload_instance.extracted_data['mappings']
    
    for gail_grade, competitors in mappings.items():
        for competitor_name, competitor_grades in competitors.items():
            for competitor_grade in competitor_grades:
                cross_references.append(
                    CrossReference(
                        gail_grade=gail_grade,
                        competitor_name=competitor_name,
                        competitor_grade=competitor_grade,
                        excel_upload=excel_upload_instance
                    )
                )
    
    # Bulk create for efficiency
    CrossReference.objects.bulk_create(cross_references, batch_size=1000)
    print(f"Created {len(cross_references)} cross-reference entries in database.")

# First install pdfplumber (no Java required)
# pip install pdfplumber

def get_stock_json(pdf_file: str = None, save_json_path: str = None, file_type: str = None):
    """
    Extract stock point data from PDF using pure Python (no Java required).
    """
    print("Reading PDF file...")
    
    try:
        # Use pdfplumber (pure Python, no Java needed)
        import pdfplumber
        import pandas as pd
        
        print("Attempting PDF extraction with pdfplumber (no Java required)...")
        
        all_tables = []
        with pdfplumber.open(pdf_file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                print(f"Processing page {page_num + 1}...")
                
                # Extract tables from page
                tables = page.extract_tables()
                
                for table_index, table in enumerate(tables):
                    if table and len(table) > 1:  # Ensure table has data
                        try:
                            # Convert table to DataFrame
                            # First row as header, rest as data
                            headers = table[0] if table else []
                            data_rows = table[1:] if len(table) > 1 else []
                            
                            if headers and data_rows:
                                df = pd.DataFrame(data_rows, columns=headers)
                                all_tables.append(df)
                                print(f"Found table with {len(df)} rows on page {page_num + 1}")
                        except Exception as e:
                            print(f"Error processing table {table_index} on page {page_num + 1}: {e}")
                            continue
        
        if not all_tables:
            return {
                "error": "No tables found in PDF",
                "suggestion": "Please check if the PDF contains structured table data"
            }
        
        dfs = all_tables
        print(f"Successfully extracted {len(dfs)} tables using pdfplumber!")
        
    except ImportError:
        return {
            "error": "pdfplumber not installed",
            "solution": "Run: pip install pdfplumber"
        }
    except Exception as e:
        print(f"PDF extraction failed: {e}")
        return {
            "error": "PDF extraction failed",
            "details": str(e),
            "suggestion": "Please check if the PDF file is valid and contains table data"
        }
    
    # REST OF YOUR ORIGINAL PROCESSING LOGIC STAYS THE SAME
    print("PDF file read successfully.\n")
    main_row_val = "LOCATION/GRADE" if file_type == "ex_work_file" else "STOCKPOINT LOCATION"
    main_key_val = "location_grade" if file_type == "ex_work_file" else "stockpoint_location"

    # Initialize dictionary to store formatted records
    formatted_data = {}

    # Check if dfs is a list of DataFrames
    if isinstance(dfs, list):
        print("Processing each table found in the PDF...\n")
        for table_index, df in enumerate(dfs):
            print(f"Processing Table {table_index + 1}:")
            print(f"DataFrame shape: {df.shape}")
            print(f"DataFrame columns: {df.columns.tolist()}")
            print(f"First few rows:\n{df.head()}")
            
            if df.empty:
                print(f"Table {table_index + 1} is empty, skipping...")
                continue

            # Drop duplicates
            df = df.drop_duplicates()
            print("Dropped duplicate rows.")

            # Find the header row
            main_col = None
            header_row_index = None
            
            for row_index, row in df.iterrows():
                row_str = ' '.join([str(val) for val in row.values if str(val) != 'nan' and val is not None])
                print(f"Row {row_index}: {row_str[:100]}...")  # Debug print
                if main_row_val in row_str:
                    main_col = row
                    header_row_index = row_index
                    print(f"Found header row at index {row_index}")
                    break
            
            if main_col is None:
                print(f"Could not find header row in table {table_index + 1}, skipping...")
                continue
            
            # Clean the header
            cleaned_header = clean_header(main_col.values)
            main_col = pd.Series(cleaned_header)
            
            print("Cleaned header: ", main_col.values.tolist())
            
            # Find the index of the main location column
            try:
                main_col_index = main_col.values.tolist().index(main_row_val)
            except ValueError:
                print(f"Could not find '{main_row_val}' in cleaned header, skipping table {table_index + 1}")
                continue
            
            print(f"Main column '{main_row_val}' found at index: {main_col_index}")
            
            # Process data rows (skip header row)
            data_start_row = header_row_index + 1 if header_row_index is not None else 0
            
            # Get the actual number of columns in the dataframe
            num_cols = len(df.columns)
            print(f"DataFrame has {num_cols} columns")
            
            for col_index in range(main_col_index + 1, min(len(main_col), num_cols)):
                if col_index >= len(main_col.values):
                    break
                    
                product_code = main_col.values[col_index]
                if not product_code or str(product_code) == 'nan' or product_code is None:
                    continue
                    
                product_code_clean = str(product_code).replace(' ', '')
                print(f"Processing product code: {product_code_clean}")
                
                for row_index in range(data_start_row, len(df)):
                    try:
                        row = df.iloc[row_index]
                        
                        # Check if we have enough columns for this row
                        if len(row) <= max(1, 2, col_index):
                            print(f"Row {row_index} doesn't have enough columns, skipping")
                            continue
                        
                        # Safe access to columns
                        sap_code_val = row.iloc[1] if len(row) > 1 else None
                        location_val = row.iloc[2] if len(row) > 2 else None
                        price_val = row.iloc[col_index] if len(row) > col_index else None
                        
                        # Skip if any essential data is missing or NaN
                        if (pd.isna(sap_code_val) or pd.isna(location_val) or 
                            pd.isna(price_val) or str(sap_code_val) == 'nan' or 
                            str(location_val) == 'nan' or str(price_val) == 'nan' or
                            sap_code_val is None or location_val is None or price_val is None):
                            continue
                        
                        sap_code = str(sap_code_val).strip()
                        location = str(location_val).strip()
                        price_str = str(price_val).replace(',', '').replace(' ', '')
                        
                        # Skip if any essential data is empty
                        if not sap_code or not location or not price_str:
                            continue
                            
                        price = int(float(price_str))
                        
                        if product_code_clean in formatted_data:
                            formatted_data[product_code_clean].append({
                                "sap_code": sap_code,
                                main_key_val: location,
                                "price": price
                            })
                        else:
                            formatted_data[product_code_clean] = [{
                                "sap_code": sap_code,
                                main_key_val: location,
                                "price": price
                            }]
                    except (ValueError, IndexError) as e:
                        print(f"Error processing row {row_index}, col {col_index}: {e}")
                        continue
    else:
        print("Error: PDF did not return a list of tables as expected.")
        return {"error": "PDF processing failed"}

    # Print formatted data output for debugging
    print("\nFormatted data output:")    
    pprint(f"Found {len(formatted_data.keys())} product codes")

    # Transform formatted_data to desired output format
    output_json = {"data": []}
    location_data = defaultdict(lambda: {"products": []})

    # Process each product code and its associated locations and prices
    for product_code, entries in formatted_data.items():
        for entry in entries:
            # Using (sap_code, location) as a unique key to group entries
            location_key = (entry["sap_code"], entry[main_key_val])
            
            # If the location_key exists, just add the product to it
            if location_key in location_data:
                location_data[location_key]["products"].append({
                    "product_code": product_code,
                    "price": entry["price"]
                })
            else:
                # Otherwise, create a new entry in location_data
                location_data[location_key] = {
                    "id": len(location_data) + 1,  # auto-incrementing id
                    "sap_code": entry["sap_code"],
                    "location": entry[main_key_val],
                    "products": [{
                        "product_code": product_code,
                        "price": entry["price"]
                    }]
                }

    output_json["data"] = list(location_data.values())

    # Print final transformed data
    print("\nTransformed JSON data output:")
    pprint(f"Processed {len(output_json['data'])} locations")

    # Save JSON output if path is provided
    if save_json_path:
        with open(save_json_path, 'w') as json_file:
            json.dump(output_json, json_file, indent=4)

    return output_json

def extract_freight(file_path):
    """
    Extract city-wise mapping from the first sheet of the provided Excel file.

    Args:
        file_path (str): Path to the Excel file.

    Returns:
        dict: Dictionary mapping city names to their attributes.
    """
    try:
        # Load the first sheet of the Excel file
        data = pd.read_excel(file_path)

        # Rename columns for clarity
        data.columns = [
            "No", "CnTy", "Condition_Type", "PL_Number", "City", "Amount",
            "Unit", "Per", "UoM", "Valid_From", "Valid_To"
        ]

        # Drop the first row containing header-like information
        data = data.iloc[1:].reset_index(drop=True)

        # Remove rows where the "City" column or other relevant columns are empty
        data = data.dropna(subset=["City", "Amount", "Unit", "Per", "UoM", "Valid_From", "Valid_To"]).reset_index(drop=True)

        # Create the dictionary mapping
        city_mapping = {
            row["City"]: {
                "Amount": row["Amount"],
                "Unit": row["Unit"],
                "Per": row["Per"],
                "UoM": row["UoM"],
                "Valid_From": row["Valid_From"],
                "Valid_To": row["Valid_To"],
            }
            for _, row in data.iterrows()
        }

        return city_mapping
    except Exception as e:
        print(f"Error extracting freight data: {e}")
        return {"error": f"Failed to extract freight data: {str(e)}"}


def add_freight(same_month_records):
    """
    Add freight data to stock point and ex-work records.
    """
    try:
        stock_point_record = None
        ex_work_record = None
        freight_file_record = None
        
        for record in same_month_records:
            if record.file_type == 'stock_point_file':
                stock_point_record = record
            elif record.file_type == 'freight_file':
                freight_file_record = record
            elif record.file_type == 'ex_work_file':
                ex_work_record = record
        
        if not freight_file_record:
            print("No freight file found for freight calculation")
            return
            
        print("Add Freight ...")
        
        # Process stock point record
        if stock_point_record and stock_point_record.extracted_data:
            done_flag_mem = {}
            for i in range(len(stock_point_record.extracted_data['data'])):
                location = stock_point_record.extracted_data['data'][i]['location']
                for freight_loc, freight_record in freight_file_record.extracted_data.items():
                    if not done_flag_mem.get(location, False):
                        if location.strip().lower() == freight_loc.strip().lower():
                            stock_point_record.extracted_data['data'][i]['freight_amount'] = freight_record['Amount']
                            done_flag_mem[location] = True
                        elif word_similarity(location, freight_loc) >= 0.95:
                            stock_point_record.extracted_data['data'][i]['freight_amount'] = freight_record['Amount']
                            done_flag_mem[location] = True

        # Process ex-work record
        if ex_work_record and ex_work_record.extracted_data:
            done_flag_mem = {}
            for i in range(len(ex_work_record.extracted_data['data'])):
                location = ex_work_record.extracted_data['data'][i]['location']
                for freight_loc, freight_record in freight_file_record.extracted_data.items():
                    if not done_flag_mem.get(location, False):
                        if location.strip().lower() == freight_loc.strip().lower():
                            ex_work_record.extracted_data['data'][i]['freight_amount'] = freight_record['Amount']
                            done_flag_mem[location] = True
                        elif word_similarity(location, freight_loc) >= 0.95:
                            ex_work_record.extracted_data['data'][i]['freight_amount'] = freight_record['Amount']
                            done_flag_mem[location] = True

        # Save the updated records
        if stock_point_record:
            stock_point_record.save(add_freight_flag=True)
        if ex_work_record:
            ex_work_record.save(add_freight_flag=True)
            
    except Exception as e:
        print(f"Error in add_freight: {e}")