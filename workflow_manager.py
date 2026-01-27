import os, time

from freecad_engine import freecad_workflow
from cadquery_engine import cadquery_workflow
from api_engine import generate_cad_code
from config import OUTPUT_DIR, MAX_RETRIES, Colors as C

# it selects which geometrical engine AI has choosen
def detect_engine(code):
    if "import FreeCAD" in code or "import Part" in code:
        return "FreeCAD"
    else:
        return "CadQuery"

# Generation -> Fix Attempts -> Final Execution
def request_manager(run_data, user_input, orcode):
    print("The workflow manager has taken charge of the request.")
    start_gen = time.time()

    code = None
    last_error = None

    for attempt in range(1, MAX_RETRIES+1):
        print(f"\n{C.BOLD}API call: attempt {attempt}/{MAX_RETRIES}{C.END}")

        # if it's not the first attempt, we add the error and the previus code
        # generate_cad_code() has to check if the code works
        
        if attempt > 1:
            code = generate_cad_code(user_input, orcode, run_data, error_log, code)
        else:
            code = generate_cad_code(user_input, orcode, run_data) 

        if not code:
            print(f"{C.YELLOW}WARNING: API returned empty code. Retrying...{C.END}")
            continue

        engine = detect_engine(code)
        print(f"Code generated, testing with {engine}.")

        success = False
        error_log = ""

        if engine == "FreeCAD":
            # ANCORA DA FARE!!!
            success, error_log = freecad_workflow(run_data, code, testing = True)
        else:
            # ANCORA DA FARE!!!
            success, error_log = cadquery_workflow(run_data, code, testing = True)

        if success:
            run_data["Gen_Time_s"] = round(time.time() - start_gen, 2)
            print(f"{C.GREEN}SUCCESS: test passed, the code is valid.{C.END}")
            save_file(run_data, code, engine, user_input)
            return
        else:
            print(f"{C.YELLOW}WARNING: test failed with error {error_log[:100]}{C.END}")
            last_error = error_log
            if attempt == MAX_RETRIES:
                print(f"{C.RED}\nFAILURE: max retries reached. Operation Failed.{C.END}")
                run_data["Status"] = "FAILED_RETRIES"
                run_data["Error_Log"] = last_error      

# it's called only if the code works correcly
def save_file(run_data, code, engine, user_input):
    model_name = run_data["Model"]
    project_name = run_data["Project_Name"]

    script_path = f"{OUTPUT_DIR}/{model_name}/{project_name}/{project_name}.py"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(f"# LLM used: {model_name}\n") 
        f.write(f"# User prompt: {user_input}\n\n") 
        f.write(code)

    run_data["Code_Lines"] = len(code.splitlines()) # counting code lines

    if engine == "CadQuery":
        cadquery_workflow(run_data, code, testing = False)
    elif engine == "FreeCAD":
        freecad_workflow(run_data, code, testing = False)