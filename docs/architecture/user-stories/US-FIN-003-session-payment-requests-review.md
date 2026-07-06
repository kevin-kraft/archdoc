---
id: US-FIN-003
title: Session Payment Requests prüfen und genehmigen
area: finance
status: draft
priority: high
owner: KD2Lab Team
endpoints:
  - method: GET
    path: /financial/session-payment-requests
  - method: GET
    path: /financial/session-payment-requests/{request_id}
  - method: POST
    path: /financial/session-payment-requests/{request_id}/approve
  - method: POST
    path: /financial/session-payment-requests/{request_id}/return
  - method: POST
    path: /financial/session-payment-requests/{request_id}/items/{item_id}/approve
  - method: POST
    path: /financial/session-payment-requests/{request_id}/items/{item_id}/reject
roles:
  - finance_admin
  - admin
tables:
  - session_payment_requests
  - compensations
  - payouts
---

# US-FIN-003 - Session Payment Requests prüfen und genehmigen

## User Story

Als **Finance Admin** möchte ich eingereichte Session Payment Requests prüfen, genehmigen oder zur Korrektur zurückgeben, damit nur fachlich korrekte Teilnehmervergütungen in die Auszahlung übergehen.

## Kontext

Der aktuelle Standard-Einstieg der Finanzseite ist `payment-requests`. Payment Requests entstehen aus abgeschlossenen Session-Workflows und können per `sessionId`, `experimentId` oder `requestId` gefiltert werden.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat `payments:approve` oder `payments:approve:dual`
- [ ] Mindestens ein Session Payment Request wurde eingereicht

## Ablauf

1. Benutzer öffnet `/financial-management?tab=payment-requests`.
2. System lädt Payment Requests inklusive optionaler Items.
3. Benutzer prüft Session, Experiment, Teilnehmer, Attendance/Evidence, Beträge und Status.
4. Benutzer genehmigt den gesamten Request oder einzelne Items.
5. Benutzer kann fehlerhafte Requests zurückgeben oder einzelne Items ablehnen.
6. System aktualisiert Status und Finance Inbox.

## Akzeptanzkriterien

- [ ] Liste zeigt Session Payment Requests mit Status, Session-/Experiment-Kontext und Beträgen.
- [ ] Direkter Link mit `requestId` öffnet/fokussiert den betreffenden Request.
- [ ] `sessionId` und `experimentId` filtern die Ansicht kontextbezogen.
- [ ] Genehmigen ist nur für berechtigte Rollen verfügbar.
- [ ] Rückgabe oder Ablehnung verlangt eine fachliche Begründung.
- [ ] Nach erfolgreicher Aktion werden Payment Requests, Compensations und Payout-relevante Queues aktualisiert.

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Request existiert nicht | Detail-/Listenansicht zeigt Fehler oder leeren Zustand |
| Benutzer hat keine Approval-Rechte | Aktionsbuttons fehlen oder sind deaktiviert |
| Backend lehnt Genehmigung ab | Fehlermeldung bleibt sichtbar, Daten werden nicht optimistisch falsch übernommen |
| Request wurde parallel geändert | Aktualisierte Daten erneut laden |

## Offene Fragen

- Soll eine vollständige Request-Genehmigung automatisch alle noch offenen Items genehmigen oder nur eligible Items?
- Welche Evidence-Mindestanforderungen blockieren eine Genehmigung verbindlich?
