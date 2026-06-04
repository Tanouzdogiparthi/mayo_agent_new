from google.adk import Agent, Workflow
from google.adk.tools import google_search
from dotenv import load_dotenv

# Import our markdown prompt strings from the asset loader
try:
    # ADK Context
    from .loader import PLANNER_PROMPT, RESEARCHER_PROMPT, PUBLISHER_PROMPT
except ImportError:
    # Streamlit Context
    from loader import PLANNER_PROMPT, RESEARCHER_PROMPT, PUBLISHER_PROMPT

# Load environment variables (.env secrets)
load_dotenv()

# =====================================================================
# 1. DEFINE STREAMLINED AGENTS (Using Quota-Safe Gemini 2.5 Flash Lite)
# =====================================================================

# Step 1: The Architect (Parses unstructured input and builds queries)
planner_agent = Agent(
    name="Intelligence_Architect",
    instruction=PLANNER_PROMPT,
    model="gemini-2.5-flash"
)

# Step 2: The Unified Researcher (Runs background, news, and wealth queries)
researcher_agent = Agent(
    name="Unified_Researcher",
    instruction=RESEARCHER_PROMPT,
    model="gemini-2.5-flash",
    tools=[google_search]
)

# Step 3: The Publisher (Validates, designs strategy, and generates Markdown)
publisher_agent = Agent(
    name="Executive_Publisher",
    instruction=PUBLISHER_PROMPT,
    model="gemini-2.5-flash"
)

# =====================================================================
# 2. DEFINE THE STREAMLINED GRAPH WORKFLOW
# =====================================================================
# The ADK framework automatically detects and runs the 'root_agent' graph.
# We have flattened the pipeline into a fast, 3-step linear sequence.
root_agent = Workflow(
    name="donor_intelligence_pipeline_v2",
    edges=[
        (
            "START", 
            planner_agent, 
            researcher_agent, 
            publisher_agent
        )
    ]
)