import React, {useEffect, useMemo, useState} from 'react';
import DataTable, {
  type DataTableColumn,
  type DataTableFilter,
} from '@site/src/features/archdoc/components/DataTable';
import ReviewEditor from './ReviewEditor';
import {
  CatalogToolbar,
  ConfidenceBadge,
  MethodBadge,
  PrimarySecondary,
  SeverityBadge,
  SourceRef,
} from './TablePrimitives';
import type {OverlayTargetType, OverlayUpdate} from './archdocApi';
import {fetchValidationIssueRows, fetchValidationStats} from './archdocApi';
import {useArchdocData} from './useArchdocData';
import {reviewStatusOptions} from '@site/src/features/archdoc/constants/reviewStatusOptions';

type Props = {
  showIssues?: boolean;
};

export default function ValidationSummary({showIssues = true}: Props) {
  const {data, loading, error, saveOverlay} = useArchdocData();
  const [query, setQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [codeFilter, setCodeFilter] = useState('all');
  const [reviewStatusFilter, setReviewStatusFilter] = useState('all');
  const [validationStats, setValidationStats] = useState<any | null>(null);
  const summary = data.validationReport?.summary;
  const issues = data.validationReport?.issues ?? [];

  useEffect(() => {
    let cancelled = false;

    fetchValidationStats()
      .then((stats) => {
        if (!cancelled) setValidationStats(stats);
      })
      .catch(() => {
        if (!cancelled) setValidationStats(null);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const issueCounts = useMemo(() => {
    const counts = new Map<string, {severity: string; code: string; count: number}>();

    for (const issue of issues) {
      const key = `${issue.severity}:${issue.code}`;
      const current = counts.get(key);
      counts.set(key, {
        severity: issue.severity,
        code: issue.code,
        count: (current?.count ?? 0) + 1,
      });
    }

    return Array.from(counts.values()).sort((a, b) => b.count - a.count);
  }, [issues]);

  const importantIssues = useMemo(() => {
    return issues
      .filter((issue: any) => issue.severity === 'error' || issue.severity === 'warning')
      .sort((a: any, b: any) => severityRank(a.severity) - severityRank(b.severity));
  }, [issues]);

  const implementationCounts = useMemo(() => {
    const counts = new Map<string, number>();

    for (const endpoint of data.endpoints) {
      const kind = endpoint.implementation?.kind ?? 'unknown';
      counts.set(kind, (counts.get(kind) ?? 0) + 1);
    }

    return Array.from(counts.entries())
      .map(([kind, count]) => ({kind, count}))
      .sort((a, b) => b.count - a.count);
  }, [data.endpoints]);

  const multiLinkedEndpoints = useMemo(() => {
    const linksByEndpoint = data.links.reduce((acc: Record<string, any[]>, link: any) => {
      if (!acc[link.endpoint_id]) acc[link.endpoint_id] = [];
      acc[link.endpoint_id].push(link);
      return acc;
    }, {});

    return Object.entries(linksByEndpoint)
      .filter(([, links]) => links.length > 1)
      .sort((a, b) => b[1].length - a[1].length);
  }, [data.links]);

  if (loading) return <p>Loading validation report...</p>;
  if (error) return <p><strong>Error:</strong> {error}</p>;
  if (!summary) return <p>No validation report found.</p>;

  const endpointCoverage = summary.endpoints === 0
    ? 0
    : (summary.linked_endpoints / summary.endpoints) * 100;
  const operationStats = validationStats?.operations;
  const operationLinkStats = validationStats?.operation_links;
  const operationEndpointCoverage = percent(
    operationStats?.with_endpoint_link,
    operationStats?.total,
  );
  const operationDependencyCoverage = percent(
    operationStats?.with_any_operation_dependency,
    operationStats?.total,
  );


  // const isolatedOperations = operationStats.filter((operation) => {
  //   return (
  //     !operation.endpoint_links?.length &&
  //     !operation.incoming_service_calls?.length &&
  //     !operation.outgoing_service_calls?.length
  //   );
  // });

  const isolatedOperationCount = operationStats?.isolated ?? 0;

  return (
    <div className="endpointTableWrapper">
      <CatalogToolbar
        title="Validation Dashboard"
        subtitle="Architecture quality signals from the deterministic catalog validator."
        query={query}
        placeholder="Search validation issues..."
        source={data.source}
        editable={data.editable}
        resultCount={issues.length}
        totalCount={issues.length}
        showControls={false}
        onQueryChange={setQuery}
      />

      <div className="archdocMetricGrid">
        <Metric label="Services" value={summary.services} />
        <Metric label="Operations" value={summary.operations} />
        <Metric label="Endpoints" value={summary.endpoints} />
        <Metric label="Links" value={summary.endpoint_service_links} />
        <Metric label="Linked Endpoints" value={`${summary.linked_endpoints}/${summary.endpoints}`} />
        <Metric label="Unlinked Endpoints" value={summary.unlinked_endpoints} variant="warning" />
        <Metric label="Errors" value={summary.errors} variant={summary.errors > 0 ? 'danger' : 'success'} />
        <Metric label="Warnings" value={summary.warnings} variant="warning" />
      </div>

      <CoverageBar value={endpointCoverage} />

      {operationStats ? (
        
        <section className="archdocSection">
          <h2>Operation Reachability</h2>
          <div className="archdocMetricGrid">
            <Metric
              label="Reachable from endpoints:"
              value={`${operationStats.with_endpoint_link}/${operationStats.total}`}
              variant={operationEndpointCoverage >= 70 ? 'success' : 'warning'}
            />
            <Metric
              label="Operations calling other operations: "
              value={`${operationStats.with_any_operation_dependency}/${operationStats.total}`}
            />
            <Metric label="Operations calling other service operations" value={operationStats.with_outgoing_service_call} />
            <Metric label="Operations called by services" value={operationStats.with_incoming_service_call} />
            <Metric label="Detected operation calls:" value={operationLinkStats?.total ?? 0} />
            <Metric
              label="Resolved operation calls"
              value={`${operationLinkStats?.resolved ?? 0}/${operationLinkStats?.total ?? 0}`}
              variant={(operationLinkStats?.unresolved ?? 0) > 0 ? 'warning' : 'success'}
            />
            {/* <Metric
              label="Isolated operations"
              value={`${isolatedOperationCount}/${operationStats.total}`}
              variant={isolatedOperationCount > 0 ? 'warning' : 'success'}
            /> */}
          </div>
          {/* <CoverageBar label="Operation Endpoint Coverage" value={operationEndpointCoverage} /> */}
          {/* <CoverageBar label="Operation Dependency Coverage" value={operationDependencyCoverage} /> */}
        </section>
      ) : null}

      <div className="archdocTwoColumn">
        <IssueCountTable items={issueCounts} />
        <ImplementationTable items={implementationCounts} total={data.endpoints.length} />
      </div>

      <MultiLinkTable items={multiLinkedEndpoints.slice(0, 20)} />

      {showIssues && (
        <ValidationIssueDataTable
          query={query}
          severityFilter={severityFilter}
          codeFilter={codeFilter}
          reviewStatusFilter={reviewStatusFilter}
          editable={data.editable}
          onSave={saveOverlay}
          onQueryChange={setQuery}
          onSeverityChange={setSeverityFilter}
          onCodeChange={setCodeFilter}
          onReviewStatusChange={setReviewStatusFilter}
        />
      )}
    </div>
  );
}

function Metric({
  label,
  value,
  variant = 'default',
}: {
  label: string;
  value: string | number;
  variant?: 'default' | 'success' | 'warning' | 'danger';
}) {
  return (
    <div className={`archdocMetric archdocMetric--${variant}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function CoverageBar({value, label = 'Endpoint-Service Coverage'}: {value: number; label?: string}) {
  return (
    <div className="archdocCoverage">
      <div className="archdocCoverageHeader">
        <strong>{label}</strong>
        <span>{value.toFixed(1)}%</span>
      </div>
      <div className="archdocCoverageTrack">
        <div className="archdocCoverageFill" style={{width: `${Math.min(value, 100)}%`}} />
      </div>
    </div>
  );
}

function percent(value?: number, total?: number) {
  if (!total) return 0;
  return ((value ?? 0) / total) * 100;
}

function IssueCountTable({items}: {items: {severity: string; code: string; count: number}[]}) {
  return (
    <section className="archdocSection">
      <h2>Issue Counts</h2>
      <div className="endpointTableScroll">
        <table className="endpointTable archdocDataTable">
          <thead>
            <tr>
              <th>Severity</th>
              <th>Code</th>
              <th>Count</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={`${item.severity}-${item.code}`}>
                <td><SeverityBadge severity={item.severity} /></td>
                <td><code>{item.code}</code></td>
                <td><strong>{item.count}</strong></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ImplementationTable({items, total}: {items: {kind: string; count: number}[]; total: number}) {
  return (
    <section className="archdocSection">
      <h2>Endpoint Implementation Types</h2>
      <div className="endpointTableScroll">
        <table className="endpointTable archdocDataTable">
          <thead>
            <tr>
              <th>Kind</th>
              <th>Count</th>
              <th>Share</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.kind}>
                <td><code>{item.kind}</code></td>
                <td><strong>{item.count}</strong></td>
                <td>{total === 0 ? '0.0' : ((item.count / total) * 100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function MultiLinkTable({items}: {items: [string, any[]][]}) {
  return (
    <section className="archdocSection">
      <h2>Multi-linked Endpoints</h2>
      {items.length === 0 ? (
        <p className="archdocMuted">No endpoints with multiple service links.</p>
      ) : (
        <div className="endpointTableScroll">
          <table className="endpointTable archdocDataTable">
            <thead>
              <tr>
                <th>Endpoint ID</th>
                <th>Links</th>
              </tr>
            </thead>
            <tbody>
              {items.map(([endpointId, links]) => (
                <tr key={endpointId}>
                  <td><code>{endpointId}</code></td>
                  <td><strong>{links.length}</strong></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

type ValidationIssueSortColumn = 'severity' | 'code' | 'item' | 'source' | 'review';

function ValidationIssueDataTable({
  query,
  severityFilter,
  codeFilter,
  reviewStatusFilter,
  editable,
  onSave,
  onQueryChange,
  onSeverityChange,
  onCodeChange,
  onReviewStatusChange,
}: {
  query: string;
  severityFilter: string;
  codeFilter: string;
  reviewStatusFilter: string;
  editable: boolean;
  onSave: (targetType: OverlayTargetType, targetId: string, payload: OverlayUpdate) => Promise<void>;
  onQueryChange: (value: string) => void;
  onSeverityChange: (value: string) => void;
  onCodeChange: (value: string) => void;
  onReviewStatusChange: (value: string) => void;
}) {
  const columns = useMemo<DataTableColumn<any, ValidationIssueSortColumn>[]>(() => [
    {
      key: 'severity',
      label: 'Severity',
      sortable: true,
      value: (issue) => issue.severity,
      render: (issue) => <SeverityBadge severity={issue.severity} />,
    },
    {
      key: 'code',
      label: 'Issue',
      sortable: true,
      value: (issue) => `${issue.code ?? ''} ${issue.message ?? ''}`,
      render: (issue) => (
        <PrimarySecondary
          primary={<code>{issue.code}</code>}
          secondary={<span>{issue.message}</span>}
        />
      ),
    },
    {
      key: 'item',
      label: 'Target',
      sortable: true,
      value: (issue) => `${issue.item_id ?? ''} ${issue.details?.qualified_name ?? ''}`,
      render: (issue) => {
        const details = issue.details ?? {};

        return (
          <PrimarySecondary
            primary={
              details.http_method ? (
                <>
                  <MethodBadge method={details.http_method} />{' '}
                  <code className="archdocPathCode">{details.path ?? '-'}</code>
                </>
              ) : (
                <code>{issue.item_id ?? '-'}</code>
              )
            }
            secondary={<span>{details.function_name ?? details.qualified_name ?? issue.item_id ?? ''}</span>}
          />
        );
      },
    },
    {
      key: 'review',
      label: 'Review',
      sortable: true,
      value: (issue) => issue.review_status,
      render: (issue) => (
        <ReviewEditor
          item={issue}
          targetType="validation_issue"
          targetId={validationIssueTargetId(issue)}
          editable={editable}
          onSave={onSave}
        />
      ),
    },
    {
      key: 'source',
      label: 'Source',
      sortable: true,
      value: (issue) => `${issue.source_file ?? ''}:${issue.line_start ?? ''}`,
      render: (issue) => <SourceRef file={issue.source_file} line={issue.line_start} />,
    },
  ], [editable, onSave]);

  const filters = useMemo<DataTableFilter<any>[]>(() => [
    {
      key: 'severity',
      label: 'Severity',
      value: severityFilter,
      onChange: onSeverityChange,
      options: [
        {label: 'All severities', value: 'all'},
        {label: 'Errors', value: 'error'},
        {label: 'Warnings', value: 'warning'},
        {label: 'Infos', value: 'info'},
      ],
      predicate: (issue, value) => value === 'all' || issue.severity === value,
    },
    {
      key: 'code',
      label: 'Code',
      value: codeFilter,
      onChange: onCodeChange,
      options: [
        {label: 'All codes', value: 'all'},
        {label: 'Resolved collisions', value: 'resolved_collisions'},
        {label: 'Identity signals', value: 'identity'},
        {label: 'Class name reused', value: 'service_class_name_reused'},
        {label: 'Service linkage open', value: 'service_linkage_open'},
        {label: 'Endpoint mapping open', value: 'endpoint_mapping_open'},
        {label: 'Operation mapping open', value: 'operation_mapping_open'},
        {label: 'Endpoint no service', value: 'endpoint_without_service_link'},
        {label: 'Service candidate open', value: 'endpoint_service_candidate_not_linked'},
        {label: 'Operation unreferenced', value: 'operation_without_endpoint_link'},
      ],
      predicate: () => true,
    },
    {
      key: 'review_status',
      label: 'Review',
      value: reviewStatusFilter,
      onChange: onReviewStatusChange,
      options: reviewStatusOptions,
      predicate: (issue, value) => value === 'all' || issue.review_status === value,
    },
  ], [
    codeFilter,
    onCodeChange,
    onReviewStatusChange,
    onSeverityChange,
    reviewStatusFilter,
    severityFilter,
  ]);

  return (
    <section className="archdocSection">
      <h2>Validation Issues</h2>
      <DataTable
        columns={columns}
        rowKey={(issue, index) => `${validationIssueTargetId(issue)}|${index}`}
        search={query}
        searchPlaceholder="Search code, target, source, message..."
        defaultSort={{column: 'severity', direction: 'asc'}}
        filters={filters}
        fetchData={fetchValidationIssueRows}
        onSearchChange={onQueryChange}
      />
    </section>
  );
}

function cleanEnum(value?: string | null) {
  if (!value) return value;

  return value
    .replace('EndpointImplementationKind.', '')
    .replace('DetectionConfidence.', '');
}

function severityRank(severity: string) {
  if (severity === 'error') return 0;
  if (severity === 'warning') return 1;
  return 2;
}

function validationIssueTargetId(issue: any) {
  return [
    issue.code ?? '',
    issue.item_id ?? '',
    issue.source_file ?? '',
    issue.line_start ?? '',
  ].join('|');
}
