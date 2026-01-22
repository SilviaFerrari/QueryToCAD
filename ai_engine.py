#Link to OpenRouter's code: https://openrouter.ai/anthropic/claude-opus-4.5/api
import os
from openai import OpenAI
from dotenv import load_dotenv # to read .env files (API key)

AI_MODEL = "anthropic/claude-3.5-sonnet"

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
OBIETTIVO: 
Il tuo compito è convertire le richieste dell'utente in script Python eseguibili.
Input: Descrizione in linguaggio naturale.
Output: SOLO codice Python per la libreria 'cadquery'.

REGOLE TASSATIVE:
1. NON scrivere testo introduttivo (niente "Ecco il codice", niente "Certamente").
2. NON usare blocchi markdown (niente ```python).
3. Importa la libreria così: import cadquery as cq
4. Assegna l'oggetto finale a una variabile chiamata 'result'.
5. Se devi fare calcoli, usa variabili esplicite all'inizio.
6. Restituisci SOLO il codice eseguibile. Nient'altro.
"""

# process the user's request
def generate_cad_code(user_prompt):
    try:
        # call to OpenRouter
        completion = client.chat.completions.create(
            model = AI_MODEL, # chosen model
            messages=[
                {"role": "system", "content": MAIN_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        
        # estraiamo dal file json solo il codice che ci interessa
        code = completion.choices[0].message.content

        # pulizia base del codice per togliere eventuali markdown problematici
        code = code.replace("```python", "").replace("```", "").strip()
        return code
    except Exception as e:
        print(f"Errore AI: {e}")
        return None