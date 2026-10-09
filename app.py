"""
=================================================================================
🏄  PERSONA — AGENTIC AI PERSONAL PRODUCTIVITY ASSISTANT (v2)
=================================================================================
v2 changes:
  - FIX 1: API key auto-loads from .env — sidebar input is hidden whenever
           config.ENV_KEY_DETECTED is True.
  - FIX 2: Full cyberpunk / glassmorphism dark UI overhaul via custom CSS.

Run it with:
    streamlit run app.py
=================================================================================
"""

# ---------------------------------------------------------------------------
# 1. IMPORTS
# ---------------------------------------------------------------------------
import datetime
from database import init_db, load_reminders, save_reminders
import streamlit as st

from config import (
    APP_DISPLAY_NAME,
    APP_PAGE_ICON,
    ENV_KEY_DETECTED,
    GROQ_FALLBACK_MODEL_NAME,
    GROQ_MODEL_NAME,
    MEMORY_MAPPING,
    resolve_api_key,
)
from groq_client import build_groq_client, stream_chat_completion
from logic import NicknameNotFoundError, resolve_nickname, sort_reminders

# ---------------------------------------------------------------------------
# 2. PAGE CONFIGURATION (must be the first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title=APP_DISPLAY_NAME,
    page_icon=APP_PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# 3. CUSTOM CSS — CYBERPUNK / GLASSMORPHISM DARK THEME
#    This block overrides Streamlit's default light styling with a deep
#    dark palette, translucent glass cards, neon accent borders, and
#    glowing interactive elements.
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>

    /* =====================================================================
       GLOBAL APP BACKGROUND — deep dark base with a subtle radial glow
       ===================================================================== */
    .stApp {
        background-color: #0E1117;
        background-image:
            radial-gradient(circle at 15% 10%, rgba(0, 230, 118, 0.08) 0%, transparent 40%),
            radial-gradient(circle at 85% 15%, rgba(255, 75, 75, 0.07) 0%, transparent 40%),
            radial-gradient(circle at 50% 100%, rgba(56, 189, 248, 0.06) 0%, transparent 50%);
        color: #E6EDF3;
    }

    /* Tighten default block spacing so the dashboard feels denser / crisper */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Headings get a crisp, slightly glowing white */
    h1, h2, h3 {
        color: #F0F6FC !important;
        letter-spacing: 0.3px;
    }
    h1 {
        text-shadow: 0 0 18px rgba(56, 189, 248, 0.25);
    }

    /* Captions / muted text */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #8B949E !important;
    }

    /* =====================================================================
       SIDEBAR — dark navy panel with a crisp right-hand neon border
       ===================================================================== */
    section[data-testid="stSidebar"] {
        background-color: #131722;
        border-right: 1px solid rgba(56, 189, 248, 0.25);
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.35);
    }
    section[data-testid="stSidebar"] * {
        color: #E6EDF3;
    }
    .sidebar-title {
        font-size: 22px;
        font-weight: 800;
        background: linear-gradient(90deg, #38BDF8, #00E676);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(56, 189, 248, 0.25);
    }

    /* .env auto-connected status pill */
    .env-status-pill {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 13px;
        background: rgba(0, 230, 118, 0.12);
        border: 1px solid rgba(0, 230, 118, 0.5);
        color: #00E676;
        box-shadow: 0 0 14px rgba(0, 230, 118, 0.25);
    }

    /* =====================================================================
       METRIC / EMAIL TRACKER — glowing stat counter
       ===================================================================== */
    [data-testid="stMetric"] {
        background: rgba(22, 27, 34, 0.7);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.08);
    }
    [data-testid="stMetricValue"] {
        color: #38BDF8 !important;
        text-shadow: 0 0 16px rgba(56, 189, 248, 0.5);
        font-weight: 800;
    }
    [data-testid="stMetricLabel"] {
        color: #8B949E !important;
    }

    /* =====================================================================
       GLASSMORPHISM REMINDER CARDS
       ===================================================================== */
    .reminder-card-missed {
        background: rgba(22, 27, 34, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 75, 75, 0.35);
        border-left: 4px solid #FF4B4B;
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 0 22px rgba(255, 75, 75, 0.12), 0 8px 24px rgba(0, 0, 0, 0.35);
    }
    .reminder-card-missed .badge-text {
        color: #FF6B6B;
        font-weight: 700;
        text-shadow: 0 0 10px rgba(255, 75, 75, 0.4);
    }

    .reminder-card-future {
        background: rgba(22, 27, 34, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 230, 118, 0.35);
        border-left: 4px solid #00E676;
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 0 22px rgba(0, 230, 118, 0.12), 0 8px 24px rgba(0, 0, 0, 0.35);
    }
    .reminder-card-future .badge-text {
        color: #4EEBA0;
        font-weight: 700;
        text-shadow: 0 0 10px rgba(0, 230, 118, 0.4);
    }

    .reminder-card-title {
        font-size: 16px;
        font-weight: 700;
        color: #F0F6FC;
    }

    /* =====================================================================
       CYBER BUTTONS — Trash / Manage / Save / +- / etc.
       ===================================================================== */
    .stButton > button {
        background: rgba(22, 27, 34, 0.85);
        color: #E6EDF3;
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 10px;
        font-weight: 700;
        letter-spacing: 0.2px;
        padding: 0.5rem 1rem;
        transition: all 0.18s ease-in-out;
    }
    .stButton > button:hover {
        border-color: #38BDF8;
        color: #38BDF8;
        box-shadow: 0 0 16px rgba(56, 189, 248, 0.35);
        transform: translateY(-1px);
    }
    .stButton > button:active {
        transform: translateY(0px);
    }

    /* =====================================================================
       CONTAINERS (used for the reschedule sub-form) — glass panel
       ===================================================================== */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(22, 27, 34, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 14px;
    }

    /* =====================================================================
       CHAT INTERFACE — distinct glowing bubbles per role
       ===================================================================== */
    [data-testid="stChatMessage"] {
        border-radius: 14px;
        padding: 6px 10px;
        margin-bottom: 8px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(22, 27, 34, 0.65);
        backdrop-filter: blur(10px);
    }
    /* User bubbles: subtle neon cyan accent */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        border: 1px solid rgba(56, 189, 248, 0.4);
        box-shadow: 0 0 18px rgba(56, 189, 248, 0.10);
    }
    /* Assistant bubbles: deep glass card with green-tinted glow */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        border: 1px solid rgba(0, 230, 118, 0.3);
        box-shadow: 0 0 18px rgba(0, 230, 118, 0.08);
    }

    /* Chat input bar */
    [data-testid="stChatInput"] {
        background: rgba(22, 27, 34, 0.8);
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 14px;
    }

    /* =====================================================================
       TEXT INPUT / DATE / TIME WIDGETS
       ===================================================================== */
    .stTextInput > div > div > input,
    .stDateInput input,
    .stTimeInput input {
        background-color: rgba(13, 17, 23, 0.8) !important;
        color: #E6EDF3 !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        border-radius: 8px !important;
    }

    /* Info / success / warning banners get a glass tint too */
    [data-testid="stAlert"] {
        background: rgba(22, 27, 34, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 12px;
    }

    /* Divider color */
    hr {
        border-color: rgba(255, 255, 255, 0.08) !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# 4. ROBUST SESSION STATE INITIALIZATION
# ---------------------------------------------------------------------------
if "unread_count" not in st.session_state:
    st.session_state.unread_count = 3

if "reschedule_target_id" not in st.session_state:
    st.session_state.reschedule_target_id = None

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "🌊 **Ahoy! Welcome aboard to Persona!** I'm your Agentic AI "
                "Productivity Assistant. Ask me about a nickname (like *'team'*, "
                "*'captain'*, *'coach'*, or *'client'*) and I'll fetch the right "
                "email from our memory banks for you. Let's ride this productivity "
                "wave together! 🏄‍♂️"
            ),
        }
    ]

# Initialize database and load reminders
init_db()

if "reminders" not in st.session_state:
    loaded = load_reminders()
    if loaded:
        st.session_state.reminders = loaded
    else:
        # First time — create some demo reminders
        _now = datetime.datetime.now()
        st.session_state.reminders = [
            {
                "id": 1,
                "task": "📧 Reply to client proposal email",
                "timestamp": _now - datetime.timedelta(days=2),
                "status": "active",
            },
            {
                "id": 2,
                "task": "📞 Call the coach about training schedule",
                "timestamp": _now - datetime.timedelta(hours=5),
                "status": "active",
            },
            {
                "id": 3,
                "task": "📝 Prepare weekly report for captain",
                "timestamp": _now + datetime.timedelta(days=1),
                "status": "active",
            },
            {
                "id": 4,
                "task": "🏄 Team stand-up meeting prep",
                "timestamp": _now + datetime.timedelta(days=3),
                "status": "active",
            },
        ]
        save_reminders(st.session_state.reminders)

# ---------------------------------------------------------------------------
# 5. SIDEBAR — "Persona Command Center"
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="sidebar-title">🏄 Persona Command Center</div>',
        unsafe_allow_html=True,
    )
    st.caption("Your mission control for mail, memory & momentum.")
    st.divider()

    # --- 5a. API KEY MANAGEMENT (FIX 1: no more nagging) --------------------
    st.markdown("### 🔑 LLM Engine Access")

    if ENV_KEY_DETECTED:
        # A key was already found in the .env file at startup. We DO NOT
        # render any text input at all — there is nothing for the user to
        # type, and no nag banner should ever appear.
        st.markdown(
            '<span class="env-status-pill">🟢 LLM Engine Connected (.env)</span>',
            unsafe_allow_html=True,
        )
        st.caption("Key auto-loaded securely from your local `.env` file.")
        session_key_input = None
    else:
        # No .env key was found — fall back to the manual sidebar input so
        # the app remains usable, but only in this scenario.
        st.markdown(
            """
            No `.env` key detected. Grab a **free Groq API Key**:

            1. Visit [console.groq.com/keys](https://console.groq.com/keys)
            2. Sign in with your Groq account
            3. Click **"Create API Key"**
            4. Paste it below 👇 (or set `GROQ_API_KEY` in a `.env` file
               and restart the app to skip this step permanently)
            """
        )
        session_key_input = st.text_input(
            "Groq API Key",
            type="password",
            placeholder="Paste your API key here...",
            help="Your key is never stored anywhere except this session's memory.",
        )

    # Delegate the actual resolution logic to config.py.
    active_api_key = resolve_api_key(session_input=session_key_input)

    # Build (and cache) the Groq client once per key, so we're not paying
    # connection-setup cost on every single rerun of the script — Streamlit
    # reruns the whole file top-to-bottom on every interaction, so caching
    # the client materially cuts latency on each chat turn.
    @st.cache_resource(show_spinner=False)
    def _get_cached_groq_client(key: str):
        return build_groq_client(api_key=key)

    groq_client = _get_cached_groq_client(active_api_key) if active_api_key else None

    st.divider()

    # --- 5b. LIVE EMAIL TRACKER ---------------------------------------------
    st.markdown("### 📬 Email Tracker")
    st.metric(label="Unread Emails", value=st.session_state.unread_count)

    col_plus, col_minus = st.columns(2)
    with col_plus:
        if st.button("➕ Add", use_container_width=True, key="btn_increment_email"):
            st.session_state.unread_count += 1
            st.rerun()
    with col_minus:
        if st.button("➖ Clear", use_container_width=True, key="btn_decrement_email"):
            # Strict positive-only guard: never let the count drop below zero.
            if st.session_state.unread_count > 0:
                st.session_state.unread_count -= 1
            st.rerun()
            st.divider()
st.markdown("### 🔄 Demo Controls")
if st.button("Reset Demo Reminders", use_container_width=True):
    _now = datetime.datetime.now()
    st.session_state.reminders = [
        {
            "id": 1,
            "task": "📧 Reply to client proposal email",
            "timestamp": _now - datetime.timedelta(days=2),
            "status": "active",
        },
        {
            "id": 2,
            "task": "📞 Call the coach about training schedule",
            "timestamp": _now - datetime.timedelta(hours=5),
            "status": "active",
        },
        {
            "id": 3,
            "task": "📝 Prepare weekly report for captain",
            "timestamp": _now + datetime.timedelta(days=1),
            "status": "active",
        },
        {
            "id": 4,
            "task": "🏄 Team stand-up meeting prep",
            "timestamp": _now + datetime.timedelta(days=3),
            "status": "active",
        },
    ]
    save_reminders(st.session_state.reminders)
    st.success("Demo reminders restored!")
    st.rerun()

    st.divider()

    # --- 5c. LONG-TERM MEMORY MAP TABLE -------------------------------------
    st.markdown("### 🧠 Long-Term Memory Map")
    st.caption("Nicknames the agent already knows about:")

    memory_table_md = "| Nickname | Email |\n|---|---|\n"
    for nickname, email in MEMORY_MAPPING.items():
        memory_table_md += f"| **{nickname}** | `{email}` |\n"
    st.markdown(memory_table_md)

# ---------------------------------------------------------------------------
# 6. MAIN AREA — HEADER
# ---------------------------------------------------------------------------
st.title(f"🌊 {APP_DISPLAY_NAME}")
st.caption("Ride the wave of your to-do list with a splash of AI. 🏄‍♀️")

# ---------------------------------------------------------------------------
# 7. API KEY GATE BANNER
#    Only ever shown if NO key exists anywhere (env or session).
# ---------------------------------------------------------------------------
if not active_api_key:
    st.info(
        "🔑 **Activate your LLM Engine!** Drop your Groq API Key "
        "into the sidebar (or set `GROQ_API_KEY` in your `.env` file) to "
        "unlock the full power of your AI Agent. Your reminders and memory "
        "map are ready to surf right now, key or no key! 🌴",
        icon="💡",
    )

st.divider()


# ---------------------------------------------------------------------------
# 7b. CREATE NEW REMINDER FORM
# ---------------------------------------------------------------------------
st.markdown("### ➕ Create New Reminder")

with st.form(key="new_reminder_form", clear_on_submit=True):
    new_task = st.text_input("Task description", placeholder="e.g. Submit internship report")
    col_date, col_time = st.columns(2)
    with col_date:
        new_date = st.date_input("Date", value=datetime.datetime.now().date())
    with col_time:
        new_time = st.time_input("Time", value=datetime.datetime.now().time())

    submitted = st.form_submit_button("Add Reminder", use_container_width=True)

    if submitted:
        if new_task.strip() == "":
            st.warning("Please enter a task description.")
        else:
            # Generate a new unique ID
            existing_ids = [r["id"] for r in st.session_state.reminders]
            new_id = max(existing_ids) + 1 if existing_ids else 1

            new_reminder = {
                "id": new_id,
                "task": new_task.strip(),
                "timestamp": datetime.datetime.combine(new_date, new_time),
                "status": "active",
            }
            st.session_state.reminders.append(new_reminder)
            save_reminders(st.session_state.reminders)
            st.success(f"Reminder added: {new_task}")
            st.rerun()

# ---------------------------------------------------------------------------
# 8. LIVE REMINDER SORTING — delegated entirely to logic.sort_reminders()
# ---------------------------------------------------------------------------
missed_reminders, future_reminders = sort_reminders(st.session_state.reminders)

current_time = datetime.datetime.now()

# ---------------------------------------------------------------------------
# 9. DASHBOARD LAYOUT — Missed vs Future side-by-side columns
# ---------------------------------------------------------------------------
col_missed, col_future = st.columns(2)

# === 9a. MISSED REMINDERS DASHBOARD (NEON RED GLASS CARDS) =================
with col_missed:
    st.markdown("### 🔴 Missed Reminders Dashboard")

    if len(missed_reminders) == 0:
        st.success("🎉 No missed reminders! You're totally in sync with the tide.")
    else:
        for reminder in missed_reminders:
            task_id = reminder["id"]

            st.markdown(
                f"""
                <div class="reminder-card-missed">
                    <div class="reminder-card-title">⏰ {reminder['task']}</div>
                    <span class="badge-text">
                        Missed: {reminder['timestamp'].strftime('%b %d, %Y at %I:%M %p')}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # --- Interactive Decision Diamond: Trash vs Manage/Reschedule ---
            trash_col, manage_col = st.columns(2)

            with trash_col:
                if st.button(
                    "🗑️ Trash", key=f"trash_{task_id}", use_container_width=True
                ):
                    for r in st.session_state.reminders:
                        if r["id"] == task_id:
                            r["status"] = "trashed"
                            save_reminders(st.session_state.reminders)
                    st.rerun()

            with manage_col:
                if st.button(
                    "🔄 Manage", key=f"manage_{task_id}", use_container_width=True
                ):
                    st.session_state.reschedule_target_id = task_id
                    st.rerun()

            # --- Reschedule sub-form (only for the active target task) -----
            if st.session_state.reschedule_target_id == task_id:
                with st.container(border=True):
                    st.markdown("**🔄 Reschedule this task:**")
                    new_date = st.date_input(
                        "New date",
                        value=current_time.date(),
                        key=f"date_{task_id}",
                    )
                    new_time = st.time_input(
                        "New time",
                        value=current_time.time(),
                        key=f"time_{task_id}",
                    )

                    if st.button("💾 Save New Time", key=f"save_{task_id}"):
                        new_datetime = datetime.datetime.combine(new_date, new_time)

                        for r in st.session_state.reminders:
                            if r["id"] == task_id:
                                r["timestamp"] = new_datetime
                                save_reminders(st.session_state.reminders)

                        st.session_state.reschedule_target_id = None
                        st.rerun()

# === 9b. FUTURE REMINDERS DASHBOARD (NEON GREEN GLASS CARDS) ===============
with col_future:
    st.markdown("### 🟢 Future Reminders Dashboard")

    if len(future_reminders) == 0:
        st.warning("🌤️ Nothing on the horizon yet — smooth sailing ahead!")
    else:
        for reminder in future_reminders:
            st.markdown(
                f"""
                <div class="reminder-card-future">
                    <div class="reminder-card-title">📌 {reminder['task']}</div>
                    <span class="badge-text">
                        Due: {reminder['timestamp'].strftime('%b %d, %Y at %I:%M %p')}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.divider()

# ---------------------------------------------------------------------------
# 10. HIGH-FIDELITY AGENTIC CHAT INTERFACE
# ---------------------------------------------------------------------------
st.markdown("### 🤖 Chat with your Agent")
st.caption(
    "Try typing a nickname like *'team'*, *'captain'*, *'coach'*, or *'client'*!"
)

chat_container = st.container(height=380, border=True)
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
user_prompt = st.chat_input("Type a message to your agent... 🌊")

if user_prompt:
    # User message add
    st.session_state.messages.append(
        {"role": "user", "content": user_prompt}
    )
    with chat_container:
        with st.chat_message("user"):
            st.markdown(user_prompt)

    try:
        matched_email = resolve_nickname(user_prompt, MEMORY_MAPPING)

        agent_reply = (
            f"✅ Nickname Found\n\n"
            f"Email: {matched_email}"
        )
        with chat_container:
            with st.chat_message("assistant"):
                st.markdown(agent_reply)

    except NicknameNotFoundError:
        if active_api_key and groq_client is not None:
            # Send the full running conversation (not just the latest turn)
            # so the agent has real multi-turn memory of the chat.
            chat_history_payload = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]
            try:
                with chat_container:
                    with st.chat_message("assistant"):
                        agent_reply = st.write_stream(
                            stream_chat_completion(
                                client=groq_client,
                                messages=chat_history_payload,
                                primary_model=GROQ_MODEL_NAME,
                                fallback_model=GROQ_FALLBACK_MODEL_NAME,
                            )
                        )
            except Exception as exc:
                agent_reply = (
                    "⚠️ The Groq LLM Engine hit an error after several retries "
                    f"(including a fallback model attempt): `{exc}`. "
                    "Please check your `GROQ_API_KEY` and try again."
                )
                with chat_container:
                    with st.chat_message("assistant"):
                        st.markdown(agent_reply)
        else:
            agent_reply = "Please configure your Groq API key."
            with chat_container:
                with st.chat_message("assistant"):
                    st.markdown(agent_reply)

    st.session_state.messages.append(
        {"role": "assistant", "content": agent_reply}
    )

st.divider()

st.caption("🏄 Persona is an internship portfolio prototype built with Streamlit and Groq.")
