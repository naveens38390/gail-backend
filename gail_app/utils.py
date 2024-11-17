# utils.py
import json
import tabula  # Correct import for tabula-py
import camelot
import pandas as pd
from pprint import pprint
from Levenshtein import ratio
from collections import defaultdict


FILE_TYPE_MAPPING = {
    "stock_point_file": "STOCK POINT FILE",
    "freight_file": "FREIGHT FILE",
    "ex_work_file": "EX WORK FILE"
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
        if col.strip():  # Ignore empty strings
            # Check if predefined headers exist in the string and add them individually
            if any(header in col for header in predefined_headers):
                for header in predefined_headers:
                    if max([word_similarity(header, col_word) for col_word in ordered_combinations(col.split(" "))]) > 0.8:
                        cleaned_row.append(header)
            else:
                cleaned_row.append(col.strip())  # Add other valid elements
    return cleaned_row


def get_stock_json(pdf_file: str = None, save_json_path: str = None, file_type:str=None):
    # Read PDF file
    print("Reading PDF file...")
    dfs = tabula.read_pdf(pdf_file, pages="all", multiple_tables=True)  # Load all pages (multiple tables)
    
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

            # Drop duplicates
            df = df.drop_duplicates()
            print("Dropped duplicate rows.")

            # Extract data from DataFrame and store it in formatted_data
            main_col = None
            for row_index, row in df.iterrows():
                if main_row_val in str(row.values[0:5]):
                    main_col = row
                    break
            
            try:
                main_col.values.tolist().index(main_row_val)
            except ValueError as ve:
                df = camelot.read_pdf(pdf_file, pages=f"{table_index+1}")[0].df
                main_col = None
                for row_index, row in df.iterrows():
                    if main_row_val in str(row.values[0:5]):
                        main_col = row
                        break
            
            main_col = pd.Series(clean_header(main_col.values))
            
            print("main_row_val: ", main_col.values.tolist())
            print("df: \n", df)
            flag = False
            for icol in range(main_col.values.tolist().index(main_row_val.strip()) + 1, len(main_col)):
                print("main_row_val: ", main_row_val)
                print("icol: ", main_col.values.tolist().index(main_row_val.strip()))
                for row_index, row in df.iterrows():
                    print("row: ", row.values, icol)
                    if flag == False and main_row_val in str(row.values[0:5]):
                        flag = True
                        continue

                    if flag:
                        if main_col.values[icol].replace(' ', '') in formatted_data:
                            formatted_data[main_col.values[icol].replace(' ', '')].append({
                                "sap_code": row.values[1],
                                main_key_val: row.values[2],
                                "price": int(row.values[icol].replace(',', '').replace(' ', ''))
                            })
                        else:
                            formatted_data[main_col.values[icol].replace(' ', '')] = [{
                                "sap_code": row.values[1],
                                main_key_val: row.values[2],
                                "price": int(row.values[icol].replace(',', '').replace(' ', ''))
                            }]
                flag = False
            
            main_col = None
    else:
        print("Error: PDF did not return a list of tables as expected.")

    # Print formatted data output for debugging
    print("\nFormatted data output:")    
    pprint(len(formatted_data.keys()))

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

    # Convert location_data to the desired list format and assign it to the output
    output_json["data"] = list(location_data.values())

    # Print final transformed data
    print("\nTransformed JSON data output:")
    pprint(output_json)

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



def add_freight(same_month_records):
    """
    "stock_point_file": "STOCK POINT FILE",
    "freight_file": "FREIGHT FILE",
    "ex_work_file": "EX WORK FILE"
    """
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
    
    """
    freight:
    {
        "AGRA": {
            "Amount": 928.72,
            "Unit": "INR",
            "Per": 1,
            "UoM": "TO",
            "Valid_From": "01.06.2022",
            "Valid_To": "31.12.9999"
        },
        "AHMEDABAD": {
            "Amount": 1737.32,
            "Unit": "INR",
            "Per": 1,
            "UoM": "TO",
            "Valid_From": "01.06.2022",
            "Valid_To": "31.12.9999"
        },...
    }

    stock_point:
    {
        "data": [
            {
                "id": 1,
                "sap_code": "5102",
                "location": "GAZIABAD/NOIDA",
                "products": [
                    {
                        "product_code": "B52A003A",
                        "price": 99650
                    },
                    {
                        "product_code": "B55HM0003A",
                        "price": 102000
                    },
                    {
                        "product_code": "B56A003A",
                        "price": 97150
                    },
                    { .... },
                    ...
                ]
            }, ...
        ]
    }

    ex work: 
    {
        "data": [
            {
                "id": 1,
                "sap_code": "5102",
                "location": "GAZIABAD/NOIDA",
                "products": [
                    {
                        "product_code": "B52A003A",
                        "price": 99650
                    },
                    {
                        "product_code": "B55HM0003A",
                        "price": 102000
                    },
                    {
                        "product_code": "B56A003A",
                        "price": 97150
                    },
                    { .... },
                    ...
                ]
            }, ...
        ]
    }

    """
    
    print("Add Freight ...")
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

    stock_point_record.save(add_freight_flag = True)
    ex_work_record.save(add_freight_flag = True)

            
