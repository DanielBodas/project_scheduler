# main.py
from src.process_manager import load_config, build_processes
from src.scheduler import Scheduler
from src.visualization import plot_gantt
from src.models import Person
from datetime import datetime

def main():
    config = load_config("config.yaml")
    processes, global_last_map = build_processes(config)

    # Crear personas (pool)
    people = [Person("Ana"), Person("Luis")]

    # Servidores: nombre -> disponibilidad inicial en horas (0 = al inicio)
    servers = {"S1": 0.0, "S2": 0.0}

    # start_day: datetime
    start_day = datetime.fromisoformat(config.get("start_day"))

    sched = Scheduler(people=people, servers=servers, start_day=start_day)
    scheduled_tasks = sched.schedule(processes)

    # Mostrar plan por consola (orden)
    for t in scheduled_tasks:
        s = start_day + timedelta(hours=t.start_time)
        e = start_day + timedelta(hours=t.end_time)
        print(f"{t.client:10} | {t.name:40} | {t.task_type:9} | {t.assigned_to:10} | {s} -> {e} | prio={t.priority}")

    # Plot Gantt
    plot_gantt(scheduled_tasks, start_day)


if __name__ == "__main__":
    from datetime import timedelta
    main()
