import multiprocessing
import os
import time
from typing import Any, Dict


def cpu_loader_worker(target_percent: float, stop_event: Any) -> None:
    """
    Runs a duty cycle CPU-bound loop on a single core.
    
    A 100ms cycle is divided into active and idle periods:
    - active_time: busy-wait calculating to consume CPU
    - idle_time: sleep to yield CPU to the OS scheduler
    """
    # Lower the scheduling priority of the child process so it doesn't starve the main API process
    if hasattr(os, "nice"):
        try:
            os.nice(19)  # 19 is lowest priority
        except Exception:
            pass

    cycle_duration = 0.1  # 100ms
    active_duration = cycle_duration * (target_percent / 100.0)
    idle_duration = cycle_duration * ((100.0 - target_percent) / 100.0)

    # Use a high-precision counter
    while not stop_event.is_set():
        start_time = time.perf_counter()
        
        # Busy-wait loop (CPU active)
        while (time.perf_counter() - start_time) < active_duration:
            # Perform dummy arithmetic calculations to keep CPU busy
            _ = 12345.0 * 54321.0
            
        # Idle period (sleep)
        if idle_duration > 0:
            time.sleep(idle_duration)


class CPULoaderManager:
    def __init__(self) -> None:
        # Use 'spawn' start method to avoid fork-safety deadlock issues (such as with locks/logging/db pools)
        self._ctx = multiprocessing.get_context("spawn")
        self.processes: list[Any] = []
        self.stop_event = self._ctx.Event()
        self.active_target: float | None = None

    def start(self, target: float = 70.0) -> None:
        """
        Starts the CPU loaders for all detected CPU cores.
        """
        if self.is_running():
            self.stop()
            
        self.stop_event.clear()
        self.active_target = target
        
        # Detect the number of logical cores
        num_cores = os.cpu_count() or 1
        
        self.processes = []
        for i in range(num_cores):
            p = self._ctx.Process(
                target=cpu_loader_worker,
                args=(target, self.stop_event),
                name=f"cpu-loader-worker-{i}",
                daemon=True
            )
            p.start()
            self.processes.append(p)

    def stop(self) -> None:
        """
        Stops all running CPU loaders.
        """
        self.stop_event.set()
        
        # 1. Ask all processes to terminate in parallel
        for p in self.processes:
            if p.is_alive():
                try:
                    p.terminate()
                except Exception:
                    pass
        
        # 2. Wait a short period for them to exit
        for p in self.processes:
            if p.is_alive():
                p.join(timeout=0.2)
                
        # 3. Force kill any processes that are still alive
        for p in self.processes:
            if p.is_alive():
                try:
                    p.kill()
                    p.join(timeout=0.2)
                except Exception:
                    pass
                    
        # 4. Clean up resources
        for p in self.processes:
            try:
                p.close()
            except Exception:
                pass
                    
        self.processes = []
        self.active_target = None

    def is_running(self) -> bool:
        """
        Checks if any cpu loader processes are running.
        """
        return len(self.processes) > 0 and any(p.is_alive() for p in self.processes)

    def get_status(self) -> Dict[str, Any]:
        """
        Returns the current status of the loader.
        """
        running = self.is_running()
        active_workers = len([p for p in self.processes if p.is_alive()])
        
        return {
            "running": running,
            "target_cpu_percent": self.active_target if running else None,
            "active_workers": active_workers,
            "total_cores": os.cpu_count() or 1
        }


# Singleton manager instance
cpu_loader = CPULoaderManager()
