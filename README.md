# Ruta7 - Car Rental Platform

A minimal, single-process car rental app for a fictional Spanish rental agency operating across 7 cities (Madrid, Barcelona, Valencia, Sevilla, Málaga, Tenerife, Mallorca). Built for the DevOps course Assignment 1.

## Domains

- **Vehicle** (`vehicle_info.py`) - vehicles, their status, and location.
- **Reservations** (`rentals.py`) - customer bookings against the Vehicle.
- **Transport** (`transport.py`) - moves vehicles between cities by truck or ship, with a queue that batches vehicles before departure.

## Requirements

- Python 3.11+
- uv

## Setup
This repo uses [uv](https://docs.astral.sh/uv/) to manage the Python environment. Install uv once per machine (see uv's docs):

```bash
git clone https://github.com/Rdrg-Blnc-IE/devops-assignment-1
cd devops-assignment-1

uv venv                           # create a local virtual environment (.venv)
uv pip install -r requirements.txt   # install pytest into it

```

## Running the app

```bash
uv run python app.py
```

Then open **http://localhost:5000**.

No manual setup step is needed -- the SQLite schema is created automatically on first run if it doesn't already exist.

## Configuration

All configuration is via environment variables, each with a working default:

| Variable     | Default         | Purpose                                                                |
|--------------|-----------------|------------------------------------------------------------------------|
| `PORT`       | `5000`          | Port the app listens on                                                |
| `HOST`       | `0.0.0.0`       | Bind address                                                           |
| `DATA_DIR`   | `./src`         | Directory for the SQLite file (`vehicles.db`)                          |
| `SECRET_KEY` | dev placeholder | Flask session signing key - set a real value for any shared deployment |

## Seeding sample data

A one-time script builds sample vehicles, customers, and rentals from a dataset:

Note: No need to run this, the repo already contains the sample database, vehicles.db.

```bash
uv run python car_rental/data_manipulation.py
```

## Running tests and coverage

```bash
uv run python -m pytest tests/test_database.py -v   #runs a single test file
uv run pytest -q                                    # run all tests
```

## What's working

Landing page to choose from customer or enterprise

- Customer:
  - customer login (by id, no password)
  - dashboard
  - renting a car
  - viewing/cancelling a rental


- Enterprise:
  - enterprise dashboard
  - vehicle list
  - Transport routing
  - transport queueing
  - rentals list
  - customer list

## Transport logic workflow
The transport system manages vehicle relocation across different locations through a queued workflow:

### 1. Initiating a Request (`request_transport`)
* **Trigger:** An enterprise user selects an active vehicle and a target destination.
* **Validation:** 
  * Confirms the target destination differs from the vehicle's current location.
  * Ensures the vehicle is not already queued or currently `in_transit`.
* **Transport Mode Assignment:**
  * **Mainland to Mainland:** Assigned to **Truck Transport** (e.g. Madrid to Barcelona).
  * **Mainland/Island to Island:** Assigned to **Ship Transport** (e.g., Madrid to Tenerife/Mallorca or Tenerife to Mallorca).
*
* **Action:** Creates a new transport record marked with a **`pending`** status and appends it to the queue.

### 2. Processing the Queue (`process_queue`)
* **Evaluation:** Pending transport requests are evaluated in first-in, first-out (**FIFO**) order.
* **Capacity Check:** Verifies that the vehicle's current location has an open transport dispatch slot.
* **State Change:** Upon approval, the status updates from **`pending`** to **`in_transit`**.

### 3. Completing Relocation (`complete_transport`)
* **Arrival:** Once the queue is sufficient to start the trip, the transport happens and the record status updates to **`completed`**.
* **Database Sync:** Updates the vehicle's `location` attribute in the database to the new location, making it available for local customer bookings at that site.

## More detail

- `ADR.md` - architecture decisions and why they were made.
- `AI_USAGE.md` - log of AI assistance used while building this.