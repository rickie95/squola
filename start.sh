#!/bin/bash

alembic alembic upgrade head && uvicorn squola.main:app --host 0.0.0.0 --port 8000