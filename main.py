import os
import time                     # to time the llm's production times
import config
import cadquery as cq           # CAD engine

from config import OUTPUT_DIR, Colors as C
from workflow_manager import request_manager
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
        model_name = model["name"]
        print(f"\n\n{C.BOLD}{C.CYAN}TESTING MODEL: {model_name}{C.END}\n")
        project_name = create_output_folder(OUTPUT_DIR, model_name, project_name_base)

        # dictionary for excel data
        run_data = init_run_data(model_name, project_name, user_input)

        request_manager(run_data, user_input, model["orcode"])

        save_to_excel(run_data)

    print(f"\n{C.HEADER}{C.BOLD}# --- BENCHMARK COMPLETED --- #{C.END}\n")

if __name__ == "__main__":
    main()