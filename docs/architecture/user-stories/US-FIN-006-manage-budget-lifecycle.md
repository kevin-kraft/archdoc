---
id: US-FIN-006
title: Budget bearbeiten, zuweisen und löschen
area: finance
status: draft
priority: medium
owner: KD2Lab Team
endpoints:
  - method: PUT
    path: /financial/budgets/{budget_id}
  - method: DELETE
    path: /financial/budgets/{budget_id}
  - method: GET
    path: /financial/budget-allocations
  - method: POST
    path: /financial/budget-allocations
  - method: PUT
    path: /financial/budget-allocations/{allocation_id}
  - method: DELETE
    path: /financial/budget-allocations/{allocation_id}
roles:
  - finance_admin
  - admin
tables:
  - budgets
  - budget_allocations
---

# US-FIN-006 - Budget bearbeiten, zuweisen und löschen

## User Story

Als **Finance Admin** möchte ich bestehende Budgets bearbeiten, nachträglich Experimenten zuweisen und bei Bedarf löschen, damit Budgetverantwortung und verfügbare Mittel aktuell bleiben.

## Kontext

Budget-Karten zeigen Rollen-/Permission-abhängige Aktionen: Bearbeiten, Zuweisen und Löschen. Im Allocation-Modus sind Stammdaten gesperrt und nur Zuweisungen relevant.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Budget existiert
- [ ] Für Bearbeiten: `payments:budget:edit`
- [ ] Für Zuweisen: `payments:budget:edit` oder `payments:budget:view:my`
- [ ] Für Löschen: `payments:budget:delete`

## Ablauf

1. Benutzer öffnet `/financial-management?tab=budgets`.
2. Benutzer wählt auf einer Budget-Karte **Bearbeiten**, **Zuweisen** oder **Löschen**.
3. Bei Bearbeiten: Benutzer aktualisiert Budget-Stammdaten und speichert.
4. Bei Zuweisen: Benutzer wählt Experiment und Allocation-Betrag und speichert.
5. Bei Löschen: Benutzer bestätigt die Löschung im Dialog.
6. System aktualisiert Budgetliste und Operational Summaries.

## Akzeptanzkriterien

- [ ] Aktionen werden nur angezeigt, wenn die passende Permission vorhanden ist.
- [ ] View-only-Benutzer sehen einen View-only-Hinweis statt Aktionsbuttons.
- [ ] Bearbeiten übernimmt bestehende Budgetwerte in den Dialog.
- [ ] Allocation-Modus lädt bestehende Allocations.
- [ ] Allocation Update/Delete aktualisiert die Summaries.
- [ ] Löschen entfernt die Budget-Karte nach Erfolg aus der Liste.

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Allocation-Betrag fehlt oder <= 0 | Validierungsfehler |
| Delete durch Backend blockiert | Fehlermeldung; Budget bleibt sichtbar |
| Allocation Summary nicht verfügbar | Summary zeigt `unavailable`, Aktionen bleiben möglich |
| Benutzer hat keine Permission | Aktion nicht sichtbar |

## Offene Fragen

- Darf ein Budget gelöscht werden, wenn bereits bezahlte Payouts dagegen gebucht wurden?
- Soll Allocation-Summe hart gegen Budget-Remaining validiert werden oder nur warnen?
