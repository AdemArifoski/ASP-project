import streamlit as st
from streamlit_calendar import calendar
import os
import json



st.title("Calendar")

# -------------------------
# SESSION INIT
# -------------------------
if "calendar_events" not in st.session_state:
    if os.path.exists("calendar_events.json"):
        with open("calendar_events.json", "r") as f:
            st.session_state.calendar_events = json.load(f)
    else:
        st.session_state.calendar_events = []

if "view" not in st.session_state:
    st.session_state.view = "dayGridMonth"

if "view_date" not in st.session_state:
    st.session_state.view_date = None


# -------------------------
# OPTIONS
# -------------------------
calendar_options = {
    "initialView": st.session_state.view,
    "initialDate": st.session_state.view_date,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridDay"
    },
    "editable": False,
    "selectable": True,
    "events": st.session_state.calendar_events,   # IMPORTANT
}


# -------------------------
# RENDER
# -------------------------
state = calendar(options=calendar_options)

st.write(state)

# -------------------------
# RESET BUTTON (HERE)
# -------------------------
if st.button("Reset Calendar"):
    st.session_state.calendar_events = []

    if os.path.exists("calendar_events.json"):
        os.remove("calendar_events.json")

    st.rerun()
    
# -------------------------
# INTERACTIONS
# -------------------------
if state.get("callback") == "dateClick":
    st.session_state.view_date = state["dateClick"]["date"]
    st.session_state.view = "timeGridDay"
    st.rerun()
