# A3: Configurable Worker Action Mapping

## Context

The initial architecture action mapper only detected common queue library calls
such as `.delay()`, `.apply_async()`, `.enqueue()`, and `.send_task()`. Utilis
uses a custom background worker model based on `Job(job_type=...)` rows and
`enqueue_job(...)`, so no worker actions were visible in the generated service
graph.

## Change

Added `mapping.workers` to the Archdoc configuration. It supports:

- direct worker dispatch calls, for example `enqueue_job(job_type=...)`
- job model constructors, for example `Job(job_type=...)`
- classic queue method suffixes
- optional known worker class and injected worker attribute names

The action mapper now emits `worker_action` items before generic action pattern
matching. Worker details include dispatch style, job type, payload expression,
schedule expression, priority, org expression, original args, and original
kwargs.

## Rationale

Worker usage differs heavily between projects. Making dispatch mechanisms
configurable keeps Archdoc universal while allowing Utilis-specific job-table
workers to be represented without hardcoding the Utilis worker implementation.

## Current Result

The generated catalog now detects 23 worker actions in Utilis. Examples include:

- `NotificationService` queueing `send_notification`,
  `send_scheduled_notification`, and `send_push_notification`
- `UnifiedCampaignService` queueing `send_email_campaign`
- `SessionManagementService` queueing `session_completion_financials`
- `AdvancedSessionManagementService` dispatching `send_session_reminder`
- privacy request fulfillment via `enqueue_job`

Dynamic job types remain represented as expressions such as `job_type` or
`job_data.job_type`.

## Verification

- `python -m py_compile` for changed config and mapper modules
- targeted static export using existing Archdoc mapper/exporter functions
- SQLite generated import with `force=True`
- `npm run typecheck`
