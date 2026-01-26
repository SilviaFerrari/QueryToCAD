#Link to OpenRouter's code: https://openrouter.ai/anthropic/claude-opus-4.5/api
import os, time
from openai import OpenAI
from dotenv import load_dotenv # to read .env files (API key)
from excel_engine import save_to_excel
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
CONTESTO:
Il tuo compito è scrivere script Python per generare modelli 3D parametrici.
Puoi scegliere tra due librerie: 'CadQuery' o 'FreeCAD'.

REGOLE DI SCELTA:
1. Usa **CadQuery** per parti meccaniche semplici o standard come staffe o piastre con fori.
2. Usa **FreeCAD** per modelli complessi od operazioni che CadQuery non gestisce bene.
3. Se l'utente richiede esplicitamente CadQuery o FreeCAD, verifica prima la fattibilità e asseconda la richiesta solo se è sensato.

SINTASSI CADQUERY:
import cadquery as cq
result = cq.Workplane("XY").box(10,10,10)

SINTASSI FREECAD:
import FreeCAD, Part
doc = FreeCAD.newDocument()
box = Part.makeBox(10,10,10)
doc.addObject("Part::Feature", "MyBox").Shape = box

IMPORTANTE:
- Non mischiare mai le due librerie.
- Se devi fare calcoli, usa variabili esplicite all'inizio.
- Se usi CadQuery, assegna l'oggetto finale a una variabile chiamata 'result'.
- Se usi FreeCAD, lavora sempre su 'FreeCAD.ActiveDocument' o crea un newDocument().
- NON includere commenti markdown o blocchi ```python, restituisci solo il codice puro.
"""

# process the user's request
def generate_cad_code(user_prompt, model_orcode):
    try:
        # call to OpenRouter
        completion = client.chat.completions.create(
            model = model_orcode, # chosen model
            messages=[
                {"role": "system", "content": MAIN_PROMPT},
                {"role": "user", "content": user_prompt},
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

# handles the API call, timer, and errors
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