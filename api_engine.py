#Link to OpenRouter's code: https://openrouter.ai/anthropic/claude-opus-4.5/api
import os, time
import config
from openai import OpenAI
from dotenv import load_dotenv # to read .env files (API key)
from excel_engine import save_to_excel
from freecad_engine import freecad_workflow
from cadquery_engine import cadquery_workflow
from config import OUTPUT_DIR, Colors as C

# to load the key from the .env file
load_dotenv()

# call to OpenAI's API (it's also possible to use only python)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1", # it specify to call OpenRouter instead of ChatGPT
    api_key=os.getenv("OPENROUTER_API_KEY"), # chiama la chiave senza scriverla in chiaro
)

# here we define the main prompt that will be integrated with the user's prompt
# it's importat to specify every single constrain to optimize the result
# contraints depends from the quality and the version of the LLM

MAIN_PROMPT = """
CONTEXT:
Your task is to write Python scripts to generate parametric 3D models.
You can choose between two libraries: CadQuery or FreeCAD.

CHOICE RULES:
1. Use CadQuery for simple or standard mechanical parts such as brackets or plates with holes.
2. Use FreeCAD for complex models or operations that CadQuery does not handle well.
3. If the user explicitly requests the use of CadQuery or FreeCAD, check feasibility first and only comply with the request if it makes sense.

CADQUERY SYNTAX:
import cadquery as cq
result = cq.Workplane("XY").box(10,10,10)

FREECAD SYNTAX:
import FreeCAD, Part
doc = FreeCAD.newDocument()
box = Part.makeBox(10,10,10)
doc.addObject("Part::Feature", "MyBox").Shape = box

IMPORTANT:
- Never mix the two libraries.
- If you need to perform calculations, use explicit variables at the beginning.
- If using CadQuery, assign the final object to a variable called 'result'.
- If using FreeCAD, always work on 'FreeCAD.ActiveDocument' or create a newDocument().
- Do NOT include markdown comments or Python blocks; return only the raw code.
"""

def error_prompt_composer(user_prompt, error_log, previous_code):
    error_prompt = f"""
    ORIGINAL TASK: {user_prompt}

    PREVIOUSLY GENERATED CODE:
    ```python 
    {previous_code}
    ```
    ERROR RETURNED: {error_log} 

    GOAL:
    Rewrite the entire code to fix the error.
    Don't provide explanations, just the correct Python code.
    """
    print(f"{C.YELLOW}WARNING: asking AI to correct some errors.{C.END}")
    return error_prompt

# process the user's request and handles AI code errors
def generate_cad_code(user_prompt, model_orcode, error_log = None, previous_code = None):
    
    if error_log and previous_code:
        final_prompt = error_prompt_composer(user_prompt, error_log, previous_code)
    else:
        final_prompt = user_prompt

    try:
        # call to OpenRouter
        completion = client.chat.completions.create(
            model = model_orcode, # chosen model
            messages=[
                {"role": "system", "content": MAIN_PROMPT},
                {"role": "user", "content": final_prompt},
            ],
        )
        
        # extracting only the code we're interested in from the json file
        code = completion.choices[0].message.content

        # basic code cleanup to remove any problematic markdowns
        code = code.replace("```python", "").replace("```", "").strip()
        return code

    except Exception as e:
        print(f"{C.RED}ERROR: something went wrong during code generation.\n{e}{C.END}")
        return None

def workflow_test_manager(run_data, code):

    success = False
    exec_error = None

    if "import FreeCAD" in code or "import Part" in code:
        freecad_workflow()
    else:
        cadquery_workflow()

    return success, exec_error

# handles the API call, timer, and errors
def api_call(orcode, user_input, run_data):
    print(f"Sending request to IA...")

    generated_code = None
    error_log = None

    for attempt in range(1, MAX_RETRIES+1):
        print(f"\n{C.BOLD}Attempt to generate code {attempt}/{MAX_RETRIES}{C.END}")

        # if it's not the first attempt, we add the error and the previus code
        # generate_cad_code() has to check if the code works
        try:
            if attempt > 1:
                generated_code = generate_cad_code(user_input, orcode, error_log, previous_code)
            else:
                generated_code = generate_cad_code(user_input, orcode) 

            if not generated_code:
                print(f"{C.YELLOW}ERROR: API returned empty code.{C.END}")
                continue
            else:            
                print(f"{C.GREEN}SUCCESS: code generated successfully.{C.END}")

        except Exception as e:
            run_data["Status"] = "API_ERROR"    # error notification
            run_data["Error_Log"] = str(e)      # error annotation
            save_to_excel(run_data)
            print(f"\n{C.YELLOW}ERROR: API error occurred.{C.END}\n")
            return None

        # if the code was successfully generated, now he have to check if it works
        success, exec_error = workflow_test_manager(run_data, generated_code)

        if success:
            print(f"{C.GREEN}SUCCESS: code works!{C.END}")
            return generated_code
        else:
            print(f"{C.YELLOW}WARNING: code failed verification.{C.END}")
            print(f"{C.RED}Error: {exec_error[:100]}...{C.END}") # printing the first part of the error
            error_log = exec_error
            
            # if it's the last attempt, we give up
            if attempt == MAX_RETRIES:
                print(f"{C.RED}Max retries reached. Moving on.{C.END}")

    return None