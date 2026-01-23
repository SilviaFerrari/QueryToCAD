import os
import time                     # to time the llm's production times
import pandas                   # standard for managing tables in python
import cadquery as cq           # CAD engine
from datatime import datetime   # timestamp for each test

from ai_engine import AI_MODEL
from ai_engine import generate_cad_code

LLM_MODELS = [
    "openai/gpt-4o",
    "anthropic/claude-sonnet-4.5",
    "anthropic/claude-opus-4.5",
    "meta-llama/llama-3.3-70b-instruct"
    ]

EXCEL_FILE = "output/performance.xlsx"

# function to manage excel file (creation/reading/writing/errors)
def save_to_excel(obj_data):

    # pass the object data dictionary into a list to prevent pandas from getting confused
    new_df = pandas.DataFrame([obj_data])

    # save file retry logic
    max_retries = 5
    for attempt in renge(max_retries):
        try:    
            if os.path.exist(EXCEL_FILE):
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

    print("UNABLE TO SAVE TO EXCEL. The data from this run is lost or only printed to screen.")

# function to analyze the object to determine if it's valid
def analyze_geometry(cq_object):
    
    total_volume = 0
    total_faces = 0
    
    try:
        obj_to_analyze = []
        
        # checking whether cq_object it's a workplane or not 
        if isinstance(cq_object, cq.Workplane):
            # extracts the list of actual solid objects from the container
            obj_to_analyze = cq_object.vals() 
        else:
            # if it's not a workplane, we assume that it's a geometric object
            obj_to_analyze = [cq_object] 

        for obj in obj_to_analyze:

            # checking and calculating the total volume
            if hasattr(obj, "Volume"):
                obj_vol = obj.Volume()
                total_volume += obj_vol

            # checking and calculating the number of faces
            if hasattr(obj, "Faces"):
                obj_faces = len(obj.Faces())
                total_faces += obj_faces
        
    except Exception as e:
        print(f"An error occurred during the geometrical analysis: {e}")
        return {"volume": 0, "faces": 0}

    return {
        "volume": total_volume, 
        "faces": total_faces
    }

# creating output folder
if not os.path.exists(f"output/{AI_MODEL}"):
    os.makedirs(f"output/{AI_MODEL}")

def main():
    # user's interaction
    print("--- QUERYtoCAD v1.0 ---")
    user_input = input("Scrivi cosa vuoi modellare > ")
    project_name = input("Nomina il file su cui verrà salvato il progetto > ")
    os.makedirs(f"output/{AI_MODEL}/{project_name}")

    # calling API
    print("\n1. Richista inviata all'IA.")
    generated_code = generate_cad_code(user_input)

    if not generated_code:
        print("Errore nella generazione del codice.")
        return

    print("\n--- CODICE GENERATO ---")
    print(generated_code)
    print("\n")

    # saving the code
    script_filename = f"output/{AI_MODEL}/{project_name}/{project_name}_code.py"
    with open(script_filename, "w", encoding="utf-8") as f:
        f.write(f"# Prompt Utente: {user_input}\n") # salvo anche il prompt correlato
        f.write(f"# Modello AI: {AI_MODEL}\n\n") # salvo il modello usato
        f.write(generated_code)

    print("\n2. Codice inviato al motore geometrico.")
    
    # local dictionary for AI's code variable
    local_vars = {}
    
    try:
        # dinamically executing the code (testing purpose only)
        exec(generated_code, globals(), local_vars)
        
        # searching for "result" variable created by AI
        if "result" in local_vars:
            part = local_vars["result"]
            # exporting the output
            filename = f"output/{AI_MODEL}/{project_name}/{project_name}.step" 
            cq.exporters.export(part, filename) 
            print(f"\nSUCCESS! File salvato in: {filename}")
        else:
            print("Errore: L'IA ha generato codice, ma non ha creato la variabile 'result'.")
            
    except Exception as e:
        print(f"Errore durante l'esecuzione del codice geometrico:\n{e}")

if __name__ == "__main__":
    main()