import streamlit as st
import clingo
import pandas as pd
from datetime import datetime, timedelta

st.subheader("Subjects")

subject_input = st.text_input(
    "Enter subjects (comma separated)",
    placeholder="e.g. im, tcs2"
)

selected_subjects = [
    s.strip() for s in subject_input.split(",") if s.strip()
]



df = pd.DataFrame({
    "Subject": selected_subjects,
    "Difficulty": [1]*len(selected_subjects),
    "Priority": [1]*len(selected_subjects),
    "Strength": [1]*len(selected_subjects),
})

edited_df = st.data_editor(
    df,
    width= "stretch",
    num_rows="fixed",
    column_config={
        "Difficulty": st.column_config.NumberColumn(
            "Difficulty",
            min_value=1,
            max_value=5,
            step=1
        ),
        "Priority": st.column_config.NumberColumn(
            "Priority",
            min_value=1,
            max_value=5,
            step=1
        ),
        "Strength": st.column_config.NumberColumn(
            "Strength",
            min_value=1,
            max_value=5,
            step=1
        ),
    }
)

subject_data = edited_df.set_index("Subject").to_dict("index")



st.subheader("Deadlines")
deadlines = {}

if selected_subjects:
    st.write("Enter deadlines for each subject:")

    for subject in selected_subjects:
        deadlines[subject] = st.date_input(
            f"Deadline for {subject}",
            value=None,  # no default date
            key=f"deadline_{subject}"
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
                    min_value=0,
                    max_value=10,
                    value=2,
                    key=f"hours_{d}_{slot}"
                )

                do_split = st.radio(
                    "Split into 1-hour blocks?",
                    ["No", "Yes"],
                    key=f"split_{d}_{slot}"
                )

                parts = 1
                if do_split == "Yes":
                    parts = st.number_input(
                        "How many sections?",
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




st.subheader("Study Plan Choice")
schedule_choice = st.radio(
    "Do you want multiple schedule to select from?",
    ["No", "Yes"],
    key="schedule_choice"
)


def generate_asp_facts(subject_data, availability):
    lines = []

    # =========================
    # DAYS (ONLY IF USED)
    # =========================

    used_days = [
        d.lower() for d, slots in availability.items()
        if any(slot_data["hours"] > 0 for slot_data in slots.values())
    ]

    if used_days:
        lines.append("day(" + "; ".join(used_days) + ").\n")

    # =========================
    # SUBJECTS
    # =========================
    subjects = [s.lower() for s in subject_data.keys()]
    lines.append("subject(" + "; ".join(subjects) + ").\n")

    # =========================
    # SUBJECT PROPERTIES
    # =========================
    lines.append("% =========================")
    lines.append("% SUBJECT PROPERTIES")
    lines.append("% =========================")

    for s, props in subject_data.items():
        s = s.lower()

        lines.append(f"difficulty({s},{props['Difficulty']}).")
        lines.append(f"priority({s},{props['Priority']}).")
        lines.append(f"subject_strength({s},{props['Strength']}).")

    lines.append("")

    # =========================
    # AVAILABILITY
    # =========================
    lines.append("% =========================")
    lines.append("% AVAILABILITY")
    lines.append("% =========================")

    for day, slots in availability.items():
        day = day.lower()

        for slot, data in slots.items():
            slot = slot.lower()

            if data["hours"] > 0:
                lines.append(f"available({day},{slot},{data['hours']}).")

    lines.append("")

    # =========================
    # OPTIONAL SPLITS
    # =========================
    lines.append("% =========================")
    lines.append("% OPTIONAL SPLITS")
    lines.append("% =========================")

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
    "morning": 9,
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
            subject, day, slot, block = [p.strip() for p in inside.split(",")]

            hour = TIME_MAP.get(slot, 9)
            day_index = DAY_MAP.get(day, 0)

            today = datetime.today()
            start_date = today + timedelta(days=(day_index - today.weekday()) % 7)

            block = int(block)

            start = start_date.replace(hour=hour, minute=0)
            start = start + timedelta(minutes=(block - 1) * 60)

            end = start + timedelta(minutes=60)

            events.append({
                "title": subject,
                "start": start.isoformat(),
                "end": end.isoformat(),
            })

    return events



def extract_weeks(models):
    for model in models:
        for atom in model:
            if atom.startswith("weeks_needed("):
                return int(atom.split("(")[1].split(")")[0])
    return 1

def shift_event(event, deadline, weeks_needed):
    start = datetime.fromisoformat(event["start"])
    end = datetime.fromisoformat(event["end"])

    duration = end - start

    deadline_dt = datetime.combine(deadline, datetime.min.time())

    window_start = deadline_dt - timedelta(weeks=weeks_needed)

    # preserve original weekday/time from Clingo
    weekday_offset = (start.weekday() - window_start.weekday()) % 7

    corrected_start = window_start + timedelta(days=weekday_offset)

    # 🔥 KEEP ORIGINAL HOUR (THIS IS THE IMPORTANT FIX)
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

        if schedule_choice == "Yes":
            control.configuration.solve.models = 0
        else:
            control.configuration.solve.models = 1

        control.ground([("base", [])])

        models = []

        def on_model(model):
            atoms = [str(s) for s in model.symbols(shown=True)]
            models.append(atoms)

        control.solve(on_model=on_model)

        # 3. Extract weeks_needed FIRST (IMPORTANT FIX)
        weeks_needed = extract_weeks(models)
        st.write("Weeks needed:", weeks_needed)

        # 4. Convert schedule
        events = clingo_to_events(models)

        # 5. SHIFT EVENTS BACK BY WEEKS_NEEDED
        adjusted_events = []

        for e in events:
            subject = e["title"]
            deadline = deadlines.get(subject)

            if not deadline:
                adjusted_events.append(e)
                continue

            adjusted_events.append(
                shift_event(e, deadline, weeks_needed)
            )

        # 6. Save to calendar
        st.session_state.calendar_events = adjusted_events

        # 7. Show results
        st.subheader("Generated Schedule")

        has_study = any(
            atom.startswith("study(")
            for m in models
            for atom in m
        )

        if not models or not has_study:
            st.warning("No valid schedule found.")
            st.info(
                "You may need to add more available days or time slots "
                "to fit all required study hours."
            )
        else:
            for i, m in enumerate(models):
                st.write(f"### Solution {i+1}")
                st.code("\n".join(m))

    else:
        st.warning("Please enter subjects and availability first.")


