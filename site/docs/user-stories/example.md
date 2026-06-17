---
id: US-AREA-001 # US = User story, Area = Bereich bsp Finanz 
title: Kurzer Titel der User Story
area: participants
status: draft # draft | ready | in-progress | done | deprecated
owner: Name # Ersteller der User Story 
endpoints:
  - method: POST
    path: /api/example
# services: Braucht man vielleicht nicht direkt
#   - ExampleService.create
roles: # Rollen die bei der Aktion eine Rolle spielen 

---

# US-AREA-001 - Kurzer Titel

## User Story

Als **[Rolle]** möchte ich **[Aktion/Funktion]**,
damit **[Nutzen/Ziel]**.

Als admin / finance admin möchte ich ein budget erstellen. 

## Kontext

Kurze Erklärung, warum diese Funktion existiert.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat die nötigen Rechte
- [ ] Benötigte Daten existieren

## Ablauf

1. Benutzer öffnet ...
2. Benutzer klickt ...
3. System validiert ...
4. System speichert ...
5. System zeigt Ergebnis ...

## Akzeptanzkriterien

- [ ] Pflichtfelder werden validiert
- [ ] Erfolgsfall funktioniert
- [ ] Fehlerfall wird verständlich angezeigt
- [ ] Berechtigungen werden geprüft

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Pflichtfeld fehlt | Validierungsfehler anzeigen |
| Keine Berechtigung | Zugriff verweigern |
| Serverfehler | Fehlermeldung anzeigen |

## Beteiligte API-Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| POST | /api/example | Erstellt einen neuen Datensatz |

## Offene Fragen

- ...

## Notizen

- Aktion von finance admin und admin und super-admin möglich 