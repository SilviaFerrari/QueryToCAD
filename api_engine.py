#Link to OpenRouter's code: https://openrouter.ai/anthropic/claude-opus-4.5/api
import os
from openai import OpenAI
from dotenv import load_dotenv # to read .env files (API key)

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
Sei un esperto ingegnere CAD. Il tuo compito è scrivere script Python per generare modelli 3D.
Puoi scegliere tra due librerie: 'CadQuery' o 'FreeCAD'.

REGOLE DI SCELTA:
1. Usa **CadQuery** (preferito) per parti meccaniche standard, staffe, piastre con fori.
2. Usa **FreeCAD** SOLO se richiesto esplicitamente o per loft complessi/operazioni che CadQuery non gestisce bene.

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