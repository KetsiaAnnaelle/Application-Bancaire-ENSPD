# Banque Analytics Web App (Flask + SQLite + SQLModel)

Single-page web app for banking analytics (clients + admins). Flask serves the backend API and the `main.html` frontend, which are already connected.

## Quick start – launch the whole project

All commands below are run **inside the project folder** (for you: `C:\Users\DELL\Desktop\Projet-GL-ENSPD`).

1. **Create and activate a virtual environment (Windows PowerShell):**

```bash
python -m venv .venv
.venv\Scripts\activate
pip install flask sqlmodel
```

2. **Create / reset and seed the database:**

```bash
python tables__projet.py
```

This drops and recreates the tables, then inserts:
- 2 admins
- 3 clients
- Login credentials
- Sample transactions (for analytics and credit analysis)

3. **Start the project (backend + frontend together):**

```bash
python app.py
```

Then open this URL in your browser:

```text
http://localhost:5000/
```

Flask serves `main.html` at `/`, and the frontend JavaScript calls the Flask API endpoints on the same server.

## Test accounts

### Client logins (Espace Client)
- **Client 1**: `didier.fouda@example.com` / `1234`
- **Client 2**: `clarisse.mbia@example.com` / `1111`
- **Client 3**: `paul.ngono@example.com` / `1980`

### Admin logins (Espace Admin)
- **Admin 1**: `admin1@bankapp.com` / `0123`
- **Admin 2**: `admin2@bankapp.com` / `0000`

## What the admin sees for each client

When logged in as admin:

- **Liste Clients**  
  - Data loaded from `GET /api/admin/clients`.  
  - Each card shows: name, email, account number, current balance, and a risk badge (premium / conditionnel / risque élevé) computed from the client’s balance and transactions.

- **Profil Client**  
  - When you click a client card, the profile view shows personal data (nom, prénom, date de naissance, adresse, email, téléphone) and banking data (numéro de compte, IBAN, RIB, carte).

- **Dashboard Client**  
  - Uses:
    - `GET /api/transactions/monthly?client_id=<id>` to draw a **line chart of the client’s balance over time**.
    - `GET /api/transactions/category-averages?client_id=<id>` to draw a **doughnut chart of expenses by category**.
  - Shows a credit score and monthly income estimate per client, computed by the backend and returned via `/api/admin/clients`.

- **Analyse Crédit (Credit analysis)**  
  - Uses the credit score and endebtment ratio from `/api/admin/clients` to:
    - Classify the client (Éligible / Éligibilité conditionnelle / Non éligible).
    - Display detailed recommendations specific to that client’s situation.

## API overview (used by the frontend)

- **`GET /`**: serves `main.html`.
- **`GET /health`**: simple health check.

### Authentication
- **`POST /api/auth/login/client`** — client login.
- **`POST /api/auth/login/admin`** — admin login.
- **`POST /api/auth/logout`** — logout.
- **`GET /api/auth/current-user`** — returns current logged-in user (client or admin).

### Transactions analytics
- **`GET /api/transactions/monthly`**
  - Returns: `year`, `month`, `income`, `expense`, `net`, `label`.
  - Query params: `start`, `end`, `client_id`.
- **`GET /api/transactions/category-averages`**
  - Returns: average `amount` per `category`.
  - Query params: `start`, `end`, `client_id`.

### Admin clients
- **`GET /api/admin/clients`**
  - **Admin only** (session must contain `user_type = "admin"`).
  - Returns list of clients with:
    - Identity & contact info.
    - Account identifiers.
    - Current balance estimate.
    - Simple `creditScore`, `endebtmentRatio`, `status`, `statusText`.
    - `monthlyIncome` (heuristic from transactions).

### Credit + chat (client space)
- **`POST /api/credit-request`** — client submits a credit request.
- **`POST /api/chat/predict`** — client chat with AI-like banking advice (uses account + transaction history).

## Notes
- Models and engine are defined in `tables__projet.py`; the API reuses that engine.
- If you change models, re-run `python tables__projet.py` to reset the schema and seed data.
- The sample data mixes positive and negative transaction amounts; the backend interprets positive as inflows and negative as outflows for analytics.



