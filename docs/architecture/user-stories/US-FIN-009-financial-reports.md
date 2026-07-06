---
id: US-FIN-009
title: Finanzberichte anzeigen
area: finance
status: draft
priority: medium
owner: KD2Lab Team
endpoints:
  - method: POST
    path: /financial/reports/financial-stats
roles:
  - finance_admin
  - admin
tables:
  - budgets
  - payouts
  - budget_allocations
---

# US-FIN-009 - Finanzberichte anzeigen

## User Story

Als **Finance Admin** möchte ich im Tab **Reports** aggregierte Finanzberichte sehen, damit ich Budgetauslastung, Experimentkosten und Teilnehmerzahlungen bewerten kann.

## Kontext

`reports` gehört zur Gruppe **Management insight**. Es ist nicht der Arbeitsbereich für einzelne Zahlungen, sondern für aggregierte Auswertung.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat Zugriff auf Finanzberichte
- [ ] Finanzstatistiken konnten geladen werden

## Ablauf

1. Benutzer öffnet `/financial-management?tab=reports`.
2. System lädt Financial Stats und Basiswährung.
3. System zeigt Budget Summary, Experiment Costs und Participant Payouts.
4. Benutzer prüft Aggregate und Trends als Management-Übersicht.

## Akzeptanzkriterien

- [ ] Reports zeigen Total Budgets, Budget Authority, Allocated und Remaining.
- [ ] Experimentkosten zeigen Experimente, Gesamtkosten, Allocations und Committed.
- [ ] Teilnehmerzahlungen zeigen Auszahlungshistorie und Statistiken.
- [ ] Mixed-Currency-Warnung erscheint, wenn Aggregate mehrere Währungen umfassen.
- [ ] Leere Daten führen zu Empty-State statt kaputten Charts/Tabellen.

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Financial Stats laden nicht | Load-Error mit Retry auf Finanzseite |
| Mixed Currency | Warnung vor Nutzung der Aggregate |
| Keine Daten vorhanden | Empty-State mit Hinweis auf fehlende Finanzdaten |

## Offene Fragen

- Welche Report-Kennzahlen sind für die Pilotphase wirklich entscheidungsrelevant?
- Soll Reports exportierbar sein oder reicht Anzeige im MVP?
