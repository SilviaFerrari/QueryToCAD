import os
import time                     # to time the llm's production times
import cadquery as cq           # CAD engine

import config
from config import OUTPUT_DIR, Colors as C
from api_engine import generate_cad_code
from excel_engine import save_to_excel, init_run_data
from geometrical_analysis import analyze_geometry
from freecad_engine import run_freecad_script

if not os.path.exists(f"{OUTPUT_DIR}"):
    os.makedirs(f"{OUTPUT_DIR}")

def create_output_folder(output_dir, model_name, name_base):
    # creating llm {OUTPUT_DIR} folder
    if not os.path.exists(f"{output_dir}/{model_name}"):
        os.makedirs(f"{output_dir}/{model_name}")
    
    # creating project folder with object version check
    version = 1
    while True:
        complete_project_name = name_base + "_v" + str(version)
        if not os.path.exists(f"{output_dir}/{model_name}/{complete_project_name}"):
            os.makedirs(f"{output_dir}/{model_name}/{complete_project_name}")
            break
        else:
            version += 1
    return complete_project_name

def main():
    # user's interaction
    print(f"\n{C.HEADER}# --- QueryToCAD v1.1 --- #{C.END}\n")
    user_input = input("Scrivi cosa vuoi modellare > ")
    project_name_base = input("Nome del file del progetto > ")

    # this loop makes all LLM models to generate the requested object
    for model in config.LLM_MODELS:
        
        print(f"\n\n{C.BOLD}TESTING MODEL: {model["name"]}{C.END}\n")
        project_name = create_output_folder(OUTPUT_DIR, model["name"], project_name_base)

        # dictionary for excel data
        run_data = init_run_data(model["name"], project_name, user_input)

        print(f"{C.CYAN}Sending request to IA...{C.END}")
        start_gen = time.time()    # generation stopwatch

        try:
            generated_code = generate_cad_code(user_input, model["orcode"]) # API call
            run_data["Gen_Time_s"] = round(time.time() - start_gen, 2)      # time calculation
            print(f"{C.GREEN}SUCCESS: code generated successfully!{C.END}")

        except Exception as e:
            run_data["Status"] = "API_ERROR"    # error notification
            run_data["Error_Log"] = str(e)      # error annotation
            save_to_excel(run_data)
            print(f"\n{C.YELLOW}WARNING: API error occurred.{C.END}\n")
            continue

        if not generated_code:
            run_data["Status"] = "GENERATION_FAIL"
            save_to_excel(run_data)
            print(f"{C.YELLOW}WARNING: generation error occurred.{C.END}")
            continue

        # saving the code and the prompt
        script_filename = f"{OUTPUT_DIR}/{model["name"]}/{project_name}/{project_name}.py"
        with open(script_filename, "w", encoding="utf-8") as f:
            f.write(f"# LLM used: {model["name"]}\n") 
            f.write(f"# User prompt: {user_input}\n\n") 
            f.write(generated_code)

        # counting code lines
        run_data["Code_Lines"] = len(generated_code.splitlines())

        # ------ GEOMETRIC ENGINE ------ #

        print(f"{C.CYAN}Code sent to the geometry engine: processing the model...{C.END}")
        start_exec = time.time() # execution stopwatch
        
        # local dictionary for AI code variable
        # otherwise it would get mixed up with main.py variables
        local_vars = {}
        
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
                    step_file = f"{OUTPUT_DIR}/{model["name"]}/{project_name}/{project_name}.step" 
                    cq.exporters.export(part, step_file) 
                    print(f"{C.GREEN}SUCCESS: .step project correctly saved in {step_file}{C.END}")
                else:
                    run_data["Status"] = "EMPTY_GEOMETRY"
                    
            else:
                run_data["Status"] = "NO_RESULT_VAR"
                run_data["Error_Log"] = "Missing variable 'result'"
                print(f"{C.RED}ERROR: {model["name"]} generated the code, but did not create the 'result' variable.{C.END}")
                
        except Exception as e:
            run_data["Status"] = "EXEC_ERROR"
            run_data["Error_Log"] = str(e)
            print(f"{C.RED}ERROR: something went wrong while running the geometry engine.\n{e}{C.END}")

        save_to_excel(run_data)

    print(f"\n{C.HEADER}# --- BENCHMARK COMPLETED --- #{C.END}\n")

if __name__ == "__main__":
    main()