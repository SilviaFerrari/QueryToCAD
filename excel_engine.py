import os
import time     
import pandas                   # standard for managing tables in 
from datetime import datetime   # timestamp for each test
from config import EXCEL_FILE

# create the dictionary (factory pattern)
def init_run_data(model_name, project_name, prompt):
    return {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Model": model_name,
        "Project_Name": project_name,
        "Prompt": prompt,
        "Status": "PENDING",
        "Gen_Time_s": 0,
        "Exec_Time_s": 0,
        "Volume_mm3": 0,
        "Faces_Count": 0,
        "Error_Log": "",
        "Code_Lines": 0
    }

# function to manage excel file (creation/reading/writing/errors)
def save_to_excel(obj_data):

    # pass the object data dictionary into a list to prevent pandas from getting confused
    new_df = pandas.DataFrame([obj_data])

    # save file retry logic
    max_retries = 5
    for attempt in range(max_retries):
        try:    
            if os.path.exists(EXCEL_FILE):
                # read the entire file
                existing_df = pandas.read_excel(EXCEL_FILE)
                # create a history of changes, discarding old row/column index
                final_df = pandas.concat([existing_df, new_df], ignore_index = True)
            else:
                final_df = new_df 
        
            # write the file to disk without the row number column
            final_df.to_excel(EXCEL_FILE, index = False) 
            print(f"Excel file updated successfully: {EXCEL_FILE}")
            return
        
        # if we try to edit the excel file while it's open, an error will occur
        except PermissionError:
            print(f"""
            WARNING: the excel file '{EXCEL_FILE}' seems to be open!\n
            Please close it within 5 second, otherwise all data will be lost.\n
            Attempt {attempt+1}/{max_retries}.
            """)

        except Exception as e:
            print(f"An unexpected error occurred while saving file: {e}")
            break

    print("ERROR: UNABLE TO SAVE TO EXCEL. The data from this run is lost or only printed to screen.")