# models.py
class Task:
    def __init__(self, name, duration, task_type, client=None, server=None,
                 dependencies=None, start_after=0, priority=999):
        """
        name: nombre legible (se usará también para display); internamente
              los tasks que se generan para clientes y globals tienen nombres únicos compuestos.
        duration: en horas (int/float)
        task_type: "manual", "automated", "milestone"
        client: nombre del cliente o "Global"
        server: nombre del servidor si requiere uno (p.ej "S1"), o None
        dependencies: lista de Task (se enlaza después en process_manager)
        start_after: horas desde start_day mínima para empezar (milestone)
        priority: entero (1 = alta prioridad). Default 999.
        """
        self.name = name
        self.duration = duration
        self.task_type = task_type
        self.client = client
        self.server = server
        self.dependencies = dependencies or []
        self.start_after = start_after
        self.priority = priority

        # campos calculados por el scheduler:
        self.assigned_to = None  # persona o servidor o "Milestone"
        self.start_time = None   # horas desde start_day (float)
        self.end_time = None     # horas desde start_day (float)

    def __repr__(self):
        return f"Task({self.client}:{self.name}, type={self.task_type}, prio={self.priority})"


class Process:
    def __init__(self, name, tasks=None):
        self.name = name
        self.tasks = tasks or []

    def __repr__(self):
        return f"Process({self.name}, tasks={len(self.tasks)})"


class Person:
    def __init__(self, name):
        self.name = name
        self.available_from = 0.0  # horas desde start_day

    def __repr__(self):
        return f"Person({self.name}, avail={self.available_from})"
