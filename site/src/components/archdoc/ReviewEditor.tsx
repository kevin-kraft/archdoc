import React, {useMemo, useState} from 'react';
import {
  overlayFromItem,
  type OverlayTargetType,
  type OverlayUpdate,
  type ReviewStatus,
} from './archdocApi';

type Props = {
  item: any;
  targetType: OverlayTargetType;
  targetId: string;
  editable: boolean;
  onSave: (targetType: OverlayTargetType, targetId: string, payload: OverlayUpdate) => Promise<void>;
};

const reviewStatuses: ReviewStatus[] = [
  'generated',
  'needs_review',
  'reviewed',
  'accepted',
  'needs_refactor',
  'false_positive',
  'deprecated',
];

const labelPresets = [
  'tenant-scoped',
  'public-contract',
  'needs-tests',
  'security-review',
  'bpmn-linked',
  'user-story-linked',
];

export default function ReviewEditor({item, targetType, targetId, editable, onSave}: Props) {
  const initial = useMemo(() => overlayFromItem(item), [item]);
  const [draft, setDraft] = useState<OverlayUpdate>(initial);
  const [labelsText, setLabelsText] = useState(initial.labels.join(', '));
  const [markersText, setMarkersText] = useState(initial.status_markers.join(', '));
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const status = draft.review_status ?? item?.review_status ?? 'generated';

  async function save() {
    setSaving(true);
    setError(null);

    try {
      await onSave(targetType, targetId, {
        ...draft,
        labels: splitList(labelsText),
        status_markers: splitList(markersText),
      });
      setOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  }

  function toggleLabel(label: string) {
    const labels = splitList(labelsText);
    const next = labels.includes(label)
      ? labels.filter((item) => item !== label)
      : [...labels, label];

    setLabelsText(next.join(', '));
  }

  return (
    <div className="archdocReviewEditor">
      <button
        type="button"
        className={`archdocReviewBadge archdocReviewBadge--${status}`}
        onClick={() => setOpen((value) => !value)}
      >
        {status}
      </button>

      {open && (
        <div className="archdocReviewPanel">
          <label>
            Status
            <select
              value={status}
              disabled={!editable || saving}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  review_status: event.target.value as ReviewStatus,
                }))
              }
            >
              {reviewStatuses.map((reviewStatus) => (
                <option key={reviewStatus} value={reviewStatus}>
                  {reviewStatus}
                </option>
              ))}
            </select>
          </label>

          <label>
            Owner
            <input
              value={draft.owner ?? ''}
              disabled={!editable || saving}
              onChange={(event) =>
                setDraft((current) => ({...current, owner: event.target.value}))
              }
            />
          </label>

          <label>
            Labels
            <input
              value={labelsText}
              disabled={!editable || saving}
              onChange={(event) => setLabelsText(event.target.value)}
            />
          </label>

          <div className="archdocLabelPresetGrid" aria-label="Label presets">
            {labelPresets.map((label) => {
              const active = splitList(labelsText).includes(label);

              return (
                <button
                  type="button"
                  key={label}
                  disabled={!editable || saving}
                  className={active ? 'archdocLabelPreset archdocLabelPreset--active' : 'archdocLabelPreset'}
                  onClick={() => toggleLabel(label)}
                >
                  {label}
                </button>
              );
            })}
          </div>

          <label>
            Markers
            <input
              value={markersText}
              disabled={!editable || saving}
              onChange={(event) => setMarkersText(event.target.value)}
            />
          </label>

          <label>
            Notes
            <textarea
              rows={3}
              value={draft.notes ?? ''}
              disabled={!editable || saving}
              onChange={(event) =>
                setDraft((current) => ({...current, notes: event.target.value}))
              }
            />
          </label>

          {!editable && (
            <p className="archdocReviewHint">Start the FastAPI backend to edit overlays.</p>
          )}

          {error && <p className="archdocReviewError">{error}</p>}

          <div className="archdocReviewActions">
            <button type="button" onClick={() => setOpen(false)}>
              Close
            </button>
            <button type="button" disabled={!editable || saving} onClick={save}>
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function splitList(value: string) {
  return value
    .split(',')
    .map((part) => part.trim())
    .filter(Boolean);
}
