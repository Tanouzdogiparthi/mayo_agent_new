import os

def load_template(filename: str) -> str:
    """Reads a markdown prompt template from the templates directory."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "templates", filename)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CRITICAL: Prompt template missing at {file_path}")
        
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

# Dynamically pull the 3 optimized templates into memory
try:
    PLANNER_PROMPT = load_template("planner.md")
    RESEARCHER_PROMPT = load_template("researcher.md")
    PUBLISHER_PROMPT = load_template("publisher.md")
except FileNotFoundError as e:
    print(e)