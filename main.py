import streamlit as st
import clingo
import pandas as pd
from datetime import datetime, timedelta
import json
from streamlit_calendar import calendar
import os




if "subjects" not in st.session_state:
    st.session_state.subjects = []

if "subject_data" not in st.session_state:
    st.session_state.subject_data = pd.DataFrame(
        columns=["Subject", "Difficulty", "Priority", "Strength"]
    )

if "deadlines" not in st.session_state:
    st.session_state.deadlines = {}

if "schedule_type" not in st.session_state:
    st.session_state.schedule_type = None

if "schedule_message" not in st.session_state:
    st.session_state.schedule_message = None

    
st.subheader("Subjects")

subject_input = st.text_input(
    "Enter subjects (comma separated)",
    placeholder="e.g. im, tcs2"
)

if st.button("Add Subjects"):

    new_subjects = [
        s.strip()
        for s in subject_input.split(",")
        if s.strip()
    ]

    old_df = st.session_state.subject_data.copy()

    # Convert existing subjects to set
    existing_subjects = set(old_df["Subject"].tolist())

    # Build rows only for NEW subjects
    new_rows = []

    for s in new_subjects:
        if s not in existing_subjects:
            new_rows.append({
                "Subject": s,
                "Difficulty": 1,
                "Priority": 1,
                "Strength": 1
            })

    # Append new subjects to existing table
    if new_rows:
        st.session_state.subject_data = pd.concat(
            [old_df, pd.DataFrame(new_rows)],
            ignore_index=True
        )


if not st.session_state.subject_data.empty:

    edited_df = st.data_editor(
        st.session_state.subject_data,
        width="stretch",
        num_rows="fixed",
        key="subject_editor",
        column_config={
            "Difficulty": st.column_config.NumberColumn(
                min_value=1,
                max_value=5,
                step=1,
            ),
            "Priority": st.column_config.NumberColumn(
                min_value=1,
                max_value=5,
                step=1,
            ),
            "Strength": st.column_config.NumberColumn(
                min_value=1,
                max_value=5,
                step=1,
            ),
        }
    )

    st.session_state.subject_data = edited_df

subject_data = (
    st.session_state.subject_data
    .set_index("Subject")
    .to_dict("index")
    if not st.session_state.subject_data.empty
    else {}
)

selected_subjects = (
    st.session_state.subject_data["Subject"].tolist()
    if not st.session_state.subject_data.empty
    else []
)



st.subheader("Deadlines")

selected_subjects = (
    st.session_state.subject_data["Subject"].tolist()
    if not st.session_state.subject_data.empty
    else []
)

if selected_subjects:
    st.write("Enter deadlines for each subject:")

    for subject in selected_subjects:
        key = subject.lower()

        st.session_state.deadlines[key] = st.date_input(
            f"Deadline for {subject}",
            value=st.session_state.deadlines.get(key),
            key=f"deadline_{key}"
        )




# WEEKLY AVAILABILITY
st.subheader("Weekly Availability")

days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
timeslots = ["Morning","Afternoon","Evening"]

availability = {}

for d in days:
    st.markdown(f"### {d}")
    availability[d] = {}

    cols = st.columns(3)

    for i, slot in enumerate(timeslots):
        with cols[i]:
            checked = st.checkbox(f"{slot}", key=f"{d}_{slot}")

            if checked:
                hours = st.number_input(
                    "Hours",
                    min_value=1,
                    max_value=4,
                    value=2,
                    key=f"hours_{d}_{slot}"
                )

                do_split = st.radio(
                    "Allow multiple subjects in this time slot?",
                    ["No", "Yes"],
                    key=f"split_{d}_{slot}"
                )

                parts = 1
                if do_split == "Yes":
                    parts = st.number_input(
                        "How many subjects can share this slot?",
                        min_value=1,
                        max_value=int(hours) if hours > 0 else 1,
                        value=int(hours) if hours > 0 else 1,
                        key=f"parts_{d}_{slot}"
                    )

                availability[d][slot] = {
                    "hours": hours,
                    "split": do_split == "Yes",
                    "parts": parts
                }






def generate_asp_facts(subject_data, availability):
    lines = []

    # DAYS (ONLY IF USED)
    used_days = [
        d.lower() for d, slots in availability.items()
        if any(slot_data["hours"] > 0 for slot_data in slots.values())
    ]

    if used_days:
        lines.append("day(" + "; ".join(used_days) + ").\n")


    # SUBJECTS
    subjects = [s.lower() for s in subject_data.keys()]
    lines.append("subject(" + "; ".join(subjects) + ").\n")

    
    # SUBJECT PROPERTIES
    lines.append("% SUBJECT PROPERTIES")

    for s, props in subject_data.items():
        s = s.lower()

        lines.append(f"difficulty({s},{props['Difficulty']}).")
        lines.append(f"priority({s},{props['Priority']}).")
        lines.append(f"subject_strength({s},{props['Strength']}).")

    lines.append("")

    # AVAILABILITY
    lines.append("% AVAILABILITY")

    for day, slots in availability.items():
        day = day.lower()

        for slot, data in slots.items():
            slot = slot.lower()

            if data["hours"] > 0:
                lines.append(f"available({day},{slot},{data['hours']}).")

    lines.append("")

   
    # AVOID
    lines.append("% AVOID")

    all_days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    all_slots = ["morning","afternoon","evening"]

    for day in all_days:
        for slot in all_slots:

            # normalize lookup properly
            slot_data = availability.get(day.capitalize(), {}).get(slot.capitalize())

            if not slot_data or slot_data.get("hours", 0) <= 0:
                lines.append(f"avoid({day},{slot}).")

    
    lines.append("")

   
    # SPLITS
    lines.append("% SPLITS")

    for day, slots in availability.items():
        day = day.lower()

        for slot, data in slots.items():
            slot = slot.lower()

            if data.get("split", False):
                lines.append(f"split({day},{slot},{data['parts']}).")

    lines.append("")

    return "\n".join(lines)





DAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

TIME_MAP = {
    "morning": 8,
    "afternoon": 13,
    "evening": 18,
}

def clingo_to_events(models):
    events = []

    for model in models:
        for atom in model:

            if not atom.startswith("study("):
                continue

            inside = atom[len("study("):-1]
            subject, day, slot, hour_index = [p.strip() for p in inside.split(",")]

            hour_index = int(hour_index)

            base_hour = TIME_MAP.get(slot, 9)
            day_index = DAY_MAP.get(day, 0)

            today = datetime.today()
            start_date = today + timedelta(days=(day_index - today.weekday()) % 7)

            # each I = 1 hour offset
            start = start_date.replace(hour=base_hour, minute=0) + timedelta(hours=hour_index - 1)

            end = start + timedelta(hours=1)

            events.append({
                "title": subject,
                "start": start.isoformat(),
                "end": end.isoformat(),
            })

    return events


def merge_events(events):
    events = sorted(events, key=lambda x: x["start"])

    merged = []

    for event in events:
        if not merged:
            merged.append(event)
            continue

        last = merged[-1]

        if (
            last["title"] == event["title"]
            and last["end"] == event["start"]
        ):
            # extend previous event
            last["end"] = event["end"]
        else:
            merged.append(event)

    return merged


def extract_weeks_per_subject(models):
    result = {}

    for model in models:
        for atom in model:
            if atom.startswith("weeks_needed("):
                inside = atom[len("weeks_needed("):-1]
                subject, weeks = inside.split(",")
                result[subject.strip()] = int(weeks)

    return result



def shift_event(event, deadline, weeks_needed):
    start = datetime.fromisoformat(event["start"])
    end = datetime.fromisoformat(event["end"])

    duration = end - start

    deadline_dt = datetime.combine(deadline, datetime.min.time())

    window_start = deadline_dt - timedelta(weeks=weeks_needed)

    # preserve original weekday/time from Clingo
    weekday_offset = (start.weekday() - window_start.weekday()) % 7

    corrected_start = window_start + timedelta(days=weekday_offset)

    # KEEP ORIGINAL HOUR (THIS IS THE IMPORTANT FIX)
    corrected_start = corrected_start.replace(
        hour=start.hour,
        minute=0
    )

    event["start"] = corrected_start.isoformat()
    event["end"] = (corrected_start + duration).isoformat()

    return event





if st.button("Generate Schedule"):

    if subject_data and availability:

        # 1. Generate facts.lp
        asp_text = generate_asp_facts(subject_data, availability)

        with open("facts.lp", "w", encoding="utf-8") as f:
            f.write(asp_text)

        # 2. Run Clingo
        control = clingo.Control()
        control.load("scheduleTest.lp")
        control.load("facts.lp")

        
        control.configuration.solve.models = 1

        control.ground([("base", [])])

        models = []

        def on_model(model):
            atoms = [str(s) for s in model.symbols(shown=True)]
            models.append(atoms)

        control.solve(on_model=on_model)

        # 3. Extract weeks_needed FIRST (IMPORTANT FIX)
        weeks_map = extract_weeks_per_subject(models)

        # 4. Convert raw ASP output → events
        raw_events = clingo_to_events(models)

        # 5. SHIFT events using deadlines
        shifted_events = []

        for e in raw_events:
            subject = e["title"]
            weeks_needed = weeks_map.get(subject, 1)
            deadline = st.session_state.deadlines.get(subject.lower())

            if deadline:
                shifted_events.append(
                    shift_event(e, deadline, weeks_needed)
                )
            else:
                shifted_events.append(e)

        # 6. Merge AFTER shifting (important)
        events = merge_events(shifted_events)

        # 7. Save to session + file
        st.session_state.calendar_events = events

        with open("calendar_events.json", "w") as f:
            json.dump(events, f)

      
            
        # 7. Show results
        st.subheader("Generated Schedule")

        has_study = any(
            atom.startswith("study(")
            for m in models
            for atom in m
        )

        if not models or not has_study:
            st.session_state.schedule_type = "warning"
            st.session_state.schedule_message = (
                "No valid schedule found. You may need to add more available days or time slots or splits are impossible."
            )
        else:
            st.session_state.schedule_type = "success"
            st.session_state.schedule_message = "\n".join(models[0])

    else:
        st.session_state.schedule_type = "warning"
        st.session_state.schedule_message = (
            "Please enter subjects and availability first."
        )


if st.session_state.schedule_type == "warning":
    st.warning(st.session_state.schedule_message)

elif st.session_state.schedule_type == "success":
    st.subheader("Generated Schedule")
    st.code(st.session_state.schedule_message)


# ---------------------------------------------------------------------------
# CALANDAR


st.title("Calendar")


# SESSION INIT
if "calendar_events" not in st.session_state:
    st.session_state.calendar_events = []
    if os.path.exists("calendar_events.json"):
        with open("calendar_events.json", "r") as f:
            st.session_state.calendar_events = json.load(f)

if "view" not in st.session_state:
    st.session_state.view = "dayGridMonth"

if "view_date" not in st.session_state:
    st.session_state.view_date = None



# OPTIONS
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




# RENDER
state = calendar(options=calendar_options)

#st.write(state)


# RESET BUTTON 
if st.button("Reset Calendar"):
    st.session_state.calendar_events = []

    if os.path.exists("calendar_events.json"):
        os.remove("calendar_events.json")

    st.rerun()
    

# INTERACTIONS
if state.get("callback") == "dateClick":
    st.session_state.view_date = state["dateClick"]["date"]
    st.session_state.view = "timeGridDay"
    st.rerun()