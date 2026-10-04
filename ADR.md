# Architecture Decision Record - Ruta7 Car Rental Platform

## [1]. Backend framework: Flask
- Date: 23-9-2026
- Status: Decided
- Context: Needed a Python web framework for server-rendered HTML pages in a single-process app, with SQLite handled by hand instead of an ORM.
- Decision: Use Flask with Jinja2 templates.
- Alternatives considered: Django - rejected, its ORM and admin panel aren't needed here. FastAPI - rejected, it's built for JSON APIs, not HTML pages.
- Consequences: Less built-in structure to rely on, but fewer dependencies and simpler code to explain.

## [2]. Domain between Vehicle and Reservations
- Date: 29-9-2026
- Status: Decided
- Context: The two domains need to stay loosely coupled, but a rental still has to reference a real car.
- Decision: A rental stores only the car's reg_num and a price snapshot taken at booking time, instead of reading Vehicle's data live.
- Alternatives considered: querying Vehicle's table directly from Reservations - rejected, since it would couple the two domains and let price changes silently affect old rentals.
- Consequences: One extra lookup per booking, but Reservations stays the clean seam for a future service split.

## [3]. SQLite schema: natural keys, enums as text
- Date: 01-10-2026
- Status: Decided
- Context: SQLite has no enum type, and a vehicle's reg_num is already a unique real-world identifier.
- Decision: Use reg_num as the primary key directly, and store enum fields (status, fuel, type, category) as plain text validated in Python.
- Alternatives considered: adding a separate autoincrement id to vehicles - rejected as redundant since reg_num is already unique.
- Consequences: Simple, readable joins, but reg_num can't be changed later without updating a primary key.

## [4]. Testing approach: business logic first, routes untested
- Date: 02-10-2026
- Status: Decided
- Context: Limited time meant choosing where to focus testing toward the 70% bar.
- Decision: Prioritized the builder validation rules and the transport routing/queue logic; tested the DB layer against a real temporary SQLite file. Flask routes were left untested.
- Alternatives considered: mocking the database entirely - rejected for the DB layer's own tests, since a fake store could pass even with broken SQL.
- Consequences: Core logic is well covered, but a routing or template bug could still slip through untested.

## [5]. Deliberately not built: the enterprise web UI
- Date: 04-10-2026
- Status: Decided
- Context: Not enough time to finish both the customer and staff sides of the app to the same standard.
- Decision: Left the enterprise side as a placeholder page and focused on finishing the customer flow (login, dashboard, rent, view rental) completely.
- Alternatives considered: building a thin version of every enterprise screen - rejected, since it would leave everything half-working instead of one side fully working.
- Consequences: Staff have no UI yet to manage the Vehicle, but the customer flow is solid and demo-ready.