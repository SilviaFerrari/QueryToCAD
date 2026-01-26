import time
import cadquery as cq

from config import OUTPUT_DIR, Colors as C
from geometrical_analysis import analyze_geometry

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
