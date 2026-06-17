import {useEffect, useState} from 'react';
import {
  loadArchdocData,
  saveOverlayItem,
  type ArchdocData,
  type OverlayTargetType,
  type OverlayUpdate,
} from './archdocApi';

export function useArchdocData() {
  const [data, setData] = useState<ArchdocData>({
    services: [],
    endpoints: [],
    links: [],
    actions: [],
    validationReport: null,
    overlay: null,
    editable: false,
    source: 'static',
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    setError(null);

    try {
      setData(await loadArchdocData());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  async function saveOverlay(
    targetType: OverlayTargetType,
    targetId: string,
    payload: OverlayUpdate,
  ) {
    if (!data.editable) {
      throw new Error('Overlay editing requires the FastAPI backend.');
    }

    await saveOverlayItem(targetType, targetId, payload);
    await refresh();
  }

  useEffect(() => {
    refresh();
  }, []);

  return {data, loading, error, refresh, saveOverlay};
}
