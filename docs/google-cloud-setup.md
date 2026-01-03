## Google Cloud Project

- Project name: life-admin-system
- Purpose: Gmail API ingestion for Life Admin System
- Created: <today’s date>

## Billing Safeguards

- Monthly budget: €5
- Alerts: 50%, 90%, 100%
- Scope: life-admin-system project only

## Enabled APIs

- Gmail API (read-only usage)

## OAuth Consent Screen

- User type: External
- Status: Testing
- Test users:
  - <intake gmail>
  - <your gmail>


## OAuth Client

- Type: Desktop application
- Name: life-admin-local-dev
- Credentials stored in secrets/google_oauth_client.json (gitignored)

## APIs Enabled

- Gmail API

## Gmail Intake – First Successful Run

- Project: life-admin-system
- Gmail API enabled
- OAuth completed (Testing mode)
- Test users configured
- Token stored locally
- Email ingested via LifeAdmin label
- Raw email archived as .eml in R2
- Content indexed and searchable
