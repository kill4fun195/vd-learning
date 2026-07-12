from fastapi import APIRouter, Query, status

from app.services.cpu_service import cpu_loader

router = APIRouter(prefix="/cpu", tags=["CPU Load Generator"])


@router.post(
    "/start",
    status_code=status.HTTP_200_OK,
    summary="Start CPU load generator",
    description="Spawns background processes to generate a specific CPU load.",
)
def start_cpu_load(
    target: float = Query(
        default=70.0,
        ge=0.0,
        le=100.0,
        description="Target CPU utilization percentage (0 to 100)"
    )
) -> dict:
    cpu_loader.start(target=target)
    return {
        "message": f"CPU load generator started targeting {target}% CPU usage.",
        "status": cpu_loader.get_status()
    }


@router.post(
    "/stop",
    status_code=status.HTTP_200_OK,
    summary="Stop CPU load generator",
    description="Stops all running background load generator processes.",
)
def stop_cpu_load() -> dict:
    cpu_loader.stop()
    return {
        "message": "CPU load generator stopped.",
        "status": cpu_loader.get_status()
    }


@router.get(
    "/status",
    status_code=status.HTTP_200_OK,
    summary="Get CPU load generator status",
    description="Returns current execution status and configuration.",
)
def get_cpu_status() -> dict:
    return cpu_loader.get_status()
