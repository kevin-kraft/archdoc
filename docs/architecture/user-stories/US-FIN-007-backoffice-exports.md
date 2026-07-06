---
id: US-FIN-007
title: Backoffice-Exporte erzeugen und als bezahlt bestätigen
area: finance
status: draft
priority: high
owner: KD2Lab Team
endpoints:
  - method: GET
    path: /financial/backoffice-exports
  - method: GET
    path: /financial/backoffice-exports/candidates
  - method: POST
    path: /financial/backoffice-exports
  - method: GET
    path: /financial/backoffice-exports/{export_id}/download
  - method: GET
    path: /financial/backoffice-exports/{export_id}/file
  - method: POST
    path: /financial/backoffice-exports/{export_id}/confirm-paid
roles:
  - finance_admin
  - admin
  - finance_operator
tables:
  - backoffice_exports
  - payouts
---

# US-FIN-007 - Backoffice-Exporte erzeugen und als bezahlt bestätigen

## User Story

Als **Payout Operator** möchte ich im Tab **Exports** auszahlungsfähige Payouts als Backoffice-Datei exportieren und nach externer Zahlung als bezahlt bestätigen, damit Zahlungen außerhalb der Plattform sauber nachverfolgt werden.

## Kontext

`exports` gehört zur Gruppe **Evidence and audit**. Der Tab ist für Settlement-Fälle gedacht, bei denen die Auszahlung nicht direkt über einen Provider in der Plattform abgeschlossen wird.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat Rechte zur Auszahlungsbearbeitung
- [ ] Es gibt eligible Export Candidates

## Ablauf

1. Benutzer öffnet `/financial-management?tab=exports`.
2. System lädt Export Candidates und bisherigen Export-Verlauf.
3. Benutzer wählt eligible Payouts mit gemeinsamer Währung und Route.
4. Benutzer wählt Exportformat, z. B. CSV, PDF oder DATEV.
5. System erzeugt Backoffice-Export.
6. Benutzer lädt Datei herunter.
7. Nach externer Zahlung bestätigt Benutzer den Export als bezahlt.
8. System markiert alle Payouts im Export als extern bezahlt.

## Akzeptanzkriterien

- [ ] Nicht eligible Payouts zeigen einen Grund und können nicht exportiert werden.
- [ ] Ausgewählte Payouts müssen Währung und Auszahlungsroute gemeinsam haben.
- [ ] Export-Historie zeigt Format, Item Count, Total Amount, Status und Zeitpunkte.
- [ ] Download ist für erzeugte Exporte verfügbar.
- [ ] **Als bezahlt bestätigen** verlangt eine explizite Bestätigung, weil die Aktion nicht rückgängig gemacht wird.
- [ ] Nach Bestätigung werden die betroffenen Payouts und Finance Queues aktualisiert.

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Auswahl enthält unterschiedliche Währungen/Routen | Validierungsfehler |
| Export-Erzeugung schlägt fehl | Fehlermeldung, kein History-Eintrag vortäuschen |
| Download schlägt fehl | Fehlermeldung |
| Confirm-paid schlägt fehl | Export bleibt unbestätigt |

## Offene Fragen

- Welche Exportformate sind produktiv verbindlich und welche nur MVP?
- Soll Confirm-paid zusätzlich einen Zahlungsnachweis/Kommentar verlangen?
