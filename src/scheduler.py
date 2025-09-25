# scheduler.py
from models import Person
from datetime import datetime, timedelta

class Scheduler:
    def __init__(self, people, servers, start_day=None):
        """
        people: list of Person objects
        servers: dict {server_name: available_from_hours} (float)
        start_day: datetime for start reference
        """
        self.people = people
        self.servers = dict(servers)  # copia
        self.start_day = start_day or datetime(2025,1,1,8,0)

    def schedule(self, processes):
        """
        processes: list of Process objects (each with Task instances already with dependencies linking)
        Returns: list of all tasks scheduled (in the order scheduled)
        """
        # collect all tasks
        all_tasks = []
        for p in processes:
            all_tasks.extend(p.tasks)

        # helper: set of scheduled tasks
        scheduled = []
        remaining = set(all_tasks)

        # helper to count dependents (for priority impact)
        def compute_dependents_count():
            cnt = {t: 0 for t in all_tasks}
            for t in all_tasks:
                for d in t.dependencies:
                    cnt[d] = cnt.get(d, 0) + 1
            return cnt

        dependents_count = compute_dependents_count()

        # main loop
        while remaining:
            # 1) Find tasks whose dependencies are already scheduled (or none).
            ready = []
            for t in list(remaining):
                if all(dep in scheduled for dep in t.dependencies):
                    # this task is "ready" logically; compute earliest possible start ignoring resource contention
                    deps_end = 0.0
                    if t.dependencies:
                        deps_end = max(dep.end_time for dep in t.dependencies)
                    earliest = max(deps_end, t.start_after or 0.0)

                    # compute earliest resource availability
                    if t.task_type == "manual":
                        person_available = min(p.available_from for p in self.people) if self.people else float('inf')
                        eff_start = max(earliest, person_available)
                    elif t.task_type == "automated":
                        if t.server:
                            server_avail = self.servers.get(t.server, 0.0)
                            eff_start = max(earliest, server_avail)
                        else:
                            # automated without dedicated server -> can start at earliest (parallel)
                            eff_start = earliest
                    elif t.task_type == "milestone":
                        # milestone has no resource, starts at earliest
                        eff_start = earliest
                    else:
                        eff_start = earliest

                    ready.append((t, eff_start))

            if not ready:
                raise RuntimeError("Deadlock: no hay tareas listas pero quedan tareas por programar (posible ciclo de dependencias)")

            # 2) Choose task to schedule next:
            #    choose minimal eff_start, tie-breaker by score = priority - dependents_count
            min_start = min(s for (_, s) in ready)
            candidates = [t for (t, s) in ready if abs(s - min_start) < 1e-9]

            def score(task):
                return getattr(task, "priority", 999) - dependents_count.get(task, 0)

            # choose candidate with minimal score
            candidates.sort(key=score)
            task_to_sched = candidates[0]

            # recompute chosen's start and end
            deps_end = 0.0
            if task_to_sched.dependencies:
                deps_end = max(dep.end_time for dep in task_to_sched.dependencies)
            start = max(deps_end, task_to_sched.start_after or 0.0)

            if task_to_sched.task_type == "manual":
                # assign to person who becomes available first
                person = min(self.people, key=lambda p: p.available_from)
                start = max(start, person.available_from)
                task_to_sched.assigned_to = person.name
                task_to_sched.start_time = start
                task_to_sched.end_time = start + task_to_sched.duration
                person.available_from = task_to_sched.end_time
            elif task_to_sched.task_type == "automated":
                if task_to_sched.server:
                    # use the server's availability
                    server_av = self.servers.get(task_to_sched.server, 0.0)
                    start = max(start, server_av)
                    task_to_sched.assigned_to = task_to_sched.server
                    task_to_sched.start_time = start
                    task_to_sched.end_time = start + task_to_sched.duration
                    self.servers[task_to_sched.server] = task_to_sched.end_time
                else:
                    # no dedicated server -> can run in parallel, no resource blocking
                    task_to_sched.assigned_to = "System"
                    task_to_sched.start_time = start
                    task_to_sched.end_time = start + task_to_sched.duration
            elif task_to_sched.task_type == "milestone":
                task_to_sched.assigned_to = "Milestone"
                task_to_sched.start_time = start
                task_to_sched.end_time = start  # zero duration
            else:
                # default behavior
                task_to_sched.assigned_to = "Unknown"
                task_to_sched.start_time = start
                task_to_sched.end_time = start + task_to_sched.duration

            # record scheduled
            scheduled.append(task_to_sched)
            remaining.remove(task_to_sched)

        # return scheduled list (in the execution order we selected)
        return scheduled
