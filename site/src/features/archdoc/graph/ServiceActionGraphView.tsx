import React, {useEffect, useMemo, useState} from 'react';
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  type Edge,
  type Node,
} from '@xyflow/react';
import ELK from 'elkjs/lib/elk.bundled.js';
import '@xyflow/react/dist/style.css';

import {fetchServiceActionGraph} from '../api/archdocApi';
import {
  actionLabel as actionGraphLabel,
  DetailBlock,
  DetailItem,
  EntityFieldTable,
  OperationActionSequence,
  OperationTypeUsageList,
  QueryDetails,
  QueryPartList,
  sourceLabel,
} from '../components/OperationActionDetails';
import {CatalogToolbar, OperationRelationBadge, OperationRelationSummary} from '../components/TablePrimitives';

type ServiceSummary = {
  id: string;
  class_name?: string;
  module?: string;
  operation_count?: number;
  endpoint_count?: number;
  action_count?: number;
};

type ServiceGraphPayload = {
  services: ServiceSummary[];
  selected_service_id: string | null;
  service: any | null;
  operations: any[];
  endpoints: any[];
  links: any[];
  actions: any[];
  operation_links: any[];
};

type GraphState = {
  nodes: Node[];
  edges: Edge[];
};

type ActionGroup = {
  key: string;
  kind: string;
  ownerId: string;
  sourceNodeId: string;
  label: string;
  target?: string;
  count: number;
  actions: any[];
};

type SelectedGraphNode = {
  id: string;
  nodeKind: string;
  service?: any;
  endpoint?: any;
  operation?: any;
  actionGroup?: ActionGroup;
  target?: string;
  actions?: any[];
  operationLinks?: any[];
  incomingOperationLinks?: any[];
};

const actionKinds = [
  {label: 'All actions', value: 'all'},
  {label: 'Database', value: 'database_action'},
  {label: 'DB transactions', value: 'database_transaction'},
  {label: 'Permissions', value: 'permission_action'},
  {label: 'Audit', value: 'audit_action'},
  {label: 'Workers', value: 'worker_action'},
  {label: 'External', value: 'external_action'},
  {label: 'Entities', value: 'entity_declaration'},
];

const elk = new ELK();

const graphLegendItems = [
  {label: 'Service class', className: 'archdocLegendDot--service'},
  {label: 'API endpoint', className: 'archdocLegendDot--endpoint'},
  {label: 'Service operation', className: 'archdocLegendDot--operation'},
  {label: 'Database action', className: 'archdocLegendDot--database'},
  {label: 'DB transaction', className: 'archdocLegendDot--transaction'},
  {label: 'Permission action', className: 'archdocLegendDot--permission'},
  {label: 'External / worker target', className: 'archdocLegendDot--target'},
];

export default function ServiceActionGraphView() {
  const [payload, setPayload] = useState<ServiceGraphPayload | null>(null);
  const [selectedServiceId, setSelectedServiceId] = useState('');
  const [actionKind, setActionKind] = useState('all');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [graph, setGraph] = useState<GraphState>({nodes: [], edges: []});
  const [selectedNode, setSelectedNode] = useState<SelectedGraphNode | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const nextPayload = await fetchServiceActionGraph({
          serviceId: selectedServiceId || undefined,
          actionKind,
          search: query,
        });

        if (cancelled) return;

        setPayload(nextPayload);

        if (!selectedServiceId && nextPayload.selected_service_id) {
          setSelectedServiceId(nextPayload.selected_service_id);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load service graph');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [selectedServiceId, actionKind, query]);

  const baseGraph = useMemo(() => buildGraph(payload), [payload]);

  useEffect(() => {
    setSelectedNode(null);
  }, [selectedServiceId, actionKind, query]);

  useEffect(() => {
    let cancelled = false;

    async function layout() {
      const next = await layoutGraph(baseGraph);

      if (!cancelled) {
        setGraph(next);
      }
    }

    layout();

    return () => {
      cancelled = true;
    };
  }, [baseGraph]);

  const services = payload?.services ?? [];
  const service = payload?.service;
  const counts = countActions(payload?.actions ?? []);

  return (
    <div className="endpointTableWrapper">
      <CatalogToolbar
        title="Service Action Graph"
        subtitle="Generated service-centered graph with endpoints, operations, actions, and detected external targets."
        query={query}
        placeholder="Filter actions by call, entity, permission..."
        source="backend"
        editable={false}
        resultCount={payload?.actions.length ?? 0}
        totalCount={payload?.actions.length ?? 0}
        showControls
        onQueryChange={setQuery}
      />

      <div className="archdocGraphControls">
        <label>
          <span>Service</span>
          <select value={selectedServiceId} onChange={(event) => setSelectedServiceId(event.target.value)}>
            {services.map((item) => (
              <option key={item.id} value={item.id}>
                {item.id} ({item.action_count ?? 0})
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Action type</span>
          <select value={actionKind} onChange={(event) => setActionKind(event.target.value)}>
            {actionKinds.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error ? <p className="archdocReviewError">{error}</p> : null}

      <section className="archdocGraphSummary">
        <Metric label="Operations" value={payload?.operations.length ?? 0} />
        <Metric label="Endpoints" value={payload?.endpoints.length ?? 0} />
        <Metric label="Actions" value={payload?.actions.length ?? 0} />
        <Metric label="DB" value={counts.database_action ?? 0} />
        <Metric label="Permissions" value={counts.permission_action ?? 0} />
        <Metric label="External" value={(counts.external_action ?? 0) + (counts.worker_action ?? 0)} />
      </section>

      <section className="archdocGraphLegend" aria-label="Graph legend">
        {graphLegendItems.map((item) => (
          <span key={item.label}>
            <i className={`archdocLegendDot ${item.className}`} />
            {item.label}
          </span>
        ))}
      </section>

      <section className="archdocGraphShell">
        <div className="archdocGraphHeader">
          <div>
            <strong>{service?.id ?? 'No service selected'}</strong>
            <span>{service?.class_name ?? service?.qualified_name ?? ''}</span>
          </div>
          {loading ? <span className="archdocMuted">Loading graph...</span> : null}
        </div>

        <ReactFlowProvider>
          <ReactFlow
            nodes={graph.nodes}
            edges={graph.edges}
            fitView
            minZoom={0.15}
            maxZoom={1.8}
            nodesDraggable
            className="archdocServiceGraph"
            onNodeClick={(_, node) => {
              setSelectedNode({
                id: node.id,
                ...(node.data as any),
              });
            }}
          >
            <MiniMap
              pannable
              zoomable
              position="bottom-right"
              nodeColor={miniMapNodeColor}
              nodeStrokeColor={miniMapNodeStrokeColor}
              nodeStrokeWidth={2}
              maskColor="rgba(15, 23, 42, 0.58)"
            />
            <Controls />
            <Background />
          </ReactFlow>
        </ReactFlowProvider>
        {selectedNode ? (
          <SelectedNodeInspector
            selected={selectedNode}
            onClose={() => setSelectedNode(null)}
          />
        ) : null}
      </section>
    </div>
  );
}

function miniMapNodeColor(node: Node) {
  if (hasNodeClass(node, 'archdocGraphNode--service')) return '#7c3aed';
  if (hasNodeClass(node, 'archdocGraphNode--endpoint')) return '#0284c7';
  if (hasNodeClass(node, 'archdocGraphNode--operation')) return '#059669';
  if (hasNodeClass(node, 'archdocGraphNode--database_action')) return '#d97706';
  if (hasNodeClass(node, 'archdocGraphNode--database_transaction')) return '#78716c';
  if (hasNodeClass(node, 'archdocGraphNode--permission_action')) return '#dc2626';
  if (hasNodeClass(node, 'archdocGraphNode--target')) return '#9333ea';
  if (hasNodeClass(node, 'archdocGraphNode--external_action')) return '#9333ea';
  if (hasNodeClass(node, 'archdocGraphNode--worker_action')) return '#9333ea';
  return '#475569';
}

function miniMapNodeStrokeColor(node: Node) {
  if (hasNodeClass(node, 'archdocGraphNode--service')) return '#c4b5fd';
  if (hasNodeClass(node, 'archdocGraphNode--endpoint')) return '#7dd3fc';
  if (hasNodeClass(node, 'archdocGraphNode--operation')) return '#6ee7b7';
  if (hasNodeClass(node, 'archdocGraphNode--database_action')) return '#fcd34d';
  if (hasNodeClass(node, 'archdocGraphNode--database_transaction')) return '#d6d3d1';
  if (hasNodeClass(node, 'archdocGraphNode--permission_action')) return '#fda4af';
  if (hasNodeClass(node, 'archdocGraphNode--target')) return '#d8b4fe';
  if (hasNodeClass(node, 'archdocGraphNode--external_action')) return '#d8b4fe';
  if (hasNodeClass(node, 'archdocGraphNode--worker_action')) return '#d8b4fe';
  return '#94a3b8';
}

function hasNodeClass(node: Node, className: string) {
  return String(node.className ?? '').split(/\s+/).includes(className);
}

function Metric({label, value}: {label: string; value: number}) {
  return (
    <div className="archdocGraphMetric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function countActions(actions: any[]) {
  return actions.reduce<Record<string, number>>((acc, action) => {
    const kind = action.kind ?? 'unknown';
    acc[kind] = (acc[kind] ?? 0) + 1;
    return acc;
  }, {});
}

function buildGraph(payload: ServiceGraphPayload | null): GraphState {
  if (!payload?.service) {
    return {nodes: [], edges: []};
  }

  const nodes = new Map<string, Node>();
  const edges = new Map<string, Edge>();
  const operations = payload.operations ?? [];
  const endpoints = payload.endpoints ?? [];
  const links = payload.links ?? [];
  const actions = payload.actions ?? [];
  const operationLinks = payload.operation_links ?? [];
  const operationIds = new Set(operations.map((operation) => operation.id));
  const actionsByOwner = actions.reduce<Map<string, any[]>>((acc, action) => {
    const ownerId = action.owner?.id;
    if (!ownerId) return acc;

    const ownerActions = acc.get(ownerId) ?? [];
    ownerActions.push(action);
    acc.set(ownerId, ownerActions);
    return acc;
  }, new Map<string, any[]>());
  const outgoingOperationLinksByOperation = operationLinks.reduce<Map<string, any[]>>((acc, link) => {
    const sourceOperationId = link.source?.operation_id;
    if (!sourceOperationId) return acc;

    const linksForOperation = acc.get(sourceOperationId) ?? [];
    linksForOperation.push(link);
    acc.set(sourceOperationId, linksForOperation);
    return acc;
  }, new Map<string, any[]>());
  const incomingOperationLinksByOperation = operationLinks.reduce<Map<string, any[]>>((acc, link) => {
    const targetOperationId = link.target?.operation_id;
    if (!targetOperationId) return acc;

    const linksForOperation = acc.get(targetOperationId) ?? [];
    linksForOperation.push(link);
    acc.set(targetOperationId, linksForOperation);
    return acc;
  }, new Map<string, any[]>());

  const addNode = (node: Node) => {
    if (!nodes.has(node.id)) {
      nodes.set(node.id, node);
    }
  };

  const addEdge = (edge: Edge) => {
    if (!edges.has(edge.id)) {
      edges.set(edge.id, edge);
    }
  };

  addNode({
    id: `service:${payload.service.id}`,
    type: 'default',
    position: {x: 0, y: 0},
    className: 'archdocGraphNode archdocGraphNode--service',
    data: {
      nodeKind: 'service',
      service: payload.service,
      label: (
        <NodeLabel
          title={payload.service.class_name ?? payload.service.id}
          subtitle={payload.service.id}
          meta={payload.service.module}
        />
      ),
    },
  });

  for (const operation of operations) {
    const operationNodeId = `operation:${operation.id}`;
    addNode({
      id: operationNodeId,
      position: {x: 0, y: 0},
      className: 'archdocGraphNode archdocGraphNode--operation',
      data: {
        nodeKind: 'operation',
        operation,
        actions: actionsByOwner.get(operation.id) ?? [],
        operationLinks: outgoingOperationLinksByOperation.get(operation.id) ?? [],
        incomingOperationLinks: incomingOperationLinksByOperation.get(operation.id) ?? [],
        label: (
          <NodeLabel
            title={operation.method}
            subtitle={operation.id}
            meta={operation.source?.file}
            relations={[
              ...(outgoingOperationLinksByOperation.get(operation.id) ?? []),
              ...(incomingOperationLinksByOperation.get(operation.id) ?? []),
            ]}
            operationId={operation.id}
          />
        ),
      },
    });
    addEdge({
      id: `service:${payload.service.id}->${operationNodeId}`,
      source: `service:${payload.service.id}`,
      target: operationNodeId,
      animated: false,
    });
  }

  const endpointsById = new Map(endpoints.map((endpoint) => [endpoint.id, endpoint]));

  for (const link of links) {
    const endpoint = endpointsById.get(link.endpoint_id);
    const operationNodeId = `operation:${link.operation_id}`;

    if (!endpoint || !operationIds.has(link.operation_id)) {
      continue;
    }

    const endpointNodeId = `endpoint:${endpoint.id}`;
    addNode({
      id: endpointNodeId,
      position: {x: 0, y: 0},
      className: 'archdocGraphNode archdocGraphNode--endpoint',
      data: {
        nodeKind: 'endpoint',
        endpoint,
        actions: actionsByOwner.get(endpoint.id) ?? [],
        label: <NodeLabel title={`${endpoint.http_method} ${endpoint.full_path ?? endpoint.path ?? '/'}`} subtitle={endpoint.function_name} />,
      },
    });
    addEdge({
      id: `${endpointNodeId}->${operationNodeId}`,
      source: endpointNodeId,
      target: operationNodeId,
      animated: false,
    });
  }

  const groupedActions = groupActions(actions, links);

  for (const group of groupedActions) {
    const actionNodeId = `action:${group.sourceNodeId}:${group.kind}:${group.key}`;
    addNode({
      id: actionNodeId,
      position: {x: 0, y: 0},
      className: `archdocGraphNode archdocGraphNode--action archdocGraphNode--${group.kind}`,
      data: {
        nodeKind: 'action',
        label: <NodeLabel title={labelForActionKind(group.kind)} subtitle={group.label} meta={`${group.count} call(s)`} />,
        actionGroup: group,
      },
    });
    addEdge({
      id: `${group.sourceNodeId}->${actionNodeId}`,
      source: group.sourceNodeId,
      target: actionNodeId,
      animated: group.kind === 'worker_action' || group.kind === 'external_action',
    });

    if (group.target) {
      const targetNodeId = `target:${group.kind}:${group.target}`;
      addNode({
        id: targetNodeId,
        position: {x: 0, y: 0},
        className: 'archdocGraphNode archdocGraphNode--target',
        data: {
          nodeKind: 'target',
          target: group.target,
          label: <NodeLabel title={group.target} subtitle={labelForActionKind(group.kind)} />,
        },
      });
      addEdge({
        id: `${actionNodeId}->${targetNodeId}`,
        source: actionNodeId,
        target: targetNodeId,
        animated: true,
      });
    }
  }

  return {nodes: Array.from(nodes.values()), edges: Array.from(edges.values())};
}

function groupActions(actions: any[], links: any[]) {
  const operationByEndpoint = new Map<string, string>();
  for (const link of links) {
    if (link.endpoint_id && link.operation_id) {
      operationByEndpoint.set(link.endpoint_id, link.operation_id);
    }
  }

  const groups = new Map<string, ActionGroup>();

  for (const action of actions) {
    const ownerId = action.owner?.id;
    if (!ownerId) continue;

    const kind = action.kind ?? 'unknown';
    if (kind === 'type_usage') continue;

    const label = actionGraphLabel(action);
    const sourceNodeId = sourceNodeIdForAction(action, operationByEndpoint);
    const key = `${sourceNodeId}|${ownerId}|${kind}|${label}`;
    const target = externalTarget(action);
    const existing = groups.get(key);

    if (existing) {
      existing.count += 1;
      existing.actions.push(action);
      continue;
    }

    groups.set(key, {
      key: slug(`${kind}-${label}`),
      kind,
      ownerId,
      sourceNodeId,
      label,
      target,
      count: 1,
      actions: [action],
    });
  }

  return Array.from(groups.values()).slice(0, 180);
}

function sourceNodeIdForAction(action: any, operationByEndpoint: Map<string, string>) {
  const ownerId = action.owner?.id;

  if (action.owner?.type === 'endpoint') {
    if (action.kind === 'permission_action') {
      return `endpoint:${ownerId}`;
    }

    const operationId = operationByEndpoint.get(ownerId);
    return operationId ? `operation:${operationId}` : `endpoint:${ownerId}`;
  }

  return `operation:${ownerId}`;
}

function externalTarget(action: any) {
  if (action.kind === 'worker_action') {
    return compactLabel(action.resource ?? action.call_name ?? 'worker');
  }

  if (action.kind === 'external_action') {
    return compactLabel(action.resource ?? action.call_name ?? 'external');
  }

  if (action.kind === 'audit_action') {
    return 'AuditService';
  }

  return undefined;
}

function labelForActionKind(kind: string) {
  return kind.replace(/_/g, ' ');
}

function compactLabel(value: string) {
  if (value.length <= 72) return value;
  return `${value.slice(0, 69)}...`;
}

function slug(value: string) {
  return value.replace(/[^a-zA-Z0-9_.-]+/g, '-').toLowerCase();
}

function NodeLabel({
  title,
  subtitle,
  meta,
  relations = [],
  operationId,
}: {
  title: string;
  subtitle?: string;
  meta?: string;
  relations?: any[];
  operationId?: string;
}) {
  return (
    <div className="archdocGraphNodeLabel">
      <strong>{title}</strong>
      {subtitle ? <span>{subtitle}</span> : null}
      {relations.length ? (
        <OperationRelationSummary links={relations} operationId={operationId} max={2} />
      ) : null}
      {meta ? <small>{meta}</small> : null}
    </div>
  );
}

function SelectedNodeInspector({
  selected,
  onClose,
}: {
  selected: SelectedGraphNode;
  onClose: () => void;
}) {
  return (
    <aside className="archdocNodeInspector" aria-label="Selected graph node details">
      <header className="archdocActionDetailsHeader">
        <div>
          <strong>{inspectorTitle(selected)}</strong>
          <span>{inspectorSubtitle(selected)}</span>
        </div>
        <button type="button" onClick={onClose}>Close</button>
      </header>
      <div className="archdocNodeInspectorBody">
        {selected.nodeKind === 'service' ? <ServiceInspector service={selected.service} /> : null}
        {selected.nodeKind === 'endpoint' ? <EndpointInspector endpoint={selected.endpoint} actions={selected.actions ?? []} /> : null}
        {selected.nodeKind === 'operation' ? (
          <OperationInspector
            operation={selected.operation}
            actions={selected.actions ?? []}
            operationLinks={selected.operationLinks ?? []}
            incomingOperationLinks={selected.incomingOperationLinks ?? []}
          />
        ) : null}
        {selected.nodeKind === 'action' && selected.actionGroup ? <ActionInspector group={selected.actionGroup} /> : null}
        {selected.nodeKind === 'target' ? (
          <DetailBlock title="Target">
            <dl className="archdocDetailsList">
              <DetailItem label="Value" value={selected.target} />
            </dl>
          </DetailBlock>
        ) : null}
      </div>
    </aside>
  );
}

function inspectorTitle(selected: SelectedGraphNode) {
  if (selected.nodeKind === 'service') return selected.service?.class_name ?? selected.service?.id ?? 'Service';
  if (selected.nodeKind === 'endpoint') return `${selected.endpoint?.http_method ?? ''} ${selected.endpoint?.full_path ?? selected.endpoint?.path ?? ''}`.trim();
  if (selected.nodeKind === 'operation') return selected.operation?.method ?? selected.operation?.id ?? 'Operation';
  if (selected.nodeKind === 'action') return selected.actionGroup?.label ?? 'Action';
  return selected.target ?? selected.id;
}

function inspectorSubtitle(selected: SelectedGraphNode) {
  if (selected.nodeKind === 'service') return selected.service?.id ?? '';
  if (selected.nodeKind === 'endpoint') return selected.endpoint?.function_name ?? '';
  if (selected.nodeKind === 'operation') return selected.operation?.id ?? '';
  if (selected.nodeKind === 'action') return `${selected.actionGroup?.kind ?? 'action'} - ${selected.actionGroup?.count ?? 0} call(s)`;
  return selected.nodeKind;
}

function ServiceInspector({service}: {service: any}) {
  return (
    <DetailBlock title="Service">
      <dl className="archdocDetailsList">
        <DetailItem label="ID" value={service?.id} />
        <DetailItem label="Class" value={service?.class_name} />
        <DetailItem label="Module" value={service?.module} />
        <DetailItem label="Description" value={service?.description} />
        <DetailItem label="Source" value={sourceLabel(service?.source)} />
      </dl>
      <DocstringBlock docstring={service?.docstring} />
    </DetailBlock>
  );
}

function EndpointInspector({endpoint, actions}: {endpoint: any; actions: any[]}) {
  return (
    <>
      <DetailBlock title="Endpoint">
        <dl className="archdocDetailsList">
          <DetailItem label="Method" value={endpoint?.http_method} />
          <DetailItem label="Path" value={endpoint?.full_path ?? endpoint?.path} />
          <DetailItem label="Include Prefix" value={endpoint?.include_prefix} />
          <DetailItem label="Local Path" value={endpoint?.path} />
          <DetailItem label="Router Prefix" value={endpoint?.router_prefix} />
          <DetailItem label="Function" value={endpoint?.function_name} />
          <DetailItem label="Module" value={endpoint?.module} />
          <DetailItem label="Source" value={sourceLabel(endpoint?.source)} />
        </dl>
      </DetailBlock>
      <OperationActionSequence actions={actions} title="Endpoint Gates" />
    </>
  );
}

function OperationInspector({
  operation,
  actions,
  operationLinks,
  incomingOperationLinks,
}: {
  operation: any;
  actions: any[];
  operationLinks: any[];
  incomingOperationLinks: any[];
}) {
  return (
    <>
      <DetailBlock title="Operation">
        <dl className="archdocDetailsList">
          <DetailItem label="Method" value={operation?.method} />
          <DetailItem label="ID" value={operation?.id} />
          <DetailItem label="Qualified" value={operation?.qualified_name} />
          <DetailItem label="Description" value={operation?.description} />
          <DetailItem label="Returns" value={operation?.returns} />
          <DetailItem label="Source" value={sourceLabel(operation?.source)} />
        </dl>
        <DocstringBlock docstring={operation?.docstring} />
      </DetailBlock>
      <ParameterList parameters={operation?.parameters ?? []} />
      <OperationLinkList title="Operation Links" links={operationLinks} direction="outgoing" />
      <OperationLinkList title="Incoming Links" links={incomingOperationLinks} direction="incoming" />
      <OperationTypeUsageList actions={actions} />
      <OperationActionSequence actions={actions} title="Detected Method Flow" />
    </>
  );
}

function DocstringBlock({docstring}: {docstring?: string | null}) {
  const value = String(docstring ?? '').trim();
  if (!value) return null;

  return <pre className="archdocDocstringBlock">{value}</pre>;
}

function OperationLinkList({
  title,
  links,
  direction,
}: {
  title: string;
  links: any[];
  direction: 'outgoing' | 'incoming';
}) {
  if (!links.length) {
    return <DetailBlock title={title}><p className="archdocMuted">No operation links detected.</p></DetailBlock>;
  }

  const sortedLinks = [...links]
    .sort((left, right) => (left.source_ref?.line_start ?? 0) - (right.source_ref?.line_start ?? 0))
    .slice(0, 16);

  return (
    <DetailBlock title={title}>
      <ol className="archdocInspectorSequence">
        {sortedLinks.map((link) => {
          const endpoint = direction === 'outgoing' ? link.target : link.source;
          const label = `${endpoint?.class_name ?? endpoint?.service_id ?? 'Service'}.${endpoint?.method_name ?? 'unknown'}`;

          return (
            <li key={link.id}>
              <OperationRelationBadge link={link} operationId={direction === 'outgoing' ? link.source?.operation_id : link.target?.operation_id} />
              <span>{label}</span>
              <small>{sourceLabel(link.source_ref)}</small>
            </li>
          );
        })}
      </ol>
    </DetailBlock>
  );
}


function ActionInspector({group}: {group: ActionGroup}) {
  const primaryAction = group.actions[0] ?? {};
  const primaryQuery = primaryAction.query;

  return (
    <>
      <DetailBlock title="Action">
        <dl className="archdocDetailsList">
          <DetailItem label="Kind" value={primaryAction.kind} />
          <DetailItem label="Method" value={primaryAction.call_name} />
          <DetailItem label="Resource" value={primaryAction.resource} />
          <DetailItem label="Access" value={primaryAction.access} />
          <DetailItem label="Owner" value={primaryAction.owner?.id} />
          <DetailItem label="Source" value={sourceLabel(primaryAction.source)} />
        </dl>
      </DetailBlock>
      {primaryAction.kind === 'worker_action' ? <WorkerDetails action={primaryAction} /> : null}
      {primaryAction.kind === 'permission_action' ? <PermissionDetails action={primaryAction} /> : null}
      {primaryQuery ? <QueryDetails query={primaryQuery} /> : null}
    </>
  );
}

function WorkerDetails({action}: {action: any}) {
  return (
    <DetailBlock title="Worker Job">
      <dl className="archdocDetailsList">
        <DetailItem label="Job type" value={action.details?.job_type} />
        <DetailItem label="Style" value={action.details?.dispatch_style} />
        <DetailItem label="Payload" value={action.details?.payload} />
        <DetailItem label="Schedule" value={action.details?.scheduled_at} />
        <DetailItem label="Priority" value={action.details?.priority} />
      </dl>
    </DetailBlock>
  );
}

function PermissionDetails({action}: {action: any}) {
  return (
    <DetailBlock title="Permission Gate">
      <dl className="archdocDetailsList">
        <DetailItem label="Required" value={action.resource} />
        <DetailItem label="Call" value={action.call_name} />
        <DetailItem label="Runs at" value={action.owner?.type === 'endpoint' ? 'endpoint dependency' : 'service code'} />
      </dl>
    </DetailBlock>
  );
}

function ParameterList({parameters}: {parameters: any[]}) {
  if (!parameters.length) {
    return <DetailBlock title="Parameters"><p className="archdocMuted">No parameters detected.</p></DetailBlock>;
  }

  return (
    <DetailBlock title="Parameters">
      <div className="archdocInspectorTokenList">
        {parameters.map((parameter) => (
          <span key={`${parameter.name}-${parameter.annotation ?? ''}`}>
            <strong>{parameter.name}</strong>
            {parameter.annotation ? <small>{parameter.annotation}</small> : null}
          </span>
        ))}
      </div>
    </DetailBlock>
  );
}

function DatabaseActionDetailsPanel({
  group,
  onClose,
}: {
  group: ActionGroup;
  onClose: () => void;
}) {
  const primaryAction = group.actions[0] ?? {};
  const primaryQuery = primaryAction.query;

  return (
    <section className="archdocActionDetails" aria-label="Database action details">
      <header className="archdocActionDetailsHeader">
        <div>
          <strong>{group.label}</strong>
          <span>
            {group.ownerId} · {group.count} call{group.count === 1 ? '' : 's'}
          </span>
        </div>
        <button type="button" onClick={onClose}>
          Close
        </button>
      </header>

      <div className="archdocActionDetailsGrid">
        <DetailBlock title="Action">
          <dl className="archdocDetailsList">
            <DetailItem label="Kind" value={primaryAction.kind} />
            <DetailItem label="Method" value={primaryAction.call_name} />
            <DetailItem label="Access" value={primaryAction.access} />
            <DetailItem label="Source" value={sourceLabel(primaryAction.source)} />
          </dl>
        </DetailBlock>

        <DetailBlock title="Query">
          {primaryQuery ? (
            <>
              <dl className="archdocDetailsList">
                <DetailItem label="Variable" value={primaryQuery.variable} />
                <DetailItem label="Operation" value={primaryQuery.operation} />
                <DetailItem label="Entities" value={(primaryQuery.entities ?? []).join(', ')} />
                <DetailItem label="Limit" value={primaryQuery.limit} />
              </dl>
              <pre className="archdocCodeBlock">{primaryQuery.expression}</pre>
            </>
          ) : (
            <p className="archdocMuted">No structured query information detected.</p>
          )}
        </DetailBlock>
      </div>

      {primaryQuery ? (
        <div className="archdocActionDetailsGrid">
          <QueryPartList title="Filters" values={primaryQuery.filters} />
          <QueryPartList title="Joins" values={primaryQuery.joins} />
          <QueryPartList title="Ordering" values={primaryQuery.ordering} />
        </div>
      ) : null}

      {Array.isArray(primaryQuery?.entity_details) && primaryQuery.entity_details.length ? (
        <div className="archdocEntityDetails">
          {primaryQuery.entity_details.map((entity: any) => (
            <DetailBlock key={entity.qualified_name ?? entity.name} title={entity.name}>
              <dl className="archdocDetailsList">
                <DetailItem label="Kind" value={entity.kind} />
                <DetailItem label="Table" value={entity.table_name} />
                <DetailItem label="Module" value={entity.module} />
                <DetailItem label="Source" value={sourceLabel(entity.source)} />
              </dl>
              <EntityFieldTable fields={entity.fields ?? []} />
            </DetailBlock>
          ))}
        </div>
      ) : null}
    </section>
  );
}

async function layoutGraph(graph: GraphState): Promise<GraphState> {
  if (!graph.nodes.length) {
    return graph;
  }

  const elkGraph = {
    id: 'root',
    layoutOptions: {
      'elk.algorithm': 'layered',
      'elk.direction': 'RIGHT',
      'elk.spacing.nodeNode': '44',
      'elk.layered.spacing.nodeNodeBetweenLayers': '72',
    },
    children: graph.nodes.map((node) => ({
      id: node.id,
      width: node.id.startsWith('action:') ? 260 : 300,
      height: node.id.startsWith('service:') ? 118 : 92,
    })),
    edges: graph.edges.map((edge) => ({
      id: edge.id,
      sources: [edge.source],
      targets: [edge.target],
    })),
  };

  const layout = await elk.layout(elkGraph);
  const positions = new Map<string, {x?: number; y?: number}>(
    (layout.children ?? []).map((node: any) => [node.id, node]),
  );

  return {
    nodes: graph.nodes.map((node) => {
      const next = positions.get(node.id);
      return {
        ...node,
        position: {
          x: next?.x ?? 0,
          y: next?.y ?? 0,
        },
      };
    }),
    edges: graph.edges,
  };
}
