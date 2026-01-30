"""Routers package for API endpoints."""

from squola.routers.teachers import router as teachers_router
from squola.routers.classes import router as classes_router
from squola.routers.matters import router as matters_router
from squola.routers.scheduling import router as scheduling_router

__all__ = ["teachers_router", "classes_router", "matters_router", "scheduling_router"]
