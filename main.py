import os
import time                     # to time the llm's production times
import cadquery as cq           # CAD engine

import config
from config import OUTPUT_DIR, Colors as C
from api_engine import generate_cad_code
from excel_engine import save_to_excel, init_run_data
from freecad_engine import run_freecad_script
from geometrical_analysis import analyze_geometry

# creating output directory
if not os.path.exists(f"{OUTPUT_DIR}"):
    os.makedirs(f"{OUTPUT_DIR}")

# creating project output folder with object version check
def create_output_folder(output_dir, model_name, name_base):
    
    if not os.path.exists(f"{output_dir}/{model_name}"):
        os.makedirs(f"{output_dir}/{model_name}")
    
    version = 1
    while True:
        complete_project_name = name_base + "_v" + str(version)
        if not os.path.exists(f"{output_dir}/{model_name}/{complete_project_name}"):
            os.makedirs(f"{output_dir}/{model_name}/{complete_project_name}")
            break
        else:
            version += 1
    return complete_project_name

def api_call(orcode, user_input, run_data):
    print(f"Sending request to IA...")
    generated_code = None
    start_gen = time.time()    # generation stopwatch

    try:
        generated_code = generate_cad_code(user_input, orcode) # API call
        run_data["Gen_Time_s"] = round(time.time() - start_gen, 2)      # time calculation
        print(f"{C.GREEN}SUCCESS: code generated successfully!{C.END}")
        return generated_code

    except Exception as e:
        run_data["Status"] = "API_ERROR"    # error notification
        run_data["Error_Log"] = str(e)      # error annotation
        save_to_excel(run_data)
        print(f"\n{C.YELLOW}WARNING: API error occurred.{C.END}\n")
        return None

def freecad_workflow(run_data, model_name, project_name, start_exec):
    # saving the choosen library in excel, .step and .py file
    run_data["Library"] = "FreeCAD" 
    print(f"Library detected: {run_data["Library"]}")

    # output directory and files
    step_file = f"{OUTPUT_DIR}/{model_name}/{project_name}/{project_name}.step"
    script_path = f"{OUTPUT_DIR}/{model_name}/{project_name}/{project_name}.py"

    # external script execution
    success, log = run_freecad_script(script_path, step_file)
    run_data["Exec_Time_s"] = round(time.time() - start_exec, 2)

    # if the file has been saved, it must be loaded into memory 
    # to check the volumes and geometries with CadQuery
    if success:
        try:
            # importing .step file in CadQuary
            part = cq.importers.importStep(step_file)

            # analyzing geometry
            geom_stats = analyze_geometry(part)
            run_data["Volume_mm3"] = round(geom_stats["volume"], 2) # round to 2 decimal places instead of 15
            run_data["Faces_Count"] = geom_stats["faces"]

            # volume validity check and {OUTPUT_DIR} export
            if run_data["Volume_mm3"] > 0:
                run_data["Status"] = "SUCCESS"
                print(f"{C.GREEN}SUCCESS: .step project correctly saved in {step_file}{C.END}")
            else:
                run_data["Status"] = "EMPTY_GEOMETRY"

        except Exception as e:
            run_data["Status"] = "ANALYSIS_FAIL"
            run_data["Error_Log"] = f"FreeCAD ok, ma l'importazione su CadQuery è fallita: {e}"
    else:
        run_data["Status"] = "EXEC_ERROR"
        run_data["Error_Log"] = log[-300:] # last 300 characters

def cadquery_workflow(run_data, generated_code, model_name, project_name, start_exec):

    # dictionary for AI variable to separate them from main.py variables
    local_vars = {}
    run_data["Library"] = "CadQuery"
    print(f"Library detected: {run_data["Library"]}")

    try:
        # dinamically executing the code (aviable only for CadQuery)
        exec(generated_code, globals(), local_vars)
        run_data["Exec_Time_s"] = round(time.time() - start_exec, 2)
        
        # searching for "result" variable created by AI
        if "result" in local_vars:
            part = local_vars["result"]

            # ------ GEOMETRICAL ANALYSIS ------ #

            geom_stats = analyze_geometry(part)
            run_data["Volume_mm3"] = round(geom_stats["volume"], 2) # round to 2 decimal places instead of 15
            run_data["Faces_Count"] = geom_stats["faces"]

            # volume validity check and {OUTPUT_DIR} export
            if run_data["Volume_mm3"] > 0:
                run_data["Status"] = "SUCCESS"
                step_file = f"{OUTPUT_DIR}/{model_name}/{project_name}/{project_name}.step" 
                cq.exporters.export(part, step_file) 
                print(f"{C.GREEN}SUCCESS: .step project correctly saved in {step_file}{C.END}")
            else:
                run_data["Status"] = "EMPTY_GEOMETRY"
                
        else:
            run_data["Status"] = "NO_RESULT_VAR"
            run_data["Error_Log"] = "Missing variable 'result'"
            print(f"{C.RED}ERROR: {model_name} generated the code, but did not create the 'result' variable.{C.END}")
            
    except Exception as e:
        run_data["Status"] = "EXEC_ERROR"
        run_data["Error_Log"] = str(e)
        print(f"{C.RED}ERROR: something went wrong while running the geometry engine.\n{e}{C.END}")

def main():
    # --- USER INTERACTION --- #
    print(f"\n{C.HEADER}# --- QueryToCAD v1.1 --- #{C.END}\n")
    user_input = input("Scrivi cosa vuoi modellare > ")
    project_name_base = input("Nome del file del progetto > ")

    # --- LLM LOOP --- #
    for model in config.LLM_MODELS:
        
        print(f"\n\n{C.BOLD}{C.CYAN}TESTING MODEL: {model["name"]}{C.END}\n")
        project_name = create_output_folder(OUTPUT_DIR, model["name"], project_name_base)

        # dictionary for excel data
        run_data = init_run_data(model["name"], project_name, user_input)

        # api call to AI
        generated_code = api_call(model["orcode"], user_input, run_data)

        if generated_code is None:
            continue

        if generated_code is None:
            run_data["Status"] = "GENERATION_FAIL"
            save_to_excel(run_data)
            print(f"{C.YELLOW}WARNING: generation error occurred.{C.END}")
            continue

        # --- SAVING CODE AND PROMPT --- #
        script_filename = f"{OUTPUT_DIR}/{model["name"]}/{project_name}/{project_name}.py"
        with open(script_filename, "w", encoding="utf-8") as f:
            f.write(f"# LLM used: {model["name"]}\n") 
            f.write(f"# User prompt: {user_input}\n\n") 
            f.write(generated_code)

        run_data["Code_Lines"] = len(generated_code.splitlines()) # counting code lines

        # ------ GEOMETRIC ENGINE ------ #

        print(f"Code sent to the geometry engine.")
        is_freecad = False
        start_exec = time.time() # execution stopwatch

        # checking if AI decided to use FreeCAD
        if "import FreeCAD" in generated_code or "import Part" in generated_code:
            is_freecad = True

        if is_freecad:
           freecad_workflow(run_data, model["name"], project_name, start_exec)

        else:
            cadquery_workflow(run_data, generated_code, model["name"], project_name, start_exec)

        save_to_excel(run_data)

    print(f"\n{C.HEADER}# --- BENCHMARK COMPLETED --- #{C.END}\n")

if __name__ == "__main__":
    main()