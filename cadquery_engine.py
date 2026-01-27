import time
import cadquery as cq

from config import OUTPUT_DIR, Colors as C
from geometrical_analysis import analyze_geometry

# Runs the CadQuery code. If test_mode=True, 
# it does NOT save the file, just checks if it works.
# Returns: (bool: success, str: error_message)
def cadquery_workflow(run_data, generated_code, testing = False):

    # dictionary for AI variable to separate them from main.py variables
    local_vars = {}
    run_data["Library"] = "CadQuery"
    model_name = run_data["Model"]
    project_name = run_data["Project_Name"]

    if not testing:
        print(f"Library detected: {run_data["Library"]}")

    try:
        # dynamic code execution (aviable only for CadQuery)
        exec(generated_code, globals(), local_vars)
        
        # searching for "result" variable created by AI
        if "result" in local_vars:
            part = local_vars["result"]

            # ------ GEOMETRICAL ANALYSIS ------ #

            # quick check if we are only testing
            if testing:
                if hasattr(part, "val") and part.val().Volume() > 0:
                    return True, ""
                else:
                    return False, "Empty geometry (volume is 0)."

            # serious check out of testing mode
            geom_stats = analyze_geometry(part)
            run_data["Volume_mm3"] = round(geom_stats["volume"], 2) # round to 2 decimal places instead of 15
            run_data["Faces_Count"] = geom_stats["faces"]

            # volume validity check and {OUTPUT_DIR} export
            if run_data["Volume_mm3"] > 0:
                run_data["Status"] = "SUCCESS"
                step_file = f"{OUTPUT_DIR}/{model_name}/{project_name}/{project_name}.step" 
                cq.exporters.export(part, step_file) 

                print(f"{C.GREEN}SUCCESS: .step project correctly saved in {step_file}{C.END}")
                return True, ""
            else:
                run_data["Status"] = "EMPTY_GEOMETRY"
                return False, "Geometry volume is 0."
                
        else:
            run_data["Status"] = "NO_RESULT_VAR"
            run_data["Error_Log"] = "Missing variable 'result'"
            if not testing:
                print(f"{C.RED}ERROR: 'result' variable missing.{C.END}")
            return False, "Missing variable 'result'."
            
    except Exception as e:
        run_data["Status"] = "EXEC_ERROR"
        run_data["Error_Log"] = str(e)
        if not testing:
            print(f"{C.RED}ERROR: something went wrong while running CadQuery code.\n{e}{C.END}")
        return False, str(e)
