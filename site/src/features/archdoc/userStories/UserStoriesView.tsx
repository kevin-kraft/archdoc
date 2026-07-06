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

import {fetchUserStoryDetail, fetchUserStoryRows, fetchUserStoryTrace} from '../api/archdocApi';
import {
  DetailItem,
  OperationActionSequence,
  OperationTypeUsageList,
  sourceLabel,
} from '../components/OperationActionDetails';
import {CatalogToolbar, MethodBadge, PrimarySecondary, SourceRef} from '../components/TablePrimitives';

type StoryDetailPayload = {
  story: any;
  linked_endpoints: any[];
};

type StoryTracePayload = {
  story: any;
  nodes: any[];
  edges: any[];
  unresolved_refs: any[];
  summary: {
    nodes: number;
    edges: number;
    unresolved_refs: number;
    by_kind: Record<string, number>;
  };
};

const statusOptions = ['all', 'draft', 'ready', 'in-progress', 'done', 'deprecated'];
const linkageOptions = ['all', 'linked', 'partial', 'missing', 'unmapped'];
const detailTabs = ['story', 'trace', 'endpoints'] as const;
type DetailTab = (typeof detailTabs)[number];

type TraceGraphState = {
  nodes: Node[];
  edges: Edge[];
};

type SelectedTraceNode = {
  id: string;
  nodeKind: string;
  traceNode: any;
  actionNodes?: any[];
};

const traceElk = new ELK();
const compactTraceDetailKinds = new Set(['database_transaction', 'type_usage']);
const traceActionDetailKinds = new Set([
  'database_action',
  'database_transaction',
  'permission_action',
  'audit_action',
  'worker_action',
  'external_action',
  'type_usage',
]);

export default function UserStoriesView() {
  const [stories, setStories] = useState<any[]>([]);
  const [selectedStoryId, setSelectedStoryId] = useState<string | null>(null);
  const [detail, setDetail] = useState<StoryDetailPayload | null>(null);
  const [trace, setTrace] = useState<StoryTracePayload | null>(null);
  const [query, setQuery] = useState('');
  const [area, setArea] = useState('all');
  const [status, setStatus] = useState('all');
  const [linkage, setLinkage] = useState('all');
  const [storyListCollapsed, setStoryListCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState<DetailTab>('story');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadStories() {
      setLoading(true);
      setError(null);

      try {
        const result = await fetchUserStoryRows({
          search: query,
          limit: 100,
          offset: 0,
          sortKey: 'id',
          sortDirection: 'asc',
          filters: {area, status, linkage},
        });

        if (cancelled) return;
        const nextStories = result.rows ?? [];
        setStories(nextStories);

        if (!selectedStoryId && nextStories[0]?.id) {
          setSelectedStoryId(nextStories[0].id);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load user stories');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadStories();

    return () => {
      cancelled = true;
    };
  }, [area, linkage, query, selectedStoryId, status]);

  useEffect(() => {
    if (!selectedStoryId) {
      setDetail(null);
      return;
    }

    const storyId = selectedStoryId;
    let cancelled = false;

    async function loadDetail() {
      try {
        const [result, traceResult] = await Promise.all([
          fetchUserStoryDetail(storyId),
          fetchUserStoryTrace(storyId),
        ]);
        if (!cancelled) {
          setDetail(result);
          setTrace(traceResult);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load user story detail');
        }
      }
    }

    loadDetail();

    return () => {
      cancelled = true;
    };
  }, [selectedStoryId]);

  const areaOptions = useMemo(() => {
    const values = Array.from(new Set(stories.map((story) => story.area).filter(Boolean))).sort();
    return ['all', ...values];
  }, [stories]);
  const displayedStories = useMemo(() => {
    if (linkage === 'all') return stories;
    return stories.filter((story) => story._linkage === linkage);
  }, [linkage, stories]);

  const selectedStory = detail?.story ?? displayedStories.find((story) => story.id === selectedStoryId);

  return (
    <div className="endpointTableWrapper">
      <CatalogToolbar
        title="User Stories"
        subtitle="Manual user journeys linked to generated endpoints, services, and architecture actions."
        query={query}
        placeholder="Search story id, title, area..."
        source="backend"
        editable={false}
        resultCount={displayedStories.length}
        totalCount={stories.length}
        showControls
        onQueryChange={setQuery}
      />

      <div className="archdocGraphControls archdocUserStoryControls">
        <label>
          <span>Area</span>
          <select value={area} onChange={(event) => setArea(event.target.value)}>
            {areaOptions.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
        <label>
          <span>Status</span>
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            {statusOptions.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
        <label>
          <span>Linkage</span>
          <select value={linkage} onChange={(event) => setLinkage(event.target.value)}>
            {linkageOptions.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
      </div>

      {error ? <p className="archdocReviewError">{error}</p> : null}
      {loading ? <p className="archdocMuted">Loading user stories...</p> : null}

      <div className={`archdocUserStoryLayout ${storyListCollapsed ? 'archdocUserStoryLayout--collapsed' : ''}`}>
        {!storyListCollapsed ? (
          <section className="archdocUserStoryList" aria-label="User story list">
            {displayedStories.map((story) => (
              <button
                type="button"
                key={story.id}
                className={`archdocUserStoryItem ${story.id === selectedStoryId ? 'archdocUserStoryItem--active' : ''}`}
                onClick={() => {
                  setSelectedStoryId(story.id);
                  setActiveTab('story');
                }}
              >
                <span className="archdocUserStoryItemHeader">
                  <strong>{story.id}</strong>
                  <LinkageBadge value={story._linkage} />
                </span>
                <span>{story.title}</span>
                <small>{story.area} · {story.status}</small>
              </button>
            ))}
          </section>
        ) : null}

        <section className="archdocUserStoryDetail" aria-label="User story detail">
          {selectedStory ? (
            <>
              <header className="archdocUserStoryDetailHeader">
                <div>
                  <strong>{selectedStory.title}</strong>
                  <span>{selectedStory.id} · {selectedStory.area} · {selectedStory.status}</span>
                </div>
                <div className="archdocUserStoryHeaderActions">
                  <button
                    type="button"
                    className="archdocUserStoryToggle"
                    aria-pressed={storyListCollapsed}
                    onClick={() => setStoryListCollapsed((value) => !value)}
                  >
                    {storyListCollapsed ? 'Show stories' : 'Hide stories'}
                  </button>
                  <LinkageBadge value={selectedStory._linkage} />
                </div>
              </header>

              <div className="archdocUserStoryMeta">
                <Metric label="Declared endpoints" value={selectedStory._link_summary?.declared_endpoints ?? 0} />
                <Metric label="Linked endpoints" value={selectedStory._link_summary?.linked_endpoints ?? 0} />
                <Metric label="Roles" value={(selectedStory.roles ?? []).length} />
              </div>

              <div className="archdocUserStoryTabs" role="tablist" aria-label="User story detail views">
                {detailTabs.map((tab) => (
                  <button
                    type="button"
                    key={tab}
                    role="tab"
                    aria-selected={activeTab === tab}
                    className={activeTab === tab ? 'archdocUserStoryTab--active' : ''}
                    onClick={() => setActiveTab(tab)}
                  >
                    {tabLabel(tab)}
                  </button>
                ))}
              </div>

              {activeTab === 'story' ? <StoryMarkdown markdown={selectedStory.body_markdown ?? ''} /> : null}
              {activeTab === 'trace' ? <UserStoryTrace trace={trace} /> : null}
              {activeTab === 'endpoints' ? <StoryEndpointLinks links={detail?.linked_endpoints ?? []} /> : null}
            </>
          ) : (
            <p className="archdocMuted">No user story selected.</p>
          )}
        </section>
      </div>
    </div>
  );
}

function tabLabel(tab: DetailTab) {
  if (tab === 'story') return 'Story';
  if (tab === 'trace') return 'Trace';
  return 'Endpoints';
}

function UserStoryTrace({trace}: {trace: StoryTracePayload | null}) {
  const [graph, setGraph] = useState<TraceGraphState>({nodes: [], edges: []});
  const [selectedNode, setSelectedNode] = useState<SelectedTraceNode | null>(null);
  const baseGraph = useMemo(() => buildTraceGraph(trace), [trace]);

  useEffect(() => {
    let cancelled = false;

    async function layout() {
      const next = await layoutTraceGraph(baseGraph);

      if (!cancelled) {
        setGraph(next);
      }
    }

    layout();

    return () => {
      cancelled = true;
    };
  }, [baseGraph]);

  useEffect(() => {
    setSelectedNode(null);
  }, [trace?.story?.id]);

  if (!trace) {
    return <p className="archdocMuted">Loading architecture trace...</p>;
  }

  const byKind = trace.summary?.by_kind ?? {};

  return (
    <section className="archdocStoryTrace" aria-label="User story architecture trace">
      <header className="archdocStoryTraceHeader">
        <div>
          <strong>Architecture Trace</strong>
          <span>{trace.summary.nodes} nodes Â· {trace.summary.edges} edges</span>
        </div>
        {trace.summary.unresolved_refs ? (
          <span className="archdocTraceBadge archdocTraceBadge--warning">
            {trace.summary.unresolved_refs} unresolved
          </span>
        ) : (
          <span className="archdocTraceBadge">linked</span>
        )}
      </header>

      <div className="archdocStoryTraceMetrics">
        {['endpoint', 'service', 'operation', 'database_action', 'entity', 'permission_action', 'worker_action', 'audit_action'].map((kind) => (
          <Metric key={kind} label={kind.replace(/_/g, ' ')} value={byKind[kind] ?? 0} />
        ))}
      </div>

      <section className="archdocTraceGraphShell" aria-label="Trace graph">
        <ReactFlowProvider>
          <ReactFlow
            nodes={graph.nodes}
            edges={graph.edges}
            fitView
            minZoom={0.2}
            maxZoom={1.6}
            nodesDraggable
            className="archdocTraceGraph"
            onNodeClick={(_, node) => {
              setSelectedNode({id: node.id, ...(node.data as any)});
            }}
          >
            <MiniMap
              pannable
              zoomable
              position="bottom-right"
              nodeColor={traceMiniMapNodeColor}
              nodeStrokeColor={traceMiniMapNodeStrokeColor}
              nodeStrokeWidth={2}
              maskColor="rgba(15, 23, 42, 0.5)"
            />
            <Controls />
            <Background />
          </ReactFlow>
        </ReactFlowProvider>
        {selectedNode ? <TraceNodeInspector selected={selectedNode} onClose={() => setSelectedNode(null)} /> : null}
      </section>
    </section>
  );
}

function buildTraceGraph(trace: StoryTracePayload | null): TraceGraphState {
  if (!trace?.nodes?.length) {
    return {nodes: [], edges: []};
  }

  const includedIds = selectTraceNodeIds(trace.nodes, trace.edges);
  const actionNodesByOwner = collectTraceActionNodes(trace.nodes, trace.edges);
  const nodes: Node[] = trace.nodes
    .filter((node) => includedIds.has(node.id))
    .map((node) => ({
      id: node.id,
      position: {x: 0, y: 0},
      className: `archdocGraphNode archdocGraphNode--${traceGraphKind(node.kind)} archdocTraceGraphNode`,
      data: {
        nodeKind: node.kind,
        traceNode: node,
        actionNodes: actionNodesByOwner.get(node.id) ?? [],
        label: (
          <TraceGraphNodeLabel
            title={traceNodeTitle(node)}
            subtitle={traceNodeSubtitle(node)}
            meta={traceNodeMeta(node)}
          />
        ),
      },
    }));

  const edges: Edge[] = trace.edges
    .filter((edge) => includedIds.has(edge.source) && includedIds.has(edge.target))
    .map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label,
      animated: edge.label === 'calls_service' || edge.label === 'does',
      className: `archdocTraceGraphEdge archdocTraceGraphEdge--${cssKind(edge.label)}`,
    }));

  return {nodes, edges};
}

function selectTraceNodeIds(nodes: any[], edges: any[]) {
  const essentialKinds = new Set(['user_story', 'endpoint', 'service', 'operation']);
  const selected = new Set<string>();
  const nodesById = new Map(nodes.map((node) => [node.id, node]));
  const visibleEdges = edges.filter((edge) => {
    const sourceNode = nodesById.get(edge.source);
    const targetNode = nodesById.get(edge.target);
    return !compactTraceDetailKinds.has(sourceNode?.kind) && !compactTraceDetailKinds.has(targetNode?.kind);
  });

  for (const node of orderTraceNodes(nodes)) {
    if (essentialKinds.has(node.kind)) {
      selected.add(node.id);
    }
  }

  if (!selected.size) {
    for (const node of orderTraceNodes(nodes)) {
      if (!compactTraceDetailKinds.has(node.kind)) {
        selected.add(node.id);
        break;
      }
    }
  }

  let changed = true;
  while (changed && selected.size < 120) {
    changed = false;
    for (const edge of visibleEdges) {
      if (selected.has(edge.source) && !selected.has(edge.target) && selected.size < 120) {
        selected.add(edge.target);
        changed = true;
      }
      if (selected.has(edge.target) && !selected.has(edge.source) && selected.size < 120) {
        selected.add(edge.source);
        changed = true;
      }
    }
  }

  pruneDisconnectedTraceNodes(selected, visibleEdges);

  return selected;
}

function pruneDisconnectedTraceNodes(selected: Set<string>, edges: any[]) {
  const connected = new Set<string>();
  for (const edge of edges) {
    if (selected.has(edge.source) && selected.has(edge.target)) {
      connected.add(edge.source);
      connected.add(edge.target);
    }
  }

  for (const id of Array.from(selected)) {
    if (!connected.has(id) && !id.startsWith('story:')) {
      selected.delete(id);
    }
  }
}

function collectTraceActionNodes(nodes: any[], edges: any[]) {
  const nodesById = new Map(nodes.map((node) => [node.id, node]));
  const actionsByOwner = new Map<string, any[]>();

  for (const edge of edges) {
    const actionNode = nodesById.get(edge.target);
    if (!actionNode || !traceActionDetailKinds.has(actionNode.kind)) {
      continue;
    }

    const ownerActions = actionsByOwner.get(edge.source) ?? [];
    ownerActions.push(normalizeTraceAction(actionNode));
    actionsByOwner.set(edge.source, ownerActions);
  }

  for (const [ownerId, actions] of actionsByOwner) {
    actionsByOwner.set(ownerId, actions.sort((left, right) => (left.source?.line_start ?? 0) - (right.source?.line_start ?? 0)));
  }

  return actionsByOwner;
}

function normalizeTraceAction(node: any) {
  const payload = node?.payload ?? {};
  return {
    ...payload,
    id: payload.id ?? node.id,
    kind: node.kind ?? payload.kind,
    resource: payload.resource ?? payload.entity ?? node.label ?? node.target_id,
    entity: payload.entity ?? node.target_id,
    call_name: payload.call_name,
    action: payload.action,
    query: payload.query,
    source: payload.source,
  };
}

function TraceGraphNodeLabel({title, subtitle, meta}: {title: string; subtitle?: string; meta?: string}) {
  return (
    <div className="archdocGraphNodeLabel archdocTraceGraphNodeLabel">
      <strong>{title}</strong>
      {subtitle ? <span>{subtitle}</span> : null}
      {meta ? <small>{meta}</small> : null}
    </div>
  );
}

function TraceNodeInspector({selected, onClose}: {selected: SelectedTraceNode; onClose: () => void}) {
  const node = selected.traceNode;
  const payload = node?.payload ?? {};

  return (
    <aside className="archdocNodeInspector archdocTraceNodeInspector" aria-label="Selected trace node details">
      <header className="archdocActionDetailsHeader">
        <div>
          <strong>{traceNodeTitle(node)}</strong>
          <span>{formatTraceKind(node?.kind)}</span>
        </div>
        <button type="button" onClick={onClose}>Close</button>
      </header>
      <div className="archdocNodeInspectorBody">
        <dl className="archdocDetailsList">
          <DetailItem label="ID" value={node?.target_id ?? node?.id} />
          <DetailItem label="Label" value={node?.label} />
          <DetailItem label="Path" value={payload.full_path ?? payload.path} />
          <DetailItem label="Function" value={payload.function_name} />
          <DetailItem label="Service" value={payload.service_id ?? payload.id} />
          <DetailItem label="Operation" value={payload.method ?? payload.operation_id} />
          <DetailItem label="Source" value={sourceLabel(payload.source)} />
        </dl>
        <TraceOperationActionDetails nodeKind={selected.nodeKind} actions={selected.actionNodes ?? []} />
      </div>
    </aside>
  );
}

function TraceOperationActionDetails({nodeKind, actions}: {nodeKind: string; actions: any[]}) {
  if (!actions.length) {
    return null;
  }

  const title = nodeKind === 'endpoint' ? 'Endpoint Gates' : 'Detected Method Flow';

  return (
    <>
      <OperationTypeUsageList actions={actions} />
      <OperationActionSequence actions={actions} title={title} />
    </>
  );
}

function traceMiniMapNodeColor(node: Node) {
  if (hasNodeClass(node, 'archdocGraphNode--user_story')) return '#0f766e';
  if (hasNodeClass(node, 'archdocGraphNode--endpoint')) return '#0284c7';
  if (hasNodeClass(node, 'archdocGraphNode--service')) return '#7c3aed';
  if (hasNodeClass(node, 'archdocGraphNode--operation')) return '#059669';
  if (hasNodeClass(node, 'archdocGraphNode--database_action')) return '#d97706';
  if (hasNodeClass(node, 'archdocGraphNode--database_transaction')) return '#78716c';
  if (hasNodeClass(node, 'archdocGraphNode--permission_action')) return '#dc2626';
  if (hasNodeClass(node, 'archdocGraphNode--entity')) return '#ca8a04';
  return '#9333ea';
}

function traceMiniMapNodeStrokeColor(node: Node) {
  if (hasNodeClass(node, 'archdocGraphNode--user_story')) return '#5eead4';
  if (hasNodeClass(node, 'archdocGraphNode--endpoint')) return '#7dd3fc';
  if (hasNodeClass(node, 'archdocGraphNode--service')) return '#c4b5fd';
  if (hasNodeClass(node, 'archdocGraphNode--operation')) return '#6ee7b7';
  if (hasNodeClass(node, 'archdocGraphNode--database_action')) return '#fcd34d';
  if (hasNodeClass(node, 'archdocGraphNode--database_transaction')) return '#d6d3d1';
  if (hasNodeClass(node, 'archdocGraphNode--permission_action')) return '#fda4af';
  if (hasNodeClass(node, 'archdocGraphNode--entity')) return '#fde68a';
  return '#d8b4fe';
}

function hasNodeClass(node: Node, className: string) {
  return String(node.className ?? '').split(/\s+/).includes(className);
}

function traceGraphKind(kind: string) {
  if (kind === 'user_story') return 'user_story';
  if (kind === 'entity') return 'entity';
  return cssKind(kind);
}

async function layoutTraceGraph(graph: TraceGraphState): Promise<TraceGraphState> {
  if (!graph.nodes.length) {
    return graph;
  }

  const elkGraph = {
    id: 'trace-root',
    layoutOptions: {
      'elk.algorithm': 'layered',
      'elk.direction': 'RIGHT',
      'elk.spacing.nodeNode': '32',
      'elk.layered.spacing.nodeNodeBetweenLayers': '56',
    },
    children: graph.nodes.map((node) => ({
      id: node.id,
      width: traceNodeWidth(node),
      height: node.id.startsWith('story:') ? 98 : 82,
    })),
    edges: graph.edges.map((edge) => ({
      id: edge.id,
      sources: [edge.source],
      targets: [edge.target],
    })),
  };

  const layout = await traceElk.layout(elkGraph);
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

function traceNodeWidth(node: Node) {
  if (node.id.startsWith('story:')) return 260;
  if (node.id.startsWith('endpoint:')) return 300;
  if (node.id.startsWith('operation:')) return 280;
  return 240;
}

function traceNodeTitle(node: any) {
  const payload = node?.payload ?? {};
  if (node?.kind === 'endpoint') return `${payload.http_method ?? ''} ${payload.full_path ?? payload.path ?? node.label}`.trim();
  if (node?.kind === 'service') return payload.class_name ?? node.label;
  if (node?.kind === 'operation') return payload.method ?? node.label;
  return node?.label ?? node?.target_id ?? node?.id ?? 'Trace node';
}

function traceNodeSubtitle(node: any) {
  const payload = node?.payload ?? {};
  if (node?.kind === 'user_story') return node.target_id;
  if (node?.kind === 'endpoint') return payload.function_name;
  if (node?.kind === 'service') return payload.id ?? node.target_id;
  if (node?.kind === 'operation') return payload.id ?? node.target_id;
  return formatTraceKind(node?.kind);
}

function orderTraceNodes(nodes: any[]) {
  const weight: Record<string, number> = {
    user_story: 0,
    endpoint: 1,
    service: 2,
    operation: 3,
    database_action: 4,
    database_transaction: 4,
    permission_action: 4,
    audit_action: 4,
    worker_action: 4,
    external_action: 4,
    entity: 5,
  };

  return [...nodes].sort((left, right) => {
    const leftWeight = weight[left.kind] ?? 9;
    const rightWeight = weight[right.kind] ?? 9;
    if (leftWeight !== rightWeight) return leftWeight - rightWeight;
    return String(left.label ?? left.id).localeCompare(String(right.label ?? right.id));
  });
}

function traceNodeMeta(node: any) {
  const payload = node?.payload ?? {};
  if (node?.kind === 'endpoint') return payload.source?.file ? sourceLabel(payload.source) : payload.module;
  if (node?.kind === 'service') return payload.module ?? payload.qualified_name ?? node.target_id;
  if (node?.kind === 'operation') return payload.qualified_name ?? sourceLabel(payload.source) ?? node.target_id;
  if (node?.kind === 'entity') return node.target_id;
  return payload.source?.file ? sourceLabel(payload.source) : node?.target_id;
}

function formatTraceKind(kind: string) {
  return String(kind ?? 'node').replace(/_/g, ' ');
}

function cssKind(kind: string) {
  return String(kind ?? 'node').replace(/[^a-z0-9_-]/gi, '-');
}
function StoryMarkdown({markdown}: {markdown: string}) {
  const blocks = parseMarkdownBlocks(markdown);

  if (!blocks.length) {
    return null;
  }

  return (
    <section className="archdocStoryMarkdown" aria-label="User story markdown">
      {blocks.map((block, index) => renderMarkdownBlock(block, index))}
    </section>
  );
}

function StoryEndpointLinks({links}: {links: any[]}) {
  if (!links.length) {
    return <p className="archdocMuted">No endpoint references declared.</p>;
  }

  return (
    <div className="archdocStoryLinks">
      {links.map((entry, index) => (
        <section className="archdocStoryLinkCard" key={`${entry.ref?.method}-${entry.ref?.path}-${index}`}>
          <header>
            <div>
              <MethodBadge method={entry.ref?.method} />{' '}
              <a className="archdocPathCode archdocStoryEndpointLink" href={catalogHref('api-endpoints', entry)}>
                {entry.ref?.path}
              </a>
            </div>
            <LinkageBadge value={entry.match_status} />
          </header>

          <div className="archdocStoryCatalogLinks">
            <a href={catalogHref('api-endpoints', entry)}>API Endpoint Catalog</a>
            <a href={catalogHref('interfaces', entry)}>Interfaces Catalog</a>
          </div>

          {entry.endpoint ? (
            <PrimarySecondary
              primary={<span>{entry.endpoint.function_name}</span>}
              secondary={<SourceRef file={entry.endpoint.source?.file} line={entry.endpoint.source?.line_start} />}
            />
          ) : (
            <p className="archdocMuted">No generated endpoint matched this reference.</p>
          )}

          {entry.links?.map((linkEntry: any, linkIndex: number) => (
            <div className="archdocStoryArchitecture" key={`${linkEntry.link?.id ?? linkIndex}`}>
              <PrimarySecondary
                primary={<code>{linkEntry.service?.id ?? linkEntry.link?.service_id}</code>}
                secondary={<span>{linkEntry.operation?.method ?? linkEntry.link?.operation_method}</span>}
              />
              <ActionSummary actions={linkEntry.actions ?? []} />
            </div>
          ))}
        </section>
      ))}
    </div>
  );
}

function catalogHref(page: 'api-endpoints' | 'interfaces', entry: any) {
  const endpoint = entry.endpoint;
  const search = endpoint?.full_path ?? endpoint?.path ?? entry.ref?.path ?? '';
  return `/docs/architecture/generated/${page}?search=${encodeURIComponent(search)}`;
}

function ActionSummary({actions}: {actions: any[]}) {
  const counts = actions.reduce<Record<string, number>>((acc, action) => {
    const kind = action.kind ?? 'unknown';
    acc[kind] = (acc[kind] ?? 0) + 1;
    return acc;
  }, {});

  const items = Object.entries(counts);
  if (!items.length) {
    return <span className="archdocMuted">No actions detected.</span>;
  }

  return (
    <div className="archdocActionChipRow">
      {items.map(([kind, count]) => (
        <span className="archdocActionChip" key={kind}>{kind.replace(/_/g, ' ')}: {count}</span>
      ))}
    </div>
  );
}

type MarkdownBlock =
  | {type: 'heading'; level: number; text: string}
  | {type: 'paragraph'; text: string}
  | {type: 'list'; ordered: boolean; items: string[]}
  | {type: 'table'; rows: string[][]};

function parseMarkdownBlocks(markdown: string): MarkdownBlock[] {
  const lines = markdown.replace(/\r\n/g, '\n').split('\n');
  const blocks: MarkdownBlock[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index].trim();

    if (!line) {
      index += 1;
      continue;
    }

    const heading = /^(#{1,4})\s+(.+)$/.exec(line);
    if (heading) {
      blocks.push({type: 'heading', level: heading[1].length, text: stripInlineMarkdown(heading[2])});
      index += 1;
      continue;
    }

    const isOrdered = /^\d+\.\s+/.test(line);
    const isBullet = /^[-*]\s+/.test(line);
    if (isOrdered || isBullet) {
      const items: string[] = [];

      while (index < lines.length) {
        const itemLine = lines[index].trim();
        const match = isOrdered
          ? /^\d+\.\s+(.+)$/.exec(itemLine)
          : /^[-*]\s+(?:\[[ xX]\]\s+)?(.+)$/.exec(itemLine);

        if (!match) break;
        items.push(stripInlineMarkdown(match[1]));
        index += 1;
      }

      blocks.push({type: 'list', ordered: isOrdered, items});
      continue;
    }

    if (line.startsWith('|') && line.endsWith('|')) {
      const rows: string[][] = [];

      while (index < lines.length) {
        const tableLine = lines[index].trim();
        if (!tableLine.startsWith('|') || !tableLine.endsWith('|')) break;

        const cells = tableLine
          .slice(1, -1)
          .split('|')
          .map((cell) => stripInlineMarkdown(cell.trim()));

        if (!cells.every((cell) => /^-+$/.test(cell))) {
          rows.push(cells);
        }
        index += 1;
      }

      blocks.push({type: 'table', rows});
      continue;
    }

    const paragraphLines = [line];
    index += 1;
    while (index < lines.length && lines[index].trim()) {
      const next = lines[index].trim();
      if (/^(#{1,4})\s+/.test(next) || /^\d+\.\s+/.test(next) || /^[-*]\s+/.test(next) || next.startsWith('|')) {
        break;
      }
      paragraphLines.push(next);
      index += 1;
    }
    blocks.push({type: 'paragraph', text: stripInlineMarkdown(paragraphLines.join(' '))});
  }

  return blocks;
}

function renderMarkdownBlock(block: MarkdownBlock, index: number) {
  if (block.type === 'heading') {
    const Heading = block.level <= 1 ? 'h2' : block.level === 2 ? 'h3' : 'h4';
    return <Heading key={index}>{block.text}</Heading>;
  }

  if (block.type === 'paragraph') {
    return <p key={index}>{block.text}</p>;
  }

  if (block.type === 'list') {
    const List = block.ordered ? 'ol' : 'ul';
    return (
      <List key={index}>
        {block.items.map((item, itemIndex) => (
          <li key={`${index}-${itemIndex}`}>{item}</li>
        ))}
      </List>
    );
  }

  const [head, ...body] = block.rows;
  if (!head) return null;

  return (
    <div className="archdocStoryMarkdownTableWrap" key={index}>
      <table className="archdocStoryMarkdownTable">
        <thead>
          <tr>
            {head.map((cell, cellIndex) => <th key={cellIndex}>{cell}</th>)}
          </tr>
        </thead>
        <tbody>
          {body.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((cell, cellIndex) => <td key={cellIndex}>{cell}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function stripInlineMarkdown(value: string) {
  return value
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .trim();
}

function LinkageBadge({value}: {value?: string}) {
  const normalized = value ?? 'unmapped';
  return <span className={`archdocLinkageBadge archdocLinkageBadge--${normalized}`}>{normalized}</span>;
}

function Metric({label, value}: {label: string; value: number}) {
  return (
    <div className="archdocGraphMetric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
