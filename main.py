import os
import time                     # to time the llm's production times
import config
import cadquery as cq           # CAD engine

from config import OUTPUT_DIR, Colors as C
from api_engine import generate_cad_code, api_call
from freecad_engine import run_freecad_script, freecad_workflow
from cadquery_engine import cadquery_workflow
from excel_engine import init_run_data, save_to_excel

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

def main():
    # --- USER INTERACTION --- #
    print(f"\n{C.HEADER}{C.BOLD}# --- QueryToCAD v1.1 --- #{C.END}\n")
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

    print(f"\n{C.HEADER}{C.BOLD}# --- BENCHMARK COMPLETED --- #{C.END}\n")

if __name__ == "__main__":
    main()