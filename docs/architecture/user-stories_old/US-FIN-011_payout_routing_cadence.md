---
id: US-FIN-011
title: Payout-Routing und Cadence konfigurieren
area: finance
status: draft
priority: high
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
  - system_config
---

# US-FIN-011 – Payout-Routing und Cadence konfigurieren

## User Story

Als **Finance Admin** möchte ich festlegen, wann und wie Auszahlungen ausgelöst und verarbeitet werden,
damit der Auszahlungsrhythmus den internen KD2Lab-Prozessen und den Erwartungen der Participants entspricht.

## Kontext

Der Abschnitt "Payout routing and cadence" steuert drei zentrale Dimensionen: den Trigger (wann eine Auszahlung entsteht), den Processing Mode (wie sie ausgeführt wird) und Timing-Parameter. Diese Einstellungen haben direkte Auswirkungen auf alle offenen Payouts – bei einer Änderung werden laufende Payout-Präferenzen und Schedules automatisch neu abgeglichen (`_reconcile_payment_settings_changes`).

## Vorbedingungen

- [ ] Benutzer ist eingeloggt mit Rolle `finance_admin` oder `admin`
- [ ] Finance → Payment Settings ist geöffnet
- [ ] Abschnitt "Payout routing and cadence" ist aufgeklappt

## Ablauf
Navbar: Payout Settings
1. Benutzer wählt **Payout trigger** aus Dropdown:
   - `per_study`: Pro abgeschlossener Studie entsteht eine Auszahlungserwartung
   - `per_threshold`: Kompensation akkumuliert sich bis zum Threshold-Betrag
   - `per_month`: Monatliche Auszahlung (erfordert `payout_day_of_month`)
2. Bei Trigger `per_threshold`: Benutzer setzt **Threshold amount (EUR)** (Pflicht, muss > 0)
3. Bei Trigger `per_month`: Benutzer setzt **Payout day of month** (Pflicht, 1–28)
4. Benutzer wählt **Payout processing mode** aus Dropdown:
   - `manual`: Staff prüft und bezahlt einzeln
   - `batch`: Automatische Stapelverarbeitung (erfordert `batch_day_of_week`)
   - `institution_backoffice`: Institutionelle Abteilung übernimmt
   - `external_provider`: Externer Anbieter
5. Bei Modus `batch`: Benutzer setzt **Batch day of week** (0 = Montag … 6 = Sonntag)
6. Benutzer setzt **Minimum payout (EUR)** (Standard: 5,00 €, muss >= 0)
7. Benutzer setzt **Default payout after approval (days)** (Standard: 7, muss >= 1)
8. Benutzer setzt **Auto-create payments after completion (days)** (Standard: 0, muss >= 0)
9. Benutzer klickt **Save Changes** → System normalisiert, validiert, speichert und reconciliert offene Payouts

## Akzeptanzkriterien

- [ ] Alle drei Trigger-Optionen (`per_study`, `per_threshold`, `per_month`) sind wählbar
- [ ] Feld `Threshold amount` erscheint nur bei Trigger `per_threshold` und ist Pflicht (> 0)
- [ ] Feld `Payout day of month` erscheint nur bei Trigger `per_month` und ist Pflicht (1–28)
- [ ] Feld `Batch day of week` erscheint nur bei Modus `batch`
- [ ] `Default payout after approval (days)` akzeptiert keine Werte < 1
- [ ] `Auto-create payments after completion (days)` akzeptiert keine negativen Werte
- [ ] Nach Save: Operating Summary reflektiert den neuen Trigger und Modus
- [ ] Nach Save: `Last Updated`-Timestamp wird gesetzt
- [ ] Ungültige Werte erzeugen verständliche Validierungsfehler inline

## Fehlerfälle

| Fall | Erwartetes Verhalten |
|---|---|
| Trigger `per_threshold`, Threshold leer oder 0 | Validierungsfehler: "Threshold payout amount must be > 0" |
| Trigger `per_month`, Tag außerhalb 1–28 | Validierungsfehler: "Monthly payout day must be between 1 and 28" |
| `Default payout after approval` < 1 | Validierungsfehler: "Default payout days must be >= 1" |
| `Auto-create after days` < 0 | Validierungsfehler: "Auto-create after days must be >= 0" |
| Modus `batch`, `batch_day_of_week` außerhalb 0–6 | Validierungsfehler: "Batch day of week must be between 0 and 6" |
| Keine Berechtigung | ForbiddenError: Seite nicht editierbar |
| Serverfehler beim Save | Fehlermeldung; Formular bleibt gefüllt |

## Beteiligte API-Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| GET | /admin/settings/payments | Lädt aktuelle Konfiguration inkl. timing_config |
| PUT | /admin/settings/payments | Speichert aktualisierte timing_config |

## Offene Fragen

- Welche Processing Modes sind in der UI tatsächlich selektierbar – alle 4 oder nur `manual` und `institution_backoffice`?
- Wird `batch_day_of_week` als 0=Montag oder 0=Sonntag interpretiert?
- Gibt es eine Warnung, wenn offene Payouts durch die Änderung betroffen sind?

## Notizen

- Bei Save löst das Backend automatisch `_reconcile_payment_settings_changes` aus – alle offenen Payouts werden mit den neuen Einstellungen neu abgeglichen
- `express_payout_enabled` und `express_payout_days` sind im Service vorhanden, aber in der UI nicht sichtbar – ggf. hidden feature
