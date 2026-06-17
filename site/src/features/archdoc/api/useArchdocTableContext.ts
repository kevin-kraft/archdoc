import {useEffect, useState} from 'react';
import {
  loadBackendHealth,
  saveOverlayItem,
  type OverlayTargetType,
  type OverlayUpdate,
} from './archdocApi';

export function useArchdocTableContext() {
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        await loadBackendHealth();
        setReady(true);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Backend unavailable');
      }
    }

    load();
  }, []);

  async function saveOverlay(
    targetType: OverlayTargetType,
    targetId: string,
    payload: OverlayUpdate,
  ) {
    await saveOverlayItem(targetType, targetId, payload);
  }

  return {
    source: ready ? 'backend' : 'static',
    editable: ready,
    ready,
    error,
    saveOverlay,
  };
}
