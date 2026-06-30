import streamlit as st
import asyncio
import json
import sqlite3
import os
import datetime
from agent import root_agent
from google.genai import types

# --- NEW IMPORTS: ADK Programmatic Execution ---
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService

# The proven async SQLite connection string
os.makedirs(".adk", exist_ok=True)
db_url = "sqlite+aiosqlite:///./.adk/session.db"

# Initialize the persistent Database Session Service
session_service = DatabaseSessionService(db_url=db_url)
adk_runner = Runner(app_name="mayo_agent_new", agent=root_agent, session_service=session_service)

# =====================================================================
# 1. PAGE CONFIGURATION & CSS
# =====================================================================
st.set_page_config(
    page_title="Donor Intelligence Pipeline", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    div.stButton > button:first-child {
        background: #1e3c72; color: white; border-radius: 6px; font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 2px solid #e0e0e0; }
    .stTabs [data-baseweb="tab"] { font-weight: 600; padding: 10px 20px; }
</style>
""", unsafe_allow_html=True)

if "pipeline_results" not in st.session_state:
    st.session_state.pipeline_results = None

# =====================================================================
# 2. SQLITE: READ & PARSE PAST SESSIONS FROM ADK WEB
# =====================================================================
def get_past_sessions():
    """Connects to the ADK SQLite DB to fetch historical sessions."""
    db_path = os.path.join(".adk", "session.db")
    if not os.path.exists(db_path):
        return []
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT id, create_time FROM sessions ORDER BY create_time DESC LIMIT 15")
        rows = c.fetchall()
        conn.close()
        
        formatted_rows = []
        for row in rows:
            
            timestamp = row[1]

            if isinstance(timestamp, (int, float)):
                dt = datetime.datetime.fromtimestamp(timestamp).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            else:
                dt = str(timestamp)

            formatted_rows.append((row[0], dt))
        return formatted_rows
    except Exception as e:
        return [("DB_Error", str(e))]

def load_historical_run(session_id):
    """Rebuilds the pipeline data dict from the ADK events table."""
    db_path = os.path.join(".adk", "session.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT event_data FROM events WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
    rows = c.fetchall()
    conn.close()
    
    model_outputs = []
    
    for row in rows:
        try:
            event_dict = json.loads(row[0])
            text_payload = None
            
            if "content" in event_dict and "parts" in event_dict["content"]:
                parts = event_dict["content"]["parts"]
                if parts and "text" in parts[0]:
                    text_payload = parts[0]["text"]
            elif "data" in event_dict and isinstance(event_dict["data"], str):
                text_payload = event_dict["data"]
                
            if text_payload and len(text_payload) > 15:
                if text_payload not in model_outputs:
                    model_outputs.append(text_payload)
        except:
            pass 
            
    pipeline_data = {"architect": "", "researcher": "", "publisher": ""}
    
    if len(model_outputs) >= 1:
        pipeline_data["architect"] = model_outputs[0]
    if len(model_outputs) >= 2:
        pipeline_data["researcher"] = model_outputs[1]
    if len(model_outputs) >= 3:
        pipeline_data["publisher"] = model_outputs[-1] 
        
    return pipeline_data

# =====================================================================
# 3. SIDEBAR: HISTORY NAVIGATOR
# =====================================================================
with st.sidebar:
    st.header("🗄️ Session History")
    st.caption("Read directly from .adk/session.db")
    
    past_sessions = get_past_sessions()
    
    if not past_sessions:
        st.info("No past sessions found in database.")
    elif past_sessions[0][0] == "DB_Error":
        st.error(f"Internal SQL Error: {past_sessions[0][1]}")
    else:
        session_options = {f"{row[1]} (ID: {row[0][:6]})": row[0] for row in past_sessions}
        selected_label = st.selectbox("Load Past Execution:", options=["-- Select --"] + list(session_options.keys()))
        
        if selected_label != "-- Select --":
            selected_id = session_options[selected_label]
            if st.button("Load History"):
                st.session_state.pipeline_results = load_historical_run(selected_id)
                st.rerun() 

# =====================================================================
# 4. MAIN UI & "GLASS BOX" LAYOUT
# =====================================================================
st.title("Donor Intelligence Pipeline")
st.markdown("**Transparent multi-agent orchestration architecture.**")
st.divider()

donor_query = st.text_input(
    "Execute New Target Definition:", 
    placeholder="e.g., I need a complete donor intelligence report on -name- -organization-"
)

async def execute_adk_pipeline(query: str):
    pipeline_data = {"architect": "", "researcher": "", "publisher": ""}

    # Create session matching ADK Web identifiers
    session = await session_service.create_session(
        app_name="mayo_agent_new",
        user_id="user"
    )

    # Create ADK message object
    user_message = types.UserContent(query)

    # Execute workflow
    async for event in adk_runner.run_async(
        session_id=session.id,
        user_id="user",
        new_message=user_message
    ):
        event_str = str(event)
        text_payload = None

        if hasattr(event, "data") and event.data:
            text_payload = event.data
        elif hasattr(event, "content") and getattr(event.content, "parts", None):
            text_payload = event.content.parts[0].text

        if text_payload:
            if "Intelligence_Architect" in event_str:
                pipeline_data["architect"] = text_payload
            elif "Unified_Researcher" in event_str:
                pipeline_data["researcher"] = text_payload
            elif "Executive_Publisher" in event_str:
                pipeline_data["publisher"] = text_payload
            else:
                pipeline_data["publisher"] = text_payload

    return pipeline_data

if st.button("Initialize Multi-Agent Graph"):
    if donor_query:
        with st.status("Executing Pipeline Nodes...", expanded=True) as status:
            st.write("🟢 Node 1: Intelligence Architect")
            st.write("🟢 Node 2: Unified Researcher")
            st.write("🟢 Node 3: Executive Publisher")
            try:
                st.session_state.pipeline_results = asyncio.run(execute_adk_pipeline(donor_query))
                status.update(label="Execution Complete", state="complete", expanded=False)
            except Exception as e:
                status.update(label="Execution Failed", state="error")
                st.error(e)

# =====================================================================
# 5. RENDER THE GLASS BOX TABS
# =====================================================================
tab1, tab2, tab3 = st.tabs([
    "📄 Node 3: Executive Summary", 
    "🧠 Node 1: Search Blueprint", 
    "🔍 Node 2: Raw Extracted Data"
])

if st.session_state.pipeline_results:
    results = st.session_state.pipeline_results
    
    with tab1:
        st.markdown(results.get("publisher", ""))
        if not results.get("publisher", ""):
            st.info("No Summary found for this run.")
            
    with tab2:
        st.caption("Raw JSON schema output enforcing precise Google Search boundaries.")
        architect_data = results.get("architect", "")
        try:
            st.json(json.loads(architect_data))
        except:
            st.code(architect_data or "No JSON data found.", language="json")
            
    with tab3:
        st.caption("Raw validated JSON extraction payloads pulled from search grounding.")
        researcher_data = results.get("researcher", "")
        try:
            st.json(json.loads(researcher_data))
        except:
            st.code(researcher_data or "No JSON data found.", language="json")
else:
    with tab1:
        st.info("Awaiting pipeline execution...")