export type OverlayTargetType =
  | 'service'
  | 'operation'
  | 'endpoint'
  | 'endpoint_service_link'
  | 'architecture_action'
  | 'validation_issue'
  | 'user_story'
  | 'bpmn_process'
  | 'bpmn_task';

export type ReviewStatus =
  | 'generated'
  | 'needs_review'
  | 'reviewed'
  | 'accepted'
  | 'needs_refactor'
  | 'false_positive'
  | 'deprecated';

export type OverlayUpdate = {
  review_status?: ReviewStatus | null;
  labels: string[];
  status_markers: string[];
  owner?: string | null;
  notes?: string | null;
  links: Record<string, string[]>;
  overrides: Record<string, unknown>;
  metadata: {
    author?: string | null;
    updated_at?: string | null;
    rationale?: string | null;
  };
};

export type ArchdocData = {
  services: any[];
  endpoints: any[];
  links: any[];
  actions: any[];
  validationReport: any | null;
  overlay: any | null;
  editable: boolean;
  source: 'backend' | 'static';
};

declare global {
  interface Window {
    ARCHDOC_API_BASE_URL?: string;
  }
}

export function getArchdocApiBaseUrl() {
  if (typeof window === 'undefined') return '';

  if (window.ARCHDOC_API_BASE_URL !== undefined) {
    return window.ARCHDOC_API_BASE_URL;
  }

  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:8010';
  }

  return '';
}

function buildArchdocUrl(path: string) {
  const baseUrl = getArchdocApiBaseUrl();

  if (baseUrl) {
    return new URL(path, baseUrl);
  }

  if (typeof window !== 'undefined') {
    return new URL(path, window.location.origin);
  }

  return new URL(path, 'http://localhost');
}

export async function loadArchdocData(): Promise<ArchdocData> {
  try {
    const response = await fetch(`${getArchdocApiBaseUrl()}/api/catalog/effective`);

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    const payload = await response.json();

    return {
      services: payload.services ?? [],
      endpoints: payload.endpoints ?? [],
      links: payload.links ?? [],
      actions: payload.actions ?? [],
      validationReport: payload.validation_report ?? null,
      overlay: payload.overlay ?? null,
      editable: true,
      source: 'backend',
    };
  } catch {
    const [servicesRes, endpointsRes, linksRes, actionsRes, validationRes] = await Promise.all([
      fetch('/archdoc/services.json'),
      fetch('/archdoc/endpoints.json'),
      fetch('/archdoc/endpoint_service_links.json'),
      fetch('/archdoc/architecture_actions.json'),
      fetch('/archdoc/validation_report.json'),
    ]);

    if (!servicesRes.ok || !endpointsRes.ok || !linksRes.ok || !validationRes.ok) {
      throw new Error('Failed to load archdoc JSON data');
    }

    const servicesJson = await servicesRes.json();
    const endpointsJson = await endpointsRes.json();
    const linksJson = await linksRes.json();
    const actionsJson = actionsRes.ok ? await actionsRes.json() : {actions: []};
    const validationJson = await validationRes.json();

    return {
      services: servicesJson.services ?? [],
      endpoints: endpointsJson.endpoints ?? [],
      links: linksJson.links ?? [],
      actions: actionsJson.actions ?? [],
      validationReport: validationJson,
      overlay: null,
      editable: false,
      source: 'static',
    };
  }
}

export async function saveOverlayItem(
  targetType: OverlayTargetType,
  targetId: string,
  payload: OverlayUpdate,
) {
  const response = await fetch(
    `${getArchdocApiBaseUrl()}/api/overlays/${targetType}/${encodeURIComponent(targetId)}`,
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
  );

  if (!response.ok) {
    throw new Error(`Failed to save overlay item: ${response.status}`);
  }

  return response.json();
}

export async function loadBackendHealth() {
  const response = await fetch(`${getArchdocApiBaseUrl()}/health`);

  if (!response.ok) {
    throw new Error(`Backend health failed: ${response.status}`);
  }

  return response.json();
}

export type TableQueryParams = {
  search: string;
  limit: number;
  offset: number;
  sortKey: string;
  sortDirection: 'asc' | 'desc';
  filters: Record<string, string>;
};

export async function fetchEndpointRows(params: TableQueryParams) {
  return fetchTableRows('/api/table/endpoints', {
    search: params.search,
    limit: String(params.limit),
    offset: String(params.offset),
    sort: params.sortKey,
    direction: params.sortDirection,
    method: params.filters.method ?? 'all',
    contract: params.filters.contract ?? 'all',
    linkage: params.filters.linkage ?? 'all',
    review_status: params.filters.review_status ?? 'all',
  });
}

export async function fetchOperationRows(params: TableQueryParams) {
  return fetchTableRows('/api/table/operations', {
    search: params.search,
    limit: String(params.limit),
    offset: String(params.offset),
    sort: params.sortKey,
    direction: params.sortDirection,
    coverage: params.filters.coverage ?? 'all',
    review_status: params.filters.review_status ?? 'all',
  });
}

export async function fetchInterfaceRows(params: TableQueryParams) {
  return fetchTableRows('/api/table/interfaces', {
    search: params.search,
    limit: String(params.limit),
    offset: String(params.offset),
    sort: params.sortKey,
    direction: params.sortDirection,
    confidence: params.filters.confidence ?? 'all',
    review_status: params.filters.review_status ?? 'all',
  });
}

export async function fetchValidationIssueRows(params: TableQueryParams) {
  return fetchTableRows('/api/table/validation-issues', {
    search: params.search,
    limit: String(params.limit),
    offset: String(params.offset),
    sort: params.sortKey,
    direction: params.sortDirection,
    severity: params.filters.severity ?? 'all',
    code: params.filters.code ?? 'all',
    review_status: params.filters.review_status ?? 'all',
  });
}

export async function fetchValidationStats() {
  const response = await fetch(`${getArchdocApiBaseUrl()}/api/validation/stats`);

  if (!response.ok) {
    throw new Error(`Failed to load validation stats: ${response.status}`);
  }

  return response.json();
}

export async function fetchUserStoryRows(params: TableQueryParams) {
  return fetchTableRows('/api/table/user-stories', {
    search: params.search,
    limit: String(params.limit),
    offset: String(params.offset),
    sort: params.sortKey,
    direction: params.sortDirection,
    area: params.filters.area ?? 'all',
    status: params.filters.status ?? 'all',
    linkage: params.filters.linkage ?? 'all',
  });
}

export async function fetchUserStoryDetail(storyId: string) {
  const response = await fetch(
    `${getArchdocApiBaseUrl()}/api/user-stories/${encodeURIComponent(storyId)}`,
  );

  if (!response.ok) {
    throw new Error(`Failed to load user story: ${response.status}`);
  }

  return response.json();
}

export async function fetchUserStoryTrace(storyId: string) {
  const response = await fetch(
    `${getArchdocApiBaseUrl()}/api/user-stories/${encodeURIComponent(storyId)}/trace`,
  );

  if (!response.ok) {
    throw new Error(`Failed to load user story trace: ${response.status}`);
  }

  return response.json();
}

export async function fetchServiceActionGraph(params: {
  serviceId?: string;
  actionKind?: string;
  search?: string;
}) {
  const url = buildArchdocUrl('/api/graph/services');

  if (params.serviceId) {
    url.searchParams.set('service_id', params.serviceId);
  }

  url.searchParams.set('action_kind', params.actionKind ?? 'all');
  url.searchParams.set('search', params.search ?? '');

  const response = await fetch(url.toString());

  if (!response.ok) {
    throw new Error(`Failed to load service graph: ${response.status}`);
  }

  return response.json();
}

async function fetchTableRows(path: string, params: Record<string, string>) {
  const url = buildArchdocUrl(path);

  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, value);
  }

  const response = await fetch(url.toString());

  if (!response.ok) {
    throw new Error(`Failed to load table rows: ${response.status}`);
  }

  return response.json() as Promise<{rows: any[]; total: number}>;
}

export function overlayFromItem(item: any): OverlayUpdate {
  const overlay = item?._overlay ?? {};

  return {
    review_status: overlay.review_status ?? item?.review_status ?? 'generated',
    labels: overlay.labels ?? [],
    status_markers: overlay.status_markers ?? [],
    owner: overlay.owner ?? '',
    notes: overlay.notes ?? '',
    links: overlay.links ?? {},
    overrides: overlay.overrides ?? {},
    metadata: overlay.metadata ?? {},
  };
}
