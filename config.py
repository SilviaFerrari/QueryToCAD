import os

OUTPUT_DIR = "output"
EXCEL_FILE = f"{OUTPUT_DIR}/performance.xlsx"
FREECAD_PATH = "c:\\Program Files\\FreeCAD 1.0\\bin\\freecacmd.exe"

LLM_MODELS = [
    {
        "name": "gpt-4o",
        "orcode": "openai/gpt-4o"
    },
    {
        "name": "claude-sonnet-4.5",
        "orcode": "anthropic/claude-sonnet-4.5"
    },   
    {
        "name": "claude-opus-4.5",
        "orcode": "anthropic/claude-opus-4.5"
    },  
    {
        "name": "llama-3.3-70b-instruct",
        "orcode": "meta-llama/llama-3.3-70b-instruct"
    }
]

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

if not os.path.exists(FREECAD_PATH):
    print(f"{Colors.YELLOW}WARNING: freecadcmd.exe non trovato in {FREECAD_PATH}{Colors.END}")