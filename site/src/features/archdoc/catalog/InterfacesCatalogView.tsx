import React, {useMemo, useState} from 'react';
import DataTable, {type DataTableColumn, type DataTableFilter} from '../components/DataTable';
import ReviewEditor from '../components/ReviewEditor';
import {
  CatalogToolbar,
  ConfidenceBadge,
  MethodBadge,
  PrimarySecondary,
  SourceRef,
} from '../components/TablePrimitives';
import {fetchInterfaceRows} from '../api/archdocApi';
import {useArchdocTableContext} from '../api/useArchdocTableContext';
import {reviewStatusOptions} from '../constants/reviewStatusOptions';

type InterfaceRow = {
  link: any;
  endpoint?: any;
};

type InterfaceSortColumn = 'endpoint' | 'service' | 'confidence' | 'source' | 'review';

export default function InterfacesCatalogView() {
  const {source, editable, error, saveOverlay} = useArchdocTableContext();
  const [query, setQuery] = useState(() => initialSearchParam());
  const [confidenceFilter, setConfidenceFilter] = useState('all');
  const [reviewStatusFilter, setReviewStatusFilter] = useState('all');

  const columns = useMemo<DataTableColumn<InterfaceRow, InterfaceSortColumn>[]>(() => [
    {
      key: 'endpoint',
      label: 'Endpoint',
      sortable: true,
      value: ({link, endpoint}) => `${endpoint?.full_path ?? endpoint?.path ?? link.endpoint_id ?? ''} ${endpoint?.function_name ?? ''}`,
      render: ({link, endpoint}) => endpoint ? (
        <PrimarySecondary
          primary={
            <>
              <MethodBadge method={endpoint.http_method} />{' '}
              <code className="archdocPathCode">{endpoint.full_path ?? endpoint.path}</code>
            </>
          }
          secondary={<span>{endpoint.function_name}</span>}
        />
      ) : (
        <code>{link.endpoint_id}</code>
      ),
    },
    {
      key: 'service',
      label: 'Service Operation',
      sortable: true,
      value: ({link}) => `${link.service_id ?? ''} ${link.operation_method ?? ''}`,
      render: ({link}) => (
        <PrimarySecondary
          primary={<code>{link.service_id}</code>}
          secondary={<span>{link.operation_method}</span>}
        />
      ),
    },
    {
      key: 'confidence',
      label: 'Detection',
      sortable: true,
      value: ({link}) => link.detection?.confidence,
      render: ({link}) => (
        <PrimarySecondary
          primary={<ConfidenceBadge value={link.detection?.confidence} />}
          secondary={<span>{link.detection?.rule ?? 'rule-based'}</span>}
        />
      ),
    },
    {
      key: 'review',
      label: 'Review',
      value: ({link}) => link.review_status,
      render: ({link}) => (
        <ReviewEditor
          item={link}
          targetType="endpoint_service_link"
          targetId={linkTargetId(link)}
          editable={editable}
          onSave={saveOverlay}
        />
      ),
    },
    {
      key: 'source',
      label: 'Source',
      sortable: true,
      value: ({link}) => `${link.source?.file ?? ''}:${link.source?.line_start ?? ''}`,
      render: ({link}) => <SourceRef file={link.source?.file} line={link.source?.line_start} />,
    },
  ], [editable, saveOverlay]);

  const filters = useMemo<DataTableFilter<InterfaceRow>[]>(() => [
    {
      key: 'confidence',
      label: 'Confidence',
      value: confidenceFilter,
      onChange: setConfidenceFilter,
      options: [
        {label: 'All confidence', value: 'all'},
        {label: 'Exact', value: 'exact'},
        {label: 'High', value: 'high'},
        {label: 'Medium', value: 'medium'},
        {label: 'Low', value: 'low'},
        {label: 'Unknown', value: 'unknown'},
      ],
      predicate: ({link}, value) => value === 'all' || (link.detection?.confidence ?? 'unknown') === value,
    },
    {
      key: 'review_status',
      label: 'Review',
      value: reviewStatusFilter,
      onChange: setReviewStatusFilter,
      options: reviewStatusOptions,
      predicate: ({link}, value) => value === 'all' || link.review_status === value,
    },
  ], [confidenceFilter, reviewStatusFilter]);

  if (error) return <p><strong>Error:</strong> {error}</p>;

  return (
    <div className="endpointTableWrapper">
      <CatalogToolbar
        title="Endpoint-Service Interfaces"
        subtitle="Resolved calls between API routes and service operations with detection confidence."
        query={query}
        placeholder="Search endpoint, path, service, operation..."
        source={source}
        editable={editable}
        resultCount={0}
        totalCount={0}
        showControls={false}
        onQueryChange={setQuery}
      />

      <DataTable
        columns={columns}
        rowKey={({link}, index) => `${linkTargetId(link)}|${index}`}
        search={query}
        searchPlaceholder="Search interfaces..."
        defaultSort={{column: 'endpoint', direction: 'asc'}}
        filters={filters}
        fetchData={fetchInterfaceRows}
        onSearchChange={setQuery}
      />
    </div>
  );
}

function initialSearchParam() {
  if (typeof window === 'undefined') return '';

  return new URLSearchParams(window.location.search).get('search') ?? '';
}

function linkTargetId(link: any) {
  return [
    link.endpoint_id ?? '',
    link.operation_id ?? '',
    link.source?.line_start ?? '',
  ].join('|');
}
