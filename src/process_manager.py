# process_manager.py
import yaml
from src.models import Task, Process
from collections import defaultdict

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_processes(config):
    """
    Construye tareas y procesos (clientes + global) a partir del YAML.
    - Las tareas generadas tienen nombre único implícito: para clientes se usan prefijos
      "ClientName::Template::TaskName" y para globals "Global::GName::TaskName" (si plantilla)
      o "Global::TaskName" (si simple).
    - Devuelve: processes (lista de Process), mappings útiles (global_last_task_map).
    """

    process_templates = config.get("process_templates", {})
    clients_cfg = config.get("clients", [])
    milestones_cfg = config.get("milestones", [])
    global_tasks_cfg = config.get("global_tasks", [])
    clients_list = [c["name"] for c in clients_cfg]

    # 1) Crear milestones (Task with duration 0)
    milestones_map = {}
    milestone_tasks = []
    for m in milestones_cfg:
        m_name = m["name"]
        start_after = m.get("start_after", 0)
        t = Task(
            name=m_name,
            duration=0,
            task_type="milestone",
            client="Global",
            start_after=start_after,
            priority=m.get("priority", 999)
        )
        milestones_map[m_name] = t
        milestone_tasks.append(t)

    # 2) Expandir global_tasks. Guardar "último nodo" por template o por nombre.
    global_tasks_expanded = []
    # keys of global_last_task_map:
    #  - ('template', template_name) -> Task (last of that expanded template as Global)
    #  - ('name', global_task_name) -> Task (for simple global tasks)
    global_last_task_map = {}

    for gdef in global_tasks_cfg:
        # Caso: usa template
        if "template" in gdef and gdef["template"] in process_templates:
            template_name = gdef["template"]
            template_tasks = process_templates[template_name]
            mapping = {}
            expanded = []
            for tdef in template_tasks:
                fq_name = f"Global::{gdef.get('name',template_name)}::{tdef['name']}"
                t = Task(
                    name=fq_name,
                    duration=tdef["duration"],
                    task_type=tdef["type"],
                    client="Global",
                    server=tdef.get("server"),
                    start_after=tdef.get("start_after", 0),
                    priority=tdef.get("priority", gdef.get("priority", 999))
                )
                mapping[tdef["name"]] = t
                expanded.append(t)
            # Resolver dependencias internas de la plantilla (local names)
            for tdef in template_tasks:
                t = mapping[tdef["name"]]
                for dep in tdef.get("dependencies", []):
                    # dep can be local task name or milestone name or (rare) template name - handle milestones
                    if dep in mapping:
                        t.dependencies.append(mapping[dep])
                    elif dep in milestones_map:
                        t.dependencies.append(milestones_map[dep])
                    else:
                        # Could be reference to some global milestone or will be resolved later
                        # We'll attempt to resolve by name from milestones_map
                        if dep in milestones_map:
                            t.dependencies.append(milestones_map[dep])
            # last task of this global template:
            last = expanded[-1]
            global_last_task_map[("template", template_name)] = last
            # also map by the global's own name in case other refer by global name
            if "name" in gdef:
                global_last_task_map[("name", gdef["name"])] = last

            global_tasks_expanded.extend(expanded)

        else:
            # Caso: tarea simple global
            # duration_per_client optional
            dur = gdef.get("duration", gdef.get("duration_per_client", 1) * max(1, len(clients_list)))
            t = Task(
                name=f"Global::{gdef['name']}",
                duration=dur,
                task_type=gdef.get("type", "manual"),
                client="Global",
                server=gdef.get("server"),
                start_after=gdef.get("start_after", 0),
                priority=gdef.get("priority", 999)
            )
            global_tasks_expanded.append(t)
            global_last_task_map[("name", gdef["name"])] = t

    # 3) Construir procesos por cliente
    processes = []
    # Mapa por cliente: cliente -> mapping raw_task_name -> Task (for that client)
    client_task_maps = {}

    for c in clients_cfg:
        client_name = c["name"]
        proc_order = c.get("processes_order", [])
        client_tasks = []
        # mapping across all templates of this client (raw name -> Task object)
        overall_map = {}
        # keep track of last task of each template for that client
        client_template_last = {}

        for template_name in proc_order:
            if template_name not in process_templates:
                raise ValueError(f"Template '{template_name}' not found for client {client_name}")
            template_tasks = process_templates[template_name]
            # local mapping for this template
            local_map = {}
            expanded = []

            for tdef in template_tasks:
                fq_name = f"{client_name}::{template_name}::{tdef['name']}"
                t = Task(
                    name=fq_name,
                    duration=tdef["duration"],
                    task_type=tdef["type"],
                    client=client_name,
                    server=tdef.get("server"),
                    start_after=tdef.get("start_after", 0),
                    priority=tdef.get("priority", 999)
                )
                local_map[tdef["name"]] = t
                expanded.append(t)

            # Resolver dependencias internas / milestones / template-deps / global template last
            for tdef in template_tasks:
                t = local_map[tdef["name"]]
                for dep in tdef.get("dependencies", []):
                    # 1) dep is a local task in same template
                    if dep in local_map:
                        t.dependencies.append(local_map[dep])
                    # 2) dep is in overall_map (task from previous templates of same client)
                    elif dep in overall_map:
                        t.dependencies.append(overall_map[dep])
                    # 3) dep is a milestone
                    elif dep in milestones_map:
                        t.dependencies.append(milestones_map[dep])
                    # 4) dep is a template name -> depends on last task of that template for this client if exists
                    elif ("template", dep) in global_last_task_map:
                        # there exists a global template with this name; but client dependency likely to refer to client's own template
                        # prefer client-side: if client already has that template built, use client's last
                        if dep in client_template_last:
                            t.dependencies.append(client_template_last[dep])
                        else:
                            # fallback to global template last
                            t.dependencies.append(global_last_task_map[("template", dep)])
                    elif dep in process_templates:
                        # depends on another template in the same client (if already built)
                        if dep in client_template_last:
                            t.dependencies.append(client_template_last[dep])
                        else:
                            # If not yet present in client, attempt to use global template last if exists
                            if ("template", dep) in global_last_task_map:
                                t.dependencies.append(global_last_task_map[("template", dep)])
                            else:
                                raise ValueError(f"Dependency on template '{dep}' cannot be resolved for client {client_name}")
                    # 5) dep could be a global simple task name
                    elif ("name", dep) in global_last_task_map:
                        t.dependencies.append(global_last_task_map[("name", dep)])
                    else:
                        raise ValueError(f"Dependencia '{dep}' no resuelta para tarea {t.name} (cliente {client_name})")

            # Append expanded tasks and update maps
            for raw_name, task_obj in local_map.items():
                overall_map[raw_name] = task_obj
                client_tasks.append(task_obj)

            # last task of this template for client
            client_template_last[template_name] = expanded[-1]

        processes.append(Process(client_name, client_tasks))
        client_task_maps[client_name] = overall_map

    # 4) Ahora que tenemos client_template_last info implicitly (we constructed above),
    #    some client tasks might have depended on templates that are global: already handled.
    # 5) Formar el proceso global que contiene milestones + global_tasks_expanded
    processes.append(Process("Global", milestone_tasks + global_tasks_expanded))

    return processes, global_last_task_map
