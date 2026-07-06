---
id: US-FIN-014
title: Dispatch-Autorisierung konfigurieren
area: finance
status: draft
priority: critical
owner: KD2Lab Team
endpoints:
  - method: GET
    path: /settings/payments
  - method: PUT
    path: /settings/payments
roles:
  - finance_admin
  - admin
tables:
  - payment_settings
  - payouts
---

# US-FIN-014 – Dispatch-Autorisierung konfigurieren

## User Story

Als **Finance Admin** möchte ich die Dispatch-Autorisierung konfigurieren (Modus, Schwellenwert, Vier-Augen-Prinzip),
damit kein Geld die Plattform verlässt, ohne dass die korrekte Anzahl an Autorisierungen erteilt wurde.

## Kontext

Die Dispatch Authorization ist der letzte Kontrollschritt vor der tatsächlichen Geldüberweisung – unabhängig vom Compensation Approval. Das Backend bestimmt die Anzahl nötiger Dispatch-Approvals via `get_required_dispatch_approvals()` basierend auf Betrag, Modus und Provider-Config. Mit `require_separate_dispatch_approver: true` kann dieselbe Person nicht beide Sign-offs erteilen.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt mit Rolle `finance_admin` oder `admin`
- [ ] Abschnitt "Dispatch authorization" ist aufgeklappt

## Ablauf
Navbar: Payout Settings
1. Benutzer wählt **Dispatch authorization mode** (Dropdown):
   - `none`: Keine Dispatch-Autorisierung nötig
   - `single`: Ein Finance-User muss autorisieren (Standard)
   - `dual`: Zwei verschiedene Finance-User müssen autorisieren
2. Benutzer setzt optional **Require dispatch authorization over (EUR)** (leer = immer Autorisierung nötig, wenn Modus ≠ none)
3. Benutzer wählt **Default dispatch authorizer role** (z. B. `finance_admin`)
4. Benutzer aktiviert/deaktiviert **"Require separate second dispatch approver"**
   - Aktiviert: Dieselbe Person kann nicht beide Sign-offs geben (Vier-Augen)
5. Benutzer aktiviert/deaktiviert **"Notify on pending dispatch authorization"**
   - Sendet Alert wenn Payout genehmigt ist, aber Dispatch noch aussteht
6. Benutzer klickt **Save Changes**

## Akzeptanzkriterien

- [ ] Alle drei Modi (`none`, `single`, `dual`) sind wählbar
- [ ] `Require dispatch authorization over` kann leer bleiben (= immer Autorisierung nötig ab Modus ≠ none)
- [ ] `dispatch_approval_over` muss > 0 wenn gesetzt
- [ ] Bei Modus `dual` + `require_separate_dispatch_approver: true`: Backend blockiert zweiten Sign-off vom selben User
- [ ] Notify-Toggle korrekt gespeichert und nach Reload beibehalten
- [ ] Operating Summary zeigt aktuellen Dispatch Sign-off Modus
- [ ] Nach Save: `Last Updated`-Timestamp gesetzt

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| `dispatch_approval_over` gesetzt und <= 0 | Validierungsfehler: "Dispatch approval threshold must be greater than 0" |
| Modus `dual`, gleicher User versucht zweiten Sign-off | Backend blockiert; Fehlermeldung im UI |
| Default authorizer role leer | `null`-Fallback – prüfen ob Routing-Fehler entsteht |
| Keine Berechtigung | ForbiddenError |
| Serverfehler beim Save | Fehlermeldung; Formular bleibt gefüllt |

## Beteiligte API-Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| GET | /admin/settings/payments | Lädt dispatch_authorization aus approval_config |
| PUT | /admin/settings/payments | Speichert dispatch_authorization-Einstellungen |

## Offene Fragen

- Kann der Modus `none` produktiv sinnvoll genutzt werden, oder ist das nur für Testzwecke gedacht?
- Was passiert mit Payouts, die bereits auf Dispatch warten, wenn der Modus geändert wird?
- Ist `dispatch_default_authorizer_role` zwingend `finance_admin` oder frei konfigurierbar?

## Notizen

- Default: `dispatch_approval_mode: "single"`, `require_separate_dispatch_approver: true`, `notify_on_dispatch_pending: true`, `dispatch_approval_over: null`
- `payout_has_required_dispatch_authorizations()` prüft primären und dualen Authorizer auf dem Payout-Objekt
- Diese Story ergänzt US-FIN-004 (Compensation Approval) – beide Stufen sind unabhängig voneinander
