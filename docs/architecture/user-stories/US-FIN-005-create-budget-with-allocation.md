---
id: US-FIN-005
title: Budget mit initialer Experiment-Zuweisung erstellen
area: finance
status: draft
priority: high
owner: KD2Lab Team
endpoints:
  - method: GET
    path: /financial/budgets
  - method: POST
    path: /financial/budgets
  - method: POST
    path: /financial/budget-allocations
  - method: GET
    path: /financial/budget-operational-summaries
roles:
  - finance_admin
  - admin
tables:
  - budgets
  - budget_allocations
  - experiments
---

# US-FIN-005 - Budget mit initialer Experiment-Zuweisung erstellen

## User Story

Als **Finance Admin** möchte ich im Tab **Budgets** ein Budget inklusive initialer Experiment-Zuweisung erstellen, damit Auszahlungen gegen ein kontrolliertes Budget laufen können.

## Kontext

Das alte `US-FIN-016_create_budget.md` war kaputt, weil es Reset-to-Defaults-Abläufe kopiert hat. In der aktuellen UI ist Budget-Erstellung ein eigener Tab im Standard Workflow und verlangt beim Erstellen bereits eine Allocation zu einem Experiment.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat `payments:budget:add`
- [ ] Mindestens ein Experiment ist auffindbar

## Ablauf

1. Benutzer öffnet `/financial-management?tab=budgets`.
2. Benutzer klickt **Budget erstellen**.
3. System öffnet den Budget-Dialog.
4. Benutzer erfasst Name, Beschreibung, Owner, Gesamtbetrag, Startdatum, optional Enddatum und Aktivstatus.
5. Benutzer wählt ein Experiment und gibt einen initialen Allocation-Betrag an.
6. Benutzer speichert.
7. System erstellt Budget und Budget Allocation.
8. System aktualisiert Budgets, Operational Summaries und Experimente.

## Akzeptanzkriterien

- [ ] Button **Budget erstellen** ist nur mit `payments:budget:add` sichtbar.
- [ ] Gesamtbetrag muss > 0 sein.
- [ ] Startdatum ist Pflicht.
- [ ] Beim Neuanlegen sind Experiment und Allocation-Betrag Pflicht.
- [ ] Allocation-Betrag muss > 0 sein.
- [ ] Nach Erfolg schließt der Dialog, die Liste wird aktualisiert und eine Erfolgsmeldung erscheint.
- [ ] Budget-Karten zeigen Total, Remaining, Allocated, Spent, Reserved, Allocation Count und offene/bezahlte Payouts.

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Gesamtbetrag fehlt oder <= 0 | Validierungsfehler |
| Startdatum fehlt | Validierungsfehler |
| Experiment oder Allocation fehlt | Validierungsfehler |
| Operational Summary kann nicht geladen werden | Budget bleibt sichtbar, Summary zeigt unavailable |
| Backend lehnt Erstellung ab | Fehlermeldung mit Backend-Message |

## Offene Fragen

- Soll ein Budget wirklich immer initial einem Experiment zugewiesen werden müssen? Aktuell erzwingt die UI das beim Create; fachlich kann das für reine Rahmenbudgets zu hart sein.
