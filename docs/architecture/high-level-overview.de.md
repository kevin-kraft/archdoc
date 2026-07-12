# Archdoc High-Level Overview

Dieses Dokument erklaert die implementierte Architektur von Archdoc vom
Source-Code-Scan bis zur SQLite-basierten Review-Oberflaeche.

## Zielbild

Archdoc ist eine deterministische Pipeline fuer Architektur-Dokumentation,
Analyse und Review.

Aktuell besteht das System aus drei groben Teilen:

- **Archdoc Generator** analysiert Source Code und erzeugt JSON.
- **UI Backend** importiert JSON und manuelle Dokumentation in SQLite.
- **Docusaurus Frontend** visualisiert Tabellen, Graphen und User Stories.

Die wichtigste Grenze ist:

> `archdoc` erzeugt Daten. `ui_backend` importiert und fragt Daten ab. Das
> Frontend visualisiert und reviewed. Menschliche Review-Daten werden nicht in
> generated JSON geschrieben.

## Gesamtueberblick

```mermaid
flowchart LR
  A["Utilis Backend Source<br/>api/app"] --> B["archdoc scan<br/>AST Raw Facts"]
  B --> C["raw_code_facts.json"]
  C --> D["archdoc map<br/>Services, Endpoints, Links, Actions"]
  D --> E["Generated Static JSON<br/>site/static/archdoc"]
  D --> F["JSON Schemas<br/>docs/architecture/schemas"]

  G["Manuelle User Stories<br/>docs/architecture/user-stories/*.md"] --> H["ui_backend Import"]
  E --> H
  I["Review Overlay JSON<br/>docs/architecture/overlays"] <--> H

  H --> J["SQLite Read Model<br/>archdoc-review.sqlite3"]
  J --> K["FastAPI Routes<br/>ui_backend"]
  K --> L["Docusaurus Frontend<br/>Tables, Graphs, User Stories"]
```

## Rollen der Komponenten

### `archdoc`

`archdoc` ist der deterministische Generator. Er liest Source Code und erzeugt
ersetzbare Architektur-Daten.

`archdoc` macht aktuell:

- Python AST Scan
- Raw Code Facts
- Service-Erkennung
- FastAPI Endpoint-Erkennung
- Endpoint-zu-Service Linking
- Architecture Action Detection
- Validator Reports
- JSON Schema Export
- Static JSON Export fuer Docusaurus

`archdoc` sollte nicht machen:

- menschliche Review-Staende speichern
- UI-Editing besitzen
- SQLite als primaere Runtime-Datenbank verwalten
- Frontend- oder Backend-Interaktion steuern

### `ui_backend`

`ui_backend` ist die interaktive Review-Schicht. Es importiert generierte JSONs
und manuelle User-Story-Dateien in SQLite.

`ui_backend` macht aktuell:

- SQLite Schema
- Import der generated JSON Dateien
- Import der Markdown User Stories
- Import/Export des Review Overlays
- serverseitige Suche, Sortierung, Filterung und Pagination
- API fuer Service Action Graph
- API fuer User Story Linking

`ui_backend` macht bewusst nicht:

- Source Code scannen
- generated JSON erzeugen
- produktive Utilis Tenant-Daten speichern

### Docusaurus Frontend

Docusaurus ist aktuell die Shell fuer Dokumentation und interaktive Views.

Das Frontend macht aktuell:

- API Endpoint Catalog
- Endpoint-Service Interface Tabelle
- Service Operation Tabelle
- Service Action Graph
- Validation Issues
- User Story Review und Trace View
- Review Controls
- Static Fallback, falls Backend nicht laeuft

## Daten-Layer

```mermaid
flowchart TB
  A["Layer 1: Raw Facts<br/>syntaxnahe AST Fakten"] --> B["Layer 2: Catalog Mapping<br/>Services, Endpoints, Links"]
  B --> C["Layer 3: Action Mapping<br/>DB, Permissions, Worker, External Calls, Entities"]
  C --> D["Layer 4: Validation<br/>Kollisionen, offene Links, Warnungen"]
  D --> E["Layer 5: Review Read Model<br/>SQLite + Overlay"]
  E --> F["Layer 6: UI Views<br/>Tables, Graphs, User Stories"]
```

### Layer 1: Raw Facts

Output:

- `docs/architecture/generated_raw/raw_code_facts.json`

Ziel:

- Code syntaktisch und deterministisch erfassen
- noch keine zu starke Architektur-Interpretation
- Source Locations fuer Erklaerbarkeit behalten

Beispiele:

- Klassen
- Methoden/Funktionen
- Decorators
- Calls
- Assignments
- Klassenfelder
- FastAPI Route Signale

### Layer 2: Catalog Mapping

Hier entstehen:

- Services
- Service Operations
- API Endpoints
- Endpoint-Service Links

Beispiel:

```mermaid
flowchart LR
  A["Endpoint<br/>POST /users/{user_id}/reset-password"] --> B["Endpoint-Service Link"]
  B --> C["Service<br/>admin.admin-user"]
  C --> D["Operation<br/>reset_password"]
```

### Layer 3: Architecture Actions

Output:

- `site/static/archdoc/architecture_actions.json`

Ziel:

- sichtbar machen, was eine Operation intern tut
- nicht nur zeigen: Endpoint ruft Service auf
- sondern auch: Service liest/schreibt DB, prueft Permissions, queued Worker usw.

Aktuelle Action-Arten:

- `database_action`
- `database_transaction`
- `permission_action`
- `worker_action`
- `external_action`
- `audit_action`
- `entity_declaration`
- `type_usage`

```mermaid
flowchart LR
  A["Endpoint"] --> B["Service Operation"]
  B --> C["Database Action"]
  B --> D["Permission Action"]
  B --> E["Worker Action"]
  B --> F["External Call"]
```

## Query- und Model-Details

Database Actions enthalten inzwischen strukturierte Query-Informationen.

Nicht nur:

```text
execute: select IAMUser where IAMUser.id == user_id
```

Sondern auch:

- Query Variable
- voller Query-Ausdruck
- Operation, z.B. `select`
- Entities, z.B. `IAMUser`
- Filter
- Joins
- Ordering
- Limit
- Entity Details

Entity Details werden ueber konfigurierbare Model-Mappings erkannt:

```yaml
mapping:
  entities:
    paths:
      - models
      - app/models
    field_value_calls:
      - Column
      - mapped_column
      - relationship
```

Dadurch kann die UI bei Database Action Nodes ein Detail-Panel anzeigen:

- Query
- Filter
- Tabelle
- Model-Felder
- Source Location

## Worker Detection

Worker-Erkennung ist konfigurierbar, weil jedes Projekt Worker anders baut.

Utilis nutzt nicht nur klassische Queue-Calls wie `.delay()`, sondern auch:

- `enqueue_job(job_type=...)`
- `Job(job_type=...)`

Die aktuelle Config erkennt:

- direkte Worker Dispatch Calls
- Job Model Constructor Calls
- klassische Queue Method Suffixes

```mermaid
flowchart LR
  A["Service Operation"] --> B["Job(job_type='send_notification')"]
  B --> C["worker_action"]
  C --> D["Worker Handler<br/>send_notification"]
```

Damit werden z.B. Worker-Actions sichtbar in:

- `NotificationService`
- `UnifiedCampaignService`
- `SessionManagementService`
- Privacy Request Fulfillment

## SQLite Read Model

SQLite ist die mittlere Schicht zwischen generated JSON und interaktiver UI.

```mermaid
flowchart LR
  A["Generated JSON"] --> B["Generated Tables<br/>ersetzbar"]
  C["Review Overlay JSON"] <--> D["Review Tables<br/>persistent"]
  E["User Story Markdown"] --> F["User Story Tables<br/>manuelle Dokumentation"]

  B --> G["FastAPI Query Routes"]
  D --> G
  F --> G
  G --> H["Frontend"]
```

Generated Tabellen koennen ersetzt werden:

- `generated_services`
- `generated_operations`
- `generated_endpoints`
- `generated_links`
- `generated_actions`
- `generated_validation_issues`

Review Tabellen bleiben erhalten:

- `review_items`
- `review_labels`
- `review_status_markers`

Manuelle User Story Daten:

- `user_stories`

Der Vorteil:

> Ein neuer Archdoc-Lauf kann generated Daten ersetzen, ohne menschliche Reviews
> zu zerstoeren.

## Overlay Layer

Das Overlay speichert menschliche Review-Daten getrennt von generated Daten.

Overlay kann enthalten:

- Review Status
- Labels
- Status Marker
- Owner
- Notes
- manuelle Links
- Overrides

Moegliche Target Types:

- `service`
- `operation`
- `endpoint`
- `endpoint_service_link`
- `architecture_action`
- `validation_issue`
- `user_story`
- spaeter `bpmn_process`, `bpmn_task`

## Frontend Views

Aktuelle Views:

- API Endpoint Catalog
- Endpoint-Service Interfaces
- Service Operations
- Service Action Graph
- Validation Issues
- User Stories

### Service Action Graph

Der Service Graph ist eine service-zentrierte Architekturansicht.

```mermaid
flowchart LR
  A["API Endpoint"] --> B["Service Operation"]
  C["Service Class"] --> B
  B --> D["Database Action"]
  B --> E["Permission Action"]
  B --> F["Worker Action"]
  B --> G["External / Audit / Type Usage"]
```

Database Action Nodes sind klickbar und zeigen:

- Source
- Query Expression
- Filter
- Model/Entity Details
- Felder und Tabellenname

### User Stories

Manuelle User Stories liegen in:

- `docs/architecture/user-stories/*.md`

Die Review-Ansicht verlinkt User Stories ueber Endpoint-Referenzen auf echte Backend-
Architektur.

```mermaid
flowchart LR
  A["User Story Markdown"] --> B["Endpoint Ref<br/>method + path"]
  B --> C["Generated Endpoint"]
  C --> D["Endpoint-Service Link"]
  D --> E["Service Operation"]
  E --> F["Architecture Actions"]
```

Beispiel:

- `US-ADMIN-001`
- Endpoint: `POST /users/{user_id}/reset-password`
- Service: `admin.admin-user`
- Operation: `reset_password`

## Was bereits funktioniert

Aktuell vorhanden:

- Source Code Scan
- Service Detection
- Endpoint Detection
- Endpoint-Service Linking
- Validation Issues
- SQLite Import
- Review Overlay
- serverseitige Tabellen
- Service Action Graph
- DB Query Details
- Model/Entity Details
- Worker Action Detection
- User Story Review und Trace View

## Moegliche Erweiterungen

### 1. Service-to-Service Verbindungen

High-confidence Service-zu-Service-Aufrufe und geerbte Facade-Operationen
werden bereits als Operation-Dependency-Links erzeugt, in SQLite importiert und
im Service-Graph-Inspector dargestellt. Dynamische oder indirekte Aufrufmuster
bleiben eine heuristische Grenze und sollten ueber Validation und Review
kontrolliert werden. Ein solcher erkannter Ablauf kann beispielsweise so
dargestellt werden:

```mermaid
flowchart LR
  A["Endpoint"] --> B["ParticipantService.create"]
  B --> C["AuditService.log"]
  B --> D["NotificationService.send"]
  D --> E["Worker Action"]
```

### 2. Full BPMN

BPMN ist noch nicht als vollwertige Architektur-Schicht integriert.

Noch fehlt:

- BPMN Prozessschema
- BPMN Task Schema
- Links von BPMN Tasks zu User Stories
- Links von BPMN Tasks zu Endpoints/Services
- BPMN Editor oder Viewer
- Validierung: Task ohne technische Umsetzung, Endpoint ohne Prozessbezug usw.

Zielbild:

```mermaid
flowchart LR
  A["BPMN Process"] --> B["BPMN Task"]
  B --> C["User Story"]
  C --> D["Endpoint"]
  D --> E["Service Operation"]
```

### 3. Full User Stories

Die User-Story-Ansicht ist aktuell ein Read-Model-Ansatz.

Noch fehlt:

- formales User Story JSON Schema
- Validator fuer Story-Qualitaet
- Parsing von Ablauf, Akzeptanzkriterien, Fehlerfaellen
- Status-/Review-Workflow fuer Stories
- Links zu Frontend Actions
- Links zu BPMN
- Coverage: welche Endpoints haben keine Story?
- Coverage: welche Stories haben keinen Endpoint?

Zielbild:

```mermaid
flowchart LR
  A["Frontend Action"] --> B["User Story Step"]
  B --> C["User Story"]
  C --> D["Endpoint"]
  D --> E["Service"]
  E --> F["DB / Worker / Permission"]
```

### 4. Frontend Action Capture

Aktuell werden Frontend Button Actions noch manuell dokumentiert.

Noch fehlt:

- Schema fuer Frontend Actions
- Import aus Markdown oder JSON
- spaeter eventuell automatisierte Extraktion aus Frontend-Code
- Verbindung Button/Route/Page zu User Story Step
- Verbindung User Story Step zu API Call

### 5. Staerkere Validator-Regeln

Sinnvolle weitere Regeln:

- User Story Endpoint existiert nicht
- Endpoint hat keine User Story
- BPMN Task hat keine technische Umsetzung
- Service-to-Service Call nicht modelliert
- Worker Job Type hat keinen Handler
- Permission Action fehlt fuer kritischen Endpoint
- doppelte Service-/Model-Namen als Review-Signal
