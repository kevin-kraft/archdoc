import React from 'react';
import {FaCircleCheck, FaTriangleExclamation} from 'react-icons/fa6';

type ToolbarProps = {
  title: string;
  subtitle: string;
  query: string;
  placeholder: string;
  source: string;
  editable: boolean;
  resultCount: number;
  totalCount: number;
  showControls?: boolean;
  onQueryChange: (value: string) => void;
};

export type SortDirection = 'asc' | 'desc';

export type SortState<TColumn extends string> = {
  column: TColumn;
  direction: SortDirection;
};

export function CatalogToolbar({
  title,
  subtitle,
  query,
  placeholder,
  source,
  editable,
  resultCount,
  totalCount,
  showControls = true,
  onQueryChange,
}: ToolbarProps) {
  return (
    <div className="archdocToolbar">
      <div className="archdocToolbarMain">
        <div>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </div>
        <div className="archdocToolbarBadges">
          <span className="archdocMetaBadge">
            {source === 'backend' ? 'Effective catalog' : 'Static JSON'}
          </span>
          <span className={editable ? 'archdocMetaBadge archdocMetaBadge--editable' : 'archdocMetaBadge'}>
            {editable ? 'Overlay API active' : 'Overlay editing unavailable'}
          </span>
        </div>
      </div>

      {showControls ? (
        <div className="archdocToolbarControls">
          <input
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder={placeholder}
            className="endpointTableSearch"
          />
          <span className="archdocResultCount">
            {resultCount} / {totalCount}
          </span>
        </div>
      ) : null}
    </div>
  );
}

export function SortHeader<TColumn extends string>({
  column,
  label,
  sort,
  onSort,
}: {
  column: TColumn;
  label: string;
  sort: SortState<TColumn>;
  onSort: (column: TColumn) => void;
}) {
  const active = sort.column === column;
  const marker = active ? (sort.direction === 'asc' ? 'up' : 'down') : '';

  return (
    <button
      type="button"
      className={active ? 'archdocSortHeader archdocSortHeader--active' : 'archdocSortHeader'}
      onClick={() => onSort(column)}
      title={`Sort by ${label}`}
    >
      <span>{label}</span>
      <span aria-hidden="true">{marker}</span>
    </button>
  );
}

export function nextSort<TColumn extends string>(
  current: SortState<TColumn>,
  column: TColumn,
): SortState<TColumn> {
  if (current.column !== column) {
    return {column, direction: 'asc'};
  }

  return {
    column,
    direction: current.direction === 'asc' ? 'desc' : 'asc',
  };
}

export function compareText(a: unknown, b: unknown) {
  return String(a ?? '').localeCompare(String(b ?? ''), undefined, {
    numeric: true,
    sensitivity: 'base',
  });
}

export function MethodBadge({method}: {method?: string}) {
  const value = method ?? 'UNKNOWN';

  return <span className={`archdocMethodBadge archdocMethodBadge--${value.toLowerCase()}`}>{value}</span>;
}

export function LinkStateIcon({linked}: {linked: boolean}) {
  return linked ? (
    <span className="archdocLinkState archdocLinkState--linked">
      <FaCircleCheck /> linked
    </span>
  ) : (
    <span className="archdocLinkState archdocLinkState--unlinked">
      <FaTriangleExclamation /> open
    </span>
  );
}

export function ConfidenceBadge({value}: {value?: string}) {
  return <span className={`archdocConfidenceBadge archdocConfidenceBadge--${value ?? 'unknown'}`}>{value ?? 'unknown'}</span>;
}

export function SeverityBadge({severity}: {severity: string}) {
  return <span className={`archdocSeverityBadge archdocSeverityBadge--${severity}`}>{severity}</span>;
}

export function SourceRef({file, line}: {file?: string; line?: number}) {
  if (!file) return <span className="archdocMuted">-</span>;

  return (
    <span className="archdocSourceRef">
      <span>{file}</span>
      {line ? <strong>{line}</strong> : null}
    </span>
  );
}

export function PrimarySecondary({
  primary,
  secondary,
}: {
  primary: React.ReactNode;
  secondary?: React.ReactNode;
}) {
  return (
    <div className="archdocCellStack">
      <div className="archdocCellPrimary">{primary}</div>
      {secondary ? <div className="archdocCellSecondary">{secondary}</div> : null}
    </div>
  );
}
