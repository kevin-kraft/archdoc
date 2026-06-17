import React, {useMemo, useState} from 'react';
import DataTable, {type DataTableColumn, type DataTableFilter} from '../components/DataTable';
import ReviewEditor from '../components/ReviewEditor';
import {CatalogToolbar, LinkStateIcon, PrimarySecondary, SourceRef} from '../components/TablePrimitives';
import {fetchOperationRows} from '../api/archdocApi';
import {useArchdocTableContext} from '../api/useArchdocTableContext';
import {reviewStatusOptions} from '../constants/reviewStatusOptions';

type OperationRow = {
  service: any;
  operation: any;
  _linked?: boolean;
};

type OperationSortColumn = 'service' | 'operation' | 'coverage' | 'source' | 'review';

export default function OperationsCatalogView() {
  const {source, editable, error, saveOverlay} = useArchdocTableContext();
  const [query, setQuery] = useState('');
  const [coverageFilter, setCoverageFilter] = useState('all');
  const [reviewStatusFilter, setReviewStatusFilter] = useState('all');

  const columns = useMemo<DataTableColumn<OperationRow, OperationSortColumn>[]>(() => [
    {
      key: 'service',
      label: 'Service',
      sortable: true,
      value: ({service}) => `${service.id ?? ''} ${service.class_name ?? ''}`,
      render: ({service}) => (
        <PrimarySecondary
          primary={<code>{service.id}</code>}
          secondary={<span>{service.class_name}</span>}
        />
      ),
    },
    {
      key: 'operation',
      label: 'Operation',
      sortable: true,
      value: ({operation}) => `${operation.method ?? ''} ${operation.id ?? ''}`,
      render: ({operation}) => (
        <PrimarySecondary
          primary={<code>{operation.method}</code>}
          secondary={<span>{operation.id}</span>}
        />
      ),
    },
    {
      key: 'coverage',
      label: 'Coverage',
      sortable: true,
      value: (row) => row._linked ? 'linked' : 'open',
      render: (row) => <LinkStateIcon linked={Boolean(row._linked)} />,
    },
    {
      key: 'review',
      label: 'Review',
      value: ({operation}) => operation.review_status,
      render: ({operation}) => (
        <ReviewEditor
          item={operation}
          targetType="operation"
          targetId={operation.id}
          editable={editable}
          onSave={saveOverlay}
        />
      ),
    },
    {
      key: 'source',
      label: 'Source',
      sortable: true,
      value: ({operation}) => `${operation.source?.file ?? ''}:${operation.source?.line_start ?? ''}`,
      render: ({operation}) => <SourceRef file={operation.source?.file} line={operation.source?.line_start} />,
    },
  ], [editable, saveOverlay]);

  const filters = useMemo<DataTableFilter<OperationRow>[]>(() => [
    {
      key: 'coverage',
      label: 'Coverage',
      value: coverageFilter,
      onChange: setCoverageFilter,
      options: [
        {label: 'All coverage', value: 'all'},
        {label: 'Linked', value: 'linked'},
        {label: 'Open', value: 'open'},
      ],
      predicate: (row, value) => {
        if (value === 'all') return true;
        return value === 'linked' ? Boolean(row._linked) : !row._linked;
      },
    },
    {
      key: 'review_status',
      label: 'Review',
      value: reviewStatusFilter,
      onChange: setReviewStatusFilter,
      options: reviewStatusOptions,
      predicate: (row, value) => value === 'all' || row.operation.review_status === value,
    },
  ], [coverageFilter, reviewStatusFilter]);

  if (error) return <p><strong>Error:</strong> {error}</p>;

  return (
    <div className="endpointTableWrapper">
      <CatalogToolbar
        title="Service Operations"
        subtitle="Generated service operation inventory with endpoint coverage and review status."
        query={query}
        placeholder="Search service, class, operation..."
        source={source}
        editable={editable}
        resultCount={0}
        totalCount={0}
        showControls={false}
        onQueryChange={setQuery}
      />

      <DataTable
        columns={columns}
        rowKey={({service, operation}, index) => [
          service.id,
          operation.id,
          operation.qualified_name,
          operation.source?.file,
          operation.source?.line_start,
          index,
        ].join('|')}
        search={query}
        searchPlaceholder="Search operations..."
        defaultSort={{column: 'service', direction: 'asc'}}
        filters={filters}
        fetchData={fetchOperationRows}
        onSearchChange={setQuery}
      />
    </div>
  );
}
