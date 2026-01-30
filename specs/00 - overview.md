# Overview

- This is a simple web app for creating teacher schedulings.
- Is a simple app designed to be used by a single user
- the user will insert all the data (teachers, classes, constraints) and then will start the generation of a schedule
- the schedule will be saved as both pdf and json

## Architecture
- it is composed by a frontend and a backend
- the frontend is a react app
- the backend is a fastapi app

## Technologies and libraries
- uv is used to manage the project, add packages with `uv add PACKAGE_NAME`
- use ortools package to manage constraints and solvers
- use sqllite as db, but prepare the road for a fully fledged DB
