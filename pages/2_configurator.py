import streamlit as st
import yaml
from datetime import datetime
from pathlib import Path

CONFIG_FILE = "config.yaml"


# --------------------
# Helpers
# --------------------
def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(config):
    # Fuerza start_day a string
    if "start_day" in config:
        config["start_day"] = str(config["start_day"])
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config, f, sort_keys=False, allow_unicode=True)


# --------------------
# Editores
# --------------------
def edit_global_tasks(config):
    st.header("🌍 Global Tasks")

    global_tasks = config.get("global_tasks", [])
    new_global_tasks = []

    # Recopilar opciones para dependencias
    all_dependency_options = []
    for g in global_tasks:
        all_dependency_options.append(g["name"])
    for pname, tasks in config.get("process_templates", {}).items():
        all_dependency_options.append(pname)
        for t in tasks:
            all_dependency_options.append(t["name"])
    for m in config.get("milestones", []):
        all_dependency_options.append(m["name"])

    for i, task in enumerate(global_tasks):
        with st.expander(f"🌐 Global Task {task['name']}", expanded=False):
            tname = st.text_input("Nombre", task["name"], key=f"gt_{i}_name")
            tdur = st.number_input(
                "Duración (h)", min_value=0.0, step=1.0,
                value=float(task.get("duration", 1)), key=f"gt_{i}_dur"
            )
            ttype = st.selectbox(
                "Tipo", ["manual", "automated"],
                index=["manual", "automated"].index(task.get("type", "manual")),
                key=f"gt_{i}_type"
            )
            tserver = st.text_input("Servidor (opcional)", task.get("server", ""), key=f"gt_{i}_server")
            tprio = st.number_input(
                "Prioridad", min_value=1, step=1,
                value=int(task.get("priority", 999)), key=f"gt_{i}_prio"
            )
            deps = task.get("dependencies", [])
            deps = [d for d in deps if d in all_dependency_options]  # 🔧 FIX
            deps = st.multiselect(
                "Dependencias",
                options=all_dependency_options,
                default=deps,
                key=f"gt_{i}_deps"
            )
            if st.button("🗑 Eliminar", key=f"gt_{i}_del"):
                continue
            new_global_tasks.append({
                "name": tname,
                "duration": tdur,
                "type": ttype,
                "server": tserver if tserver else None,
                "priority": tprio,
                "dependencies": deps
            })

    if st.button("➕ Añadir Global Task"):
        new_global_tasks.append({
            "name": f"global_task_{len(new_global_tasks)+1}",
            "duration": 1,
            "type": "manual",
            "priority": 999,
            "dependencies": []
        })

    config["global_tasks"] = new_global_tasks
    return config


def edit_templates(config):
    st.header("📦 Process Templates")

    templates = config.get("process_templates", {})

    # Recopilar dependencias posibles
    all_dependency_options = []
    for g in config.get("global_tasks", []):
        all_dependency_options.append(g["name"])
    for pname, tasks in templates.items():
        all_dependency_options.append(pname)  # dependencia al proceso entero
        for t in tasks:
            all_dependency_options.append(t["name"])
    for m in config.get("milestones", []):
        all_dependency_options.append(m["name"])

    new_templates = {}
    for pname, tasks in templates.items():
        with st.expander(f"🧩 Template: {pname}", expanded=False):
            new_pname = st.text_input("Nombre plantilla", pname, key=f"{pname}_name")
            new_tasks = []
            for i, task in enumerate(tasks):
                with st.expander(f"➡️ Task {task['name']}", expanded=False):
                    tname = st.text_input("Nombre tarea", task["name"], key=f"{pname}_{i}_name")
                    tdur = st.number_input(
                        "Duración (h)", min_value=0.0, step=1.0,
                        value=float(task["duration"]), key=f"{pname}_{i}_dur"
                    )
                    ttype = st.selectbox(
                        "Tipo", ["manual", "automated"],
                        index=["manual", "automated"].index(task["type"]),
                        key=f"{pname}_{i}_type"
                    )
                    tserver = st.text_input("Servidor (opcional)", task.get("server", ""), key=f"{pname}_{i}_server")
                    tprio = st.number_input(
                        "Prioridad", min_value=1, step=1,
                        value=int(task.get("priority", 999)), key=f"{pname}_{i}_prio"
                    )
                    deps = task.get("dependencies", [])
                    deps = [d for d in deps if d in all_dependency_options]  # 🔧 FIX
                    deps = st.multiselect(
                        "Dependencias",
                        options=all_dependency_options,
                        default=deps,
                        key=f"{pname}_{i}_deps"
                    )
                    if st.button("🗑 Eliminar tarea", key=f"{pname}_{i}_del"):
                        continue
                    new_tasks.append({
                        "name": tname,
                        "duration": tdur,
                        "type": ttype,
                        "server": tserver if tserver else None,
                        "priority": tprio,
                        "dependencies": deps
                    })
            if st.button("➕ Añadir tarea", key=f"{pname}_addtask"):
                new_tasks.append({
                    "name": f"new_task_{len(new_tasks)+1}",
                    "duration": 1,
                    "type": "manual",
                    "priority": 999,
                    "dependencies": []
                })
            new_templates[new_pname] = new_tasks
        if st.button("🗑 Eliminar template", key=f"{pname}_del_template"):
            continue

    if st.button("➕ Añadir template nuevo"):
        new_templates[f"template_{len(new_templates)+1}"] = []

    config["process_templates"] = new_templates
    return config


# --------------------
# Main
# --------------------
def main():
    st.set_page_config(page_title="Editor YAML", layout="wide")
    st.title("⚙️ Editor de configuración del proyecto")

    config = load_config()

    # Start day
    raw_start = config.get("start_day", None)
    if raw_start:
        if isinstance(raw_start, str):
            start_date = datetime.fromisoformat(raw_start)
        else:
            start_date = raw_start
    else:
        start_date = datetime.today()
    config["start_day"] = st.date_input("📅 Start day", value=start_date).isoformat()

    # Secciones de edición
    config = edit_global_tasks(config)
    config = edit_templates(config)

    if st.button("💾 Guardar cambios"):
        save_config(config)
        st.success("Config guardada correctamente.")


if __name__ == "__main__":
    main()
