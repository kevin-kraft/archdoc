---
id: US-ADMIN-001
title: Reset user password
area: admin
status: draft
owner: Architecture Demo
endpoints:
  - method: POST
    path: /users/{user_id}/reset-password
    purpose: Triggers a password reset for an existing user.
roles:
  - admin
---

# US-ADMIN-001 - Reset user password

## User Story

Als **Admin** möchte ich **das Passwort eines Users zurücksetzten**,
damit **ein gesperrter oder verlorener Zugang wiederhergestellt werden kann**.

## Kontext

Diese Story verbindet eine manuell erfasste Nutzeraktion mit dem generierten
Backend-Katalog. Die Demo zeigt, welcher Router, Service und welche Actions an
dem angegebenen Endpoint haengen.

## Vorbedingungen

- [ ] Benutzer ist eingeloggt
- [ ] Benutzer hat Admin-Rechte
- [ ] Ziel-User existiert

## Ablauf

1. Admin öffnet die User-Verwaltung.
2. Admin wählt einen User aus.
3. Admin klickt Passwort zurücksetzten.
4. System prueft Berechtigungen.
5. System führt den Reset aus und zeigt das Ergebnis.

## Akzeptanzkriterien

- [ ] Der Endpoint ist mit der User Story verknuepft
- [ ] Die Service-Operation ist sichtbar
- [ ] Database Actions und Permissions sind nachvollziehbar
- [ ] Fehlerfall fuer fehlende Berechtigung ist erkennbar

## Beteiligte API-Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| POST | /users/{user_id}/reset-password | Passwort-Reset fuer User |

## Offene Fragen

- Welche konkrete Frontend-Button-ID soll später auf diese Story zeigen?
