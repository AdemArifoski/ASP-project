import streamlit as st
import json
import clingo

st.title("Students Schedule")

uploaded_file = st.file_uploader("Upload JSON file", type=["json", "txt"])




# JSON → ASP
def json_to_asp(json_text):
    asp = []

    # Parse the JSON array
    students = json.loads(json_text)

    for data in students:
        sid = data["id"]

        asp.append(f"student({sid}).")

        for sub in data.get("subjects", []):
            s = sub["name"]
            asp.append(f"subject({sid},{s}).")
            asp.append(f"difficulty({sid},{s},{sub['difficulty']}).")
            asp.append(f"priority({sid},{s},{sub['priority']}).")
            asp.append(f"subject_strength({sid},{s},{sub['strength']}).")

        for a in data.get("availability", []):
            asp.append(
                f"available({sid},{a['day']},{a['time']},{a['hours']})."
            )

        for av in data.get("avoid", []):
            asp.append(
                f"avoid({sid},{av['day']},{av['time']})."
            )

        for sp in data.get("split", []):
            asp.append(
                f"split({sid},{sp['day']},{sp['time']},{sp['value']})."
            )

    return "\n".join(asp)



# SOLVER FUNCTION
def run_clingo(asp_facts):
    control = clingo.Control()

    # load your logic program
    control.load("students.lp")

    # add facts dynamically
    control.add("base", [], asp_facts)

    control.ground([("base", [])])

    models = []

    def on_model(model):
        atoms = model.symbols(shown=True)
        models.append([str(a) for a in atoms])

    control.configuration.solve.models = 1
    control.solve(on_model=on_model)

    return models



if uploaded_file is not None:

    if st.button("Generate Schedule"):

        jsonl_text = uploaded_file.read().decode("utf-8")

        asp_facts = json_to_asp(jsonl_text)

        #st.subheader("Generated ASP Facts")
        #st.code(asp_facts, language="prolog")

        models = run_clingo(asp_facts)

        st.subheader("Solution")

        if not models:
            st.warning("No solution found.")
        else:
            st.success("Solution found!")
            for m in models[0]:
                st.write(m)