import os
import time                     # to time the llm's production times
import cadquery as cq           # CAD engine

import config
from config import OUTPUT_DIR
from api_engine import generate_cad_code
from excel_engine import save_to_excel, init_run_data
from geometrical_analysis import analyze_geometry

if not os.path.exists(f"{OUTPUT_DIR}"):
    os.makedirs(f"{OUTPUT_DIR}")

def main():
    # user's interaction
    print("--- QUERYtoCAD v1.0 ---")
    user_input = input("Scrivi cosa vuoi modellare > ")
    project_name_base = input("Nome del file del progetto > ")

    # ------ DIRECOTRY ORGANIZATION ------ #

    # this loop makes all LLM models to generate the requested object
    for model in config.LLM_MODELS:
        print(f"\n\nTESTING MODEL: {model["name"]}\n")

        # creating llm {OUTPUT_DIR} folder
        if not os.path.exists(f"{OUTPUT_DIR}/{model["name"]}"):
            os.makedirs(f"{OUTPUT_DIR}/{model["name"]}")
        
        # creating project folder with object version check
        version = 1
        while True:
            project_name = project_name_base + "_v" + str(version)
            if not os.path.exists(f"{OUTPUT_DIR}/{model["name"]}/{project_name}"):
                os.makedirs(f"{OUTPUT_DIR}/{model["name"]}/{project_name}")
                break
            else:
                version += 1

        # ------ API CALL ------ #

        # dictionary for excel data
        run_data = init_run_data(model["name"], project_name, user_input)

        print("\nRichista inviata all'IA...")
        start_gen = time.time()    # generation stopwatch

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
        script_filename = f"{OUTPUT_DIR}/{model["name"]}/{project_name}/{project_name}.py"
        with open(script_filename, "w", encoding="utf-8") as f:
            f.write(f"# LLM used: {model["name"]}\n") 
            f.write(f"# User prompt: {user_input}\n\n") 
            f.write(generated_code)

        # counting code lines
        run_data["Code_Lines"] = len(generated_code.splitlines())

        # ------ GEOMETRIC ENGINE ------ #

        print("Code sent to the geometry engine: processing the model...")
        start_exec = time.time() # execution stopwatch
        
        # local dictionary for AI code variable
        # otherwise it would get mixed up with main.py variables
        local_vars = {}
        
        try:
            # dinamically executing the code (testing purpose only)
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
                    print(f"\nSUCCESS: .step project correctly saved in {step_file}")
                else:
                    run_data["Status"] = "EMPTY_GEOMETRY"
                    
            else:
                run_data["Status"] = "NO_RESULT_VAR"
                run_data["Error_Log"] = "Missing variable 'result'"
                print(f"ERROR: {model["name"]} generated the code, but did not create the 'result' variable.")
                
        except Exception as e:
            run_data["Status"] = "EXEC_ERROR"
            run_data["Error_Log"] = str(e)
            print(f"\nERROR: something went wrong while running the geometry engine.\n{e}")

        save_to_excel(run_data)

    print("\n--- BENCHMARK COMPLETED ---")

if __name__ == "__main__":
    main()