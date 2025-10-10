# Mini Lead CRM

Ein kleines Lead-Management-System (CRM) mit Backend (FastAPI + SQLite) und Frontend (React + TypeScript + Vite).  
Es erlaubt Leads zu erstellen, optionale Primärkontakte mit E-Mails zu hinterlegen, Leads zu filtern, zu suchen und den Status zu ändern.

---

## Tech-Stack

**Backend:**  
- Python 3.11+  
- FastAPI  
- SQLAlchemy 2.x  
- SQLite (für schnelles Setup)  
- Pydantic (Validierung)

**Frontend:**  
- React 18 + TypeScript + Vite  
- TanStack Query (State & Data Fetching)  
- zod (Formularvalidierung)

**Extras / Optional:**  
- Vitest + React Testing Library für Tests  
- Debounce für Suchfeld im Frontend  
- Logging via `uvicorn`  

---

## Datenmodell

**Leads**  
- `id`: Integer, PK  
- `name`: String, Pflichtfeld  
- `domain`: String, optional  
- `status`: Enum (`new`, `qualified`, `lost`), Default=`new`  
- `created_at`: UTC Timestamp  
- `primary_contact_id`: FK zu Contacts, optional  

**Contacts**  
- `id`: Integer, PK  
- `first_name`: String, optional  
- `last_name`: String, optional  

**ContactEmails**  
- `id`: Integer, PK  
- `contact_id`: FK zu Contacts  
- `value`: String, E-Mail  
- `is_primary`: Boolean, Default=False  
- Constraints: Eindeutige E-Mail pro Kontakt (`lower(value)`), genau eine Primary

---

## API Endpoints

### 1. `POST /leads`
- Erstellt einen Lead, optional mit Primärkontakt + E-Mails  
- Body: `LeadCreate` Schema  
- Response: 201 Created mit LeadRead  

### 2. `GET /leads`
- Listet Leads mit Filter und Pagination  
- Query Params:  
  - `q` (optional): Suche über `name` oder `domain`  
  - `status` (optional): `new` | `qualified` | `lost`  
  - `limit` (optional): max 200, Default 20  
  - `offset` (optional): Default 0  
- Response: `{ items: LeadRead[], total: number }`

### 3. `POST /leads/{id}/status` (Bonus)
- Ändert den Status eines bestehenden Leads  
- Query: `new_status`  
- Response: Aktualisierter Lead (`LeadRead`)

---

## Frontend

- **Seite:** Single Page, zeigt alle Leads  
- **Funktionen:**  
  - Liste der Leads  
  - Suchfeld mit Debounce  
  - Status-Dropdown Filter  
  - Formular zum Anlegen eines Leads mit optionalem Primärkontakt  
  - Status kann direkt in der Liste geändert werden (Inline Edit + Badge)  

---

## Tests

**Backend:**  
- Pytest  
- Testet Lead-Erstellung und GET /leads  

**Frontend:**  
- Vitest + React Testing Library  
- Testet Öffnen des Formulars und UI Interaktion  

---

## Setup & Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Abstriche / Trade-offs

### SQLite statt PostgreSQL
- SQLite für schnelles Setup und lokale Entwicklung.  
- **Vorteil:** Kein Docker/Postgres nötig, schnelle Tests.  
- **Nachteil:** Manche fortgeschrittenen Constraints sind nicht nativ möglich.

### Primary-Email Partial-Unique
- In PostgreSQL könnte man einen Partial-Unique-Index auf `is_primary` erstellen, um sicherzustellen, dass jeder Kontakt genau eine Primary-Email hat.

### Keine Alembic-Migration
- SQLite ist klein, Tabellen werden direkt aus den SQLAlchemy-Models erstellt.  
- **Vorteil:** Einfacher Start, kein Setup-Aufwand.  
- **Nachteil:** Keine Versionierung von Schemaänderungen.

### Tests
- Nur Kern-Tests implementiert (Lead erstellen, GET /leads, einfache Frontend-Testfälle).  
- Kein umfassendes Test-Setup für alle Fehlerfälle oder E-Mail-Validierungen.

---

## SQLite-Einschränkungen

| Feature | PostgreSQL | SQLite | Umsetzung im Projekt |
|---------|------------|--------|--------------------|
| Case-insensitive UNIQUE | ✅ unterstützt | ❌ nicht nativ | Über Python-Code beim Erstellen von E-Mails geprüft |
| Partial Unique Index (`is_primary`) | ✅ direkt in DB | ❌ nicht nativ | In `crud.py` geprüft: mindestens eine Primary-Email wird gesetzt |
| Foreign Keys + ON DELETE SET NULL | ✅ unterstützt | ✅ unterstützt ab SQLite 3.6.19 | Primary-Contact-FK korrekt gesetzt/gelöscht |
| Datetime UTC default | ✅ problemlos | ✅ funktioniert | Mit `datetime.now(timezone.utc)` gelöst |
| Transactions | ✅ unterstützt | ✅ unterstützt | `with db.begin():` im Backend für konsistente Inserts |

**Fazit:**  
SQLite ist ideal für die Challenge wegen einfacher Einrichtung, aber Features wie Partial-Unique Constraints oder Case-Insensitive UNIQUE müssen durch Python-Code umgesetzt werden. In PostgreSQL wären diese Constraints direkt in der Datenbank möglich.
