import React, {useMemo, useState} from 'react';
import DataTable, {type DataTableColumn, type DataTableFilter} from '../components/DataTable';
import ReviewEditor from '../components/ReviewEditor';
import {
  CatalogToolbar,
  LinkStateIcon,
  MethodBadge,
  PrimarySecondary,
  SourceRef,
} from '../components/TablePrimitives';
import {fetchEndpointRows} from '../api/archdocApi';
import {useArchdocTableContext} from '../api/useArchdocTableContext';
import {reviewStatusOptions} from '../constants/reviewStatusOptions';

type EndpointSortColumn = 'method' | 'endpoint' | 'implementation' | 'contract' | 'linkage' | 'source' | 'review';

export default function EndpointCatalogView() {
  const {source, editable, error, saveOverlay} = useArchdocTableContext();
  const [query, setQuery] = useState(() => initialSearchParam());
  const [methodFilter, setMethodFilter] = useState('all');
  const [contractFilter, setContractFilter] = useState('all');
  const [linkageFilter, setLinkageFilter] = useState('all');
  const [reviewStatusFilter, setReviewStatusFilter] = useState('all');

  const columns = useMemo<DataTableColumn<any, EndpointSortColumn>[]>(() => [
    {
      key: 'method',
      label: 'Method',
      sortable: true,
      value: (endpoint) => endpoint.http_method,
      render: (endpoint) => <MethodBadge method={endpoint.http_method} />,
    },
    {
      key: 'endpoint',
      label: 'Endpoint',
      sortable: true,
      value: (endpoint) => `${endpoint.full_path ?? endpoint.path ?? ''} ${endpoint.id ?? ''}`,
      render: (endpoint) => (
        <PrimarySecondary
          primary={<code className="archdocPathCode">{endpoint.full_path ?? endpoint.path ?? '/'}</code>}
          secondary={
            <span>
              {(endpoint.include_prefix || endpoint.router_prefix) && endpoint.path !== endpoint.full_path
                ? [endpoint.include_prefix, endpoint.router_prefix, endpoint.path || '/'].filter(Boolean).join(' + ')
                : endpoint.id}
            </span>
          }
        />
      ),
    },
    {
      key: 'implementation',
      label: 'Implementation',
      sortable: true,
      value: (endpoint) => `${endpoint.function_name ?? ''} ${endpoint.module ?? ''}`,
      render: (endpoint) => (
        <PrimarySecondary
          primary={<code>{endpoint.function_name}</code>}
          secondary={<span>{endpoint.module}</span>}
        />
      ),
    },
    {
      key: 'contract',
      label: 'Contract',
      value: (endpoint) => `${endpoint.kwargs?.response_model ?? ''} ${(endpoint.parameters ?? []).map((param: any) => param.name).join(' ')}`,
      render: (endpoint) => (
        <PrimarySecondary
          primary={
            <code>
              {endpoint.kwargs?.response_model ??
                endpoint.route_options?.response_model ??
                'no response model'}
            </code>
          }
          secondary={<ParameterSummary parameters={endpoint.parameters ?? []} />}
        />
      ),
    },
    {
      key: 'linkage',
      label: 'Linkage',
      sortable: true,
      value: (endpoint) => (endpoint._linked ? 'linked' : 'open'),
      render: (endpoint) => <LinkStateIcon linked={Boolean(endpoint._linked)} />,
    },
    {
      key: 'source',
      label: 'Source',
      sortable: true,
      value: (endpoint) => `${endpoint.source?.file ?? ''}:${endpoint.source?.line_start ?? ''}`,
      render: (endpoint) => <SourceRef file={endpoint.source?.file} line={endpoint.source?.line_start} />,
    },
    {
      key: 'review',
      label: 'Review',
      value: (endpoint) => endpoint.review_status,
      render: (endpoint) => (
        <ReviewEditor
          item={endpoint}
          targetType="endpoint"
          targetId={endpoint.id}
          editable={editable}
          onSave={saveOverlay}
        />
      ),
    } as DataTableColumn<any, EndpointSortColumn>,
  ], [editable, saveOverlay]);

  const filters = useMemo<DataTableFilter<any>[]>(() => [
    {
      key: 'method',
      label: 'Method',
      value: methodFilter,
      onChange: setMethodFilter,
      options: [
        {label: 'All methods', value: 'all'},
        {label: 'GET', value: 'GET'},
        {label: 'POST', value: 'POST'},
        {label: 'PUT', value: 'PUT'},
        {label: 'PATCH', value: 'PATCH'},
        {label: 'DELETE', value: 'DELETE'},
      ],
      predicate: (endpoint, value) => value === 'all' || endpoint.http_method === value,
    },
    {
      key: 'contract',
      label: 'Contract',
      value: contractFilter,
      onChange: setContractFilter,
      options: [
        {label: 'All contracts', value: 'all'},
        {label: 'Has response model', value: 'has_response_model'},
        {label: 'Missing response model', value: 'missing_response_model'},
        {label: 'Has parameters', value: 'has_parameters'},
        {label: 'No parameters', value: 'no_parameters'},
      ],
      predicate: () => true,
    },
    {
      key: 'linkage',
      label: 'Linkage',
      value: linkageFilter,
      onChange: setLinkageFilter,
      options: [
        {label: 'All linkage', value: 'all'},
        {label: 'Linked', value: 'linked'},
        {label: 'Open', value: 'open'},
      ],
      predicate: (endpoint, value) => {
        if (value === 'all') return true;
        return value === 'linked' ? Boolean(endpoint._linked) : !endpoint._linked;
      },
    },
    {
      key: 'review_status',
      label: 'Review',
      value: reviewStatusFilter,
      onChange: setReviewStatusFilter,
      options: reviewStatusOptions,
      predicate: (endpoint, value) => value === 'all' || endpoint.review_status === value,
    },
  ], [contractFilter, linkageFilter, methodFilter, reviewStatusFilter]);

  if (error) return <p><strong>Error:</strong> {error}</p>;

  return (
    <div className="endpointTableWrapper">
      <CatalogToolbar
        title="API Endpoint Catalog"
        subtitle="Generated FastAPI route inventory with linkage, response, parameter, and review state."
        query={query}
        placeholder="Search method, path, module, function..."
        source={source}
        editable={editable}
        resultCount={0}
        totalCount={0}
        showControls={false}
        onQueryChange={setQuery}
      />

      <DataTable
        columns={columns}
        rowKey={(endpoint, index) => endpoint.generated_pk ?? `${endpoint.id}|${endpoint.source?.file}|${endpoint.source?.line_start}|${index}`}
        search={query}
        searchPlaceholder="Search endpoints..."
        defaultSort={{column: 'endpoint', direction: 'asc'}}
        filters={filters}
        fetchData={fetchEndpointRows}
        onSearchChange={setQuery}
      />
    </div>
  );
}

function initialSearchParam() {
  if (typeof window === 'undefined') return '';

  return new URLSearchParams(window.location.search).get('search') ?? '';
}


function ParameterSummary({parameters}: {parameters: any[]}) {
  if (parameters.length === 0) return <span>no detected parameters</span>;

  return (
    <span>
      {parameters.slice(0, 3).map((param) => (
        <span className="archdocInlineToken" key={`${param.name}-${param.source ?? ''}`}>
          {param.name}
          {param.source ? `:${param.source}` : ''}
        </span>
      ))}
      {parameters.length > 3 ? <span className="archdocMuted">+{parameters.length - 3}</span> : null}
    </span>
  );
}
