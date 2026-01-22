import os
import cadquery as cq
from ai_engine import generate_cad_code
from ai_engine import AI_MODEL

# creating output folder
if not os.path.exists(f"output/{AI_MODEL}"):
    os.makedirs(f"output/{AI_MODEL}")

def main():
    # user's interaction
    print("--- QUERYtoCAD v1.0 ---")
    user_input = input("Scrivi cosa vuoi modellare > ")
    project_name = input("Nomina il file su cui verrà salvato il progetto > ")
    os.makedirs(f"output/{AI_MODEL}/{project_name}")

    # calling API
    print("\n1. Richista inviata all'IA.")
    generated_code = generate_cad_code(user_input)

    if not generated_code:
        print("Errore nella generazione del codice.")
        return

    print("\n--- CODICE GENERATO ---")
    print(generated_code)
    print("\n")

    # saving the code
    script_filename = f"output/{AI_MODEL}/{project_name}/{project_name}_code.py"
    with open(script_filename, "w", encoding="utf-8") as f:
        f.write(f"# Prompt Utente: {user_input}\n") # salvo anche il prompt correlato
        f.write(f"# Modello AI: {AI_MODEL}\n\n") # salvo il modello usato
        f.write(generated_code)

    print("\n2. Codice inviato al motore geometrico.")
    
    # local dictionary for AI's code variable
    local_vars = {}
    
    try:
        # dinamically executing the code (testing purpose only)
        exec(generated_code, globals(), local_vars)
        
        # searching for "result" variable created by AI
        if "result" in local_vars:
            part = local_vars["result"]
            # exporting the output
            filename = f"output/{AI_MODEL}/{project_name}/{project_name}.step" 
            cq.exporters.export(part, filename) 
            print(f"\nSUCCESS! File salvato in: {filename}")
        else:
            print("Errore: L'IA ha generato codice, ma non ha creato la variabile 'result'.")
            
    except Exception as e:
        print(f"Errore durante l'esecuzione del codice geometrico:\n{e}")

if __name__ == "__main__":
    main()