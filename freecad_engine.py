import os
import subprocess
import config

# Here we're going to lauch freecad in headless mode.
# In order to do that, freecad needs explicit instructions to export the code.

def run_freecad_script(script_path, output_step_path):
    # create a temporary wrapper file to append an export command
    wrapper_script_path = script_path.replace(".py", "_wrapper.py")

    # this extra code has to be added to AI's script in the footer
    # to correctrly export the object due to AI common errors
    footer_code = f"""
    import FreeCAD
    import Part
    import sys

    try: 
        doc = FreeCAD.ActiveDocument

        # check to see if the document is empty
        if not doc or not doc.Objects:
            print(f"FREECAD_ERROR: no valid object in the document.")
            sys.exit(1)

        # it takes the last created object = final result
        # this is because FreeCAD inserts the object in a history list
        obj = doc.Objects[-1]

        # native export command of FreeCAD
        Part.export([obj], r"{output_step_path}")
        print("FREECAD_SUCCESS: export completed.")

    except Exception as e:
        print(f"FREECAD_ERROR: {{e}}")
        sys.exit(1)
    """
    # reading original script
    with open(script_path, "r", encoding="utf-8") as f:
        original_code = f.read()
    
    # creating wrapped script
    with open(wrapper_script_path, "w", encoding="utf-8") as f:
        f.write(original_code + "\n" + footer_code)

    # launching process (it's like launching it from the terminal)
    try: 
        result = subprocess.run(
            [config.FREECAD_PATH, wrapper_script_path], # executable path
            capture_output=True,    # listen to captrue FreeCAD output
            text=True,              # it reads the output as text
            timeout=60              # if FreeCAD blocks for more than 60sec, it kills it
        )
        
        # analizing FreeCAD console output
        log = result.stdout + result.stderr

        # it looks for the keyword in the footer
        if "FREECAD_SUCCESS" in log and os.path.exists(output_step_path):
            return True, log
        else:
            return False, log

    except subprocess.TimeoutExpired:
        return False, "TIMEOUT: FreeCAD ci ha messo troppo tempo."

    except Exception as e:
        return False, f"SYSTEM ERROR: {e}"