# # utils.py
# import json
# import tabula  # Correct import for tabula-py
# from pprint import pprint

# def get_stock_json(pdf_file: str = None, save_json_path: str = None):
#     # Read PDF file
#     print("Reading PDF file...")
#     dfs = tabula.read_pdf(pdf_file, pages="all", multiple_tables=True)  # Load all pages (multiple tables)
#     print("PDF file read successfully.\n")

#     # Initialize dictionary to store formatted records
#     formatted_data = {}

#     # Check if dfs is a list of DataFrames
#     if isinstance(dfs, list):
#         print("Processing each table found in the PDF...\n")
#         for table_index, df in enumerate(dfs):
#             print(f"Processing Table {table_index + 1}:")
            
#             # Drop duplicates
#             df = df.drop_duplicates()
#             print("Dropped duplicate rows.")

#             # Extract data from DataFrame and store it in formatted_data
#             main_col = None
#             for row_index, row in df.iterrows():
#                 if "STOCKPOINT LOCATION" in str(row.values[0:5]):
#                     main_col = row
#                     break
            
#             flag = False
#             for icol in range(main_col.values.tolist().index('STOCKPOINT LOCATION') + 1, len(main_col)):
#                 for row_index, row in df.iterrows():
#                     if flag == False and "STOCKPOINT LOCATION" in str(row.values[0:5]):
#                         flag = True
#                         continue

#                     if flag:
#                         if main_col.values[icol].replace(' ', '') in formatted_data:
#                             formatted_data[main_col.values[icol].replace(' ', '')].append({
#                                 "sap_code": row.values[1],
#                                 "stockpoint_location": row.values[2],
#                                 "price": int(row.values[icol].replace(',', '').replace(' ', ''))
#                             })
#                         else:
#                             formatted_data[main_col.values[icol].replace(' ', '')] = [{
#                                 "sap_code": row.values[1],
#                                 "stockpoint_location": row.values[2],
#                                 "price": int(row.values[icol].replace(',', '').replace(' ', ''))
#                             }]
#                 flag = False
            
#             main_col = None
#     else:
#         print("Error: PDF did not return a list of tables as expected.")

#     # Print formatted data output for debugging
#     print("\nFormatted data output:")    
#     pprint(len(formatted_data.keys()))

#     if save_json_path:
#         with open(save_json_path, 'w') as json_file:
#             json.dump(formatted_data, json_file, indent=4)

#     return formatted_data



# utils.py
import json
import tabula  # Correct import for tabula-py
from pprint import pprint
from collections import defaultdict

def get_stock_json(pdf_file: str = None, save_json_path: str = None):
    # Read PDF file
    print("Reading PDF file...")
    dfs = tabula.read_pdf(pdf_file, pages="all", multiple_tables=True)  # Load all pages (multiple tables)
    print("PDF file read successfully.\n")

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
                if "STOCKPOINT LOCATION" in str(row.values[0:5]):
                    main_col = row
                    break
            
            flag = False
            for icol in range(main_col.values.tolist().index('STOCKPOINT LOCATION') + 1, len(main_col)):
                for row_index, row in df.iterrows():
                    if flag == False and "STOCKPOINT LOCATION" in str(row.values[0:5]):
                        flag = True
                        continue

                    if flag:
                        if main_col.values[icol].replace(' ', '') in formatted_data:
                            formatted_data[main_col.values[icol].replace(' ', '')].append({
                                "sap_code": row.values[1],
                                "stockpoint_location": row.values[2],
                                "price": int(row.values[icol].replace(',', '').replace(' ', ''))
                            })
                        else:
                            formatted_data[main_col.values[icol].replace(' ', '')] = [{
                                "sap_code": row.values[1],
                                "stockpoint_location": row.values[2],
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
            location_key = (entry["sap_code"], entry["stockpoint_location"])
            
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
                    "location": entry["stockpoint_location"],
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

