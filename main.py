import os
import time                     # to time the llm's production times
import pandas                   # standard for managing tables in python
import cadquery as cq           # CAD engine
from datatime import datetime   # timestamp for each test
from ai_engine import generate_cad_code

LLM_MODELS = [
    {
        "name": "gpt-4o",
        "orcode": "openai/gpt-4o"
    },
    {
        "name": "claude-sonnet-4.5",
        "orcode": "anthropic/claude-sonnet-4.5"
    },   
    {
        "name": "claude-opus-4.5",
        "orcode": "anthropic/claude-opus-4.5"
    },  
    {
        "name": "llama-3.3-70b-instruct",
        "orcode": "meta-llama/llama-3.3-70b-instruct"
    }
]

if not os.path.exists(f"output"):
    os.makedirs(f"output")

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

def main():
    # user's interaction
    print("--- QUERYtoCAD v1.0 ---")
    user_input = input("Scrivi cosa vuoi modellare > ")
    project_name = input("Nome del file del progetto > ")

    # this loop makes all LLM models to generate the requested object
    for model in LLM_MODELS:
        print(f"\nTesting Model: {model["name"]}...")

        # creating llm output folder
        if not os.path.exists(f"output/{model["name"]}"):
            os.makedirs(f"output/{model["name"]}")
        
        # creating project folder with object version check
        version = 1
        while True:
            if not os.path.exists(f"output/{model["name"]}/{project_name}"):
                project_name = project_name + "_v" + str(version)
                os.makedirs(f"output/{model["name"]}/{project_name}")
                break
            else:
                coutenr += 1
                project_name = project_name + "_v" + str(version)

        # dictionary for excel data
        run_data = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Model": model_name,
            "Project_Name": project_name_base,
            "Prompt": user_input,
            "Status": "PENDING",
            "Gen_Time_s": 0,
            "Exec_Time_s": 0,
            "Volume_mm3": 0,
            "Faces_Count": 0,
            "Error_Log": ""
        }

        print("\nRichista inviata all'IA...")
        start_gen = time.start()    # timer start

        try:
            generated_code = generate_cad_code(user_input, model["orcode"]) # API call
            run_data["Gen_Time_s"] = round(time.time() - start_gen, 2)      # time calculation
            print("\nSUCCESS: code generated successfully!\n")

        except Exception as e:
            run_data["Status"] = "API_ERROR"    # error notification
            run_data["Error_Log"] = str(e)      # error annotation
            save_to_excel(run_data)
            print(f"\nWARNING: API error occurred.\n")
            continue

        if not generated_code:
            run_data["Status"] = "GENERATION_FAIL"
            save_to_excel(run_data)
            print(f"\nWARNING: generation error occurred.\n")
            continue

        # saving the code and the prompt
        script_filename = f"output/{model["name"]}/{project_name}/{project_name}.py"
        with open(script_filename, "w", encoding="utf-8") as f:
            f.write(f"# LLM used: {model["name"]}\n") 
            f.write(f"# User prompt: {user_input}\n\n") 
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