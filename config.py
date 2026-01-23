OUTPUT_DIR = "output"
EXCEL_FILE = f"{OUTPUT_DIR}/performance.xlsx"

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