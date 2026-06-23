# save as app.py
import multiprocessing as mp
import time
import math
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Header, Footer


def cpu_heavy_worker(task_q: mp.Queue, result_q: mp.Queue):
    """Long-running worker process that reads tasks and emits results."""
    while True:
        task = task_q.get()
        if task is None:
            break
        # Simulated heavy CPU work (replace with real work)
        n = task.get("n", 1000000)
        s = 0.0
        for i in range(1, n):
            s += math.sqrt(i)
        result_q.put({"n": n, "result": s, "ts": time.time()})
    result_q.put({"_worker_terminated": True})


class ProcPoolApp(App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # multiprocessing queues for communication
        self.task_q = mp.Queue()
        self.result_q = mp.Queue()
        self.worker_proc = None

    def compose(self) -> ComposeResult:
        yield Header()
        self.table = DataTable()
        self.table.add_columns("n", "result", "ts")
        yield self.table
        yield Footer()

    def on_mount(self):
        # start worker process
        self.worker_proc = mp.Process(
            target=cpu_heavy_worker, args=(self.task_q, self.result_q), daemon=True
        )
        self.worker_proc.start()

        # schedule periodic drain of result queue (runs on UI event loop)
        self.set_interval(0.1, self.drain_results)

        # example: submit some tasks
        for n in (200000, 400000, 800000):
            self.task_q.put({"n": n})

    def drain_results(self):
        """Called on the UI thread — safe to update widgets here."""
        try:
            while True:
                item = self.result_q.get_nowait()
                if item.get("_worker_terminated"):
                    continue
                self.table.add_row(
                    str(item["n"]), f"{item['result']:.3f}", f"{item['ts']:.3f}"
                )
        except Exception:
            # queue empty (mp.Queue raises queue.Empty which is a subclass of Exception here)
            pass

    async def on_unmount(self) -> None:
        # tell worker to stop and join
        if self.worker_proc and self.worker_proc.is_alive():
            self.task_q.put(None)
            self.worker_proc.join(timeout=2)


if __name__ == "__main__":
    # IMPORTANT: multiprocessing needs this guard on Windows
    mp.set_start_method("spawn")  # optional; 'spawn' is safest cross-platform
    ProcPoolApp().run()
