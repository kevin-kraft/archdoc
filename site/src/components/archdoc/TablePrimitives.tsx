import React from 'react';
import {FaArrowRight, FaCircleCheck, FaCodeBranch, FaTriangleExclamation} from 'react-icons/fa6';

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


type OperationRelationEndpoint = {
  operation_id?: string | null;
  service_id?: string | null;
  class_name?: string | null;
  method_name?: string | null;
};

export type OperationRelationLink = {
  id?: string;
  link_type?: string;
  source?: OperationRelationEndpoint | null;
  target?: OperationRelationEndpoint | null;
  call_name?: string;
  resolved?: boolean;
  details?: Record<string, unknown>;
};

function relationDirection(link: OperationRelationLink, operationId?: string): 'incoming' | 'outgoing' {
  return link.target?.operation_id === operationId ? 'incoming' : 'outgoing';
}

function relationCounterpart(link: OperationRelationLink, direction: 'incoming' | 'outgoing') {
  const endpoint = direction === 'incoming' ? link.source : link.target;
  return `${endpoint?.class_name ?? endpoint?.service_id ?? 'Service'}.${endpoint?.method_name ?? 'unknown'}`;
}

function relationDescription(link: OperationRelationLink, direction: 'incoming' | 'outgoing', counterpart: string) {
  if (link.link_type === 'inherited_operation') {
    return direction === 'outgoing'
      ? `Inherited operation: this facade-owned operation is implemented by ${counterpart}.`
      : `Inherited operation target: ${counterpart} exposes this implementation through a facade or inherited service.`;
  }

  if (link.link_type === 'service_call') {
    return direction === 'outgoing'
      ? `Service operation call to ${counterpart}.`
      : `Service operation call from ${counterpart}.`;
  }

  return `Operation relation ${link.link_type ?? 'unknown'} with ${counterpart}.`;
}

export function OperationRelationBadge({
  link,
  operationId,
  compact = false,
}: {
  link: OperationRelationLink;
  operationId?: string;
  compact?: boolean;
}) {
  const direction = relationDirection(link, operationId);
  const counterpart = relationCounterpart(link, direction);
  const inherited = link.link_type === 'inherited_operation';
  const label = inherited
    ? (direction === 'incoming' ? 'Inherited target' : 'Inherited')
    : (direction === 'incoming' ? 'Called by' : 'Calls');
  const title = relationDescription(link, direction, counterpart);
  const className = inherited
    ? 'archdocOperationRelationBadge archdocOperationRelationBadge--inherited'
    : 'archdocOperationRelationBadge archdocOperationRelationBadge--serviceCall';

  return (
    <span className={className} title={title} aria-label={title}>
      {inherited ? <FaCodeBranch aria-hidden="true" /> : <FaArrowRight aria-hidden="true" />}
      <span>{label}</span>
      {!compact ? <small>{counterpart}</small> : null}
    </span>
  );
}

export function OperationRelationSummary({
  links,
  operationId,
  max = 3,
}: {
  links?: OperationRelationLink[];
  operationId?: string;
  max?: number;
}) {
  const relationLinks = links ?? [];
  if (!relationLinks.length) {
    return <span className="archdocMuted">No operation relations</span>;
  }

  const visible = relationLinks.slice(0, max);
  const hidden = relationLinks.length - visible.length;

  return (
    <span className="archdocOperationRelationList">
      {visible.map((link, index) => (
        <OperationRelationBadge
          key={link.id ?? `${link.link_type ?? 'relation'}-${index}`}
          link={link}
          operationId={operationId}
          compact={relationLinks.length > 2}
        />
      ))}
      {hidden > 0 ? (
        <span className="archdocOperationRelationOverflow" title={`${hidden} additional operation relation(s)`}>
          +{hidden}
        </span>
      ) : null}
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
