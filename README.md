# ecodish365

Monorepo for the **ecodish365** stack: a **Next.js** frontend and **Django** backend with nutrition and sustainability calculators. Core numeric scoring for **HSR**, **FCS**, and **HENI** lives in **`backend/rust_core`** (PyO3 extension) and is consumed from Python.

## Repository layout

| Path | Description |
|------|-------------|
| `frontend/` | Next.js 15 app (`npm run dev`) |
| `backend/` | Django project (`dish_project`), calculators, CNF-backed APIs |
| `backend/rust_core/` | Rust crate built with **maturin** → Python module `rust_core` |
| `backend/raw_cnf/` | Canadian Nutrient File (CNF) CSV data used by calculators |

## Prerequisites

- **Python** 3.10+ (backend venv recommended under `backend/.venv`)
- **Node.js** 18+ (frontend)
- **Rust** toolchain + [**maturin**](https://www.maturin.rs/) (to compile `rust_core`)

## Backend setup

From the repo root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Build and install the native extension (required for HSR / FCS / HENI scoring):

```bash
cd rust_core
maturin develop
```

Configure environment (see `backend/dish_project/settings.py` for full list). At minimum you will typically set:

- `DJANGO_SETTINGS_MODULE=dish_project.settings`
- `DJANGO_SECRET_KEY` (production)
- `CNF_FOLDER` if your CNF data is not the default `backend/raw_cnf`

Run migrations and the dev server:

```bash
cd backend
source .venv/bin/activate
python manage.py migrate
python manage.py runserver
```

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

## Tests

```bash
cd backend
source .venv/bin/activate
python manage.py test
```

HENI / FCS-focused suites (examples):

```bash
python manage.py test heni_calculator.tests.test_heni_daly_rust
python manage.py test fcs_calculator.tests.test_fcs_rust
```

## Documentation

- `backend/fcs_calculator/FCS_RUST_INTEGRATION_PLAN.md` — FCS ↔ Rust
- `backend/heni_calculator/HENI_RUST_INTEGRATION_PLAN.md` — HENI ↔ Rust

## License

Add or update a `LICENSE` file at the repo root if this project is published.
