import React, {useEffect, useMemo, useState} from 'react';
import {compareText, nextSort, SortHeader, type SortState} from './TablePrimitives';

export type DataTableColumn<T, TColumn extends string> = {
  key: TColumn;
  label: string;
  sortable?: boolean;
  width?: string;
  value: (row: T) => unknown;
  render?: (row: T) => React.ReactNode;
};

export type DataTableFilter<T> = {
  key: string;
  label: string;
  value: string;
  options: {label: string; value: string}[];
  predicate: (row: T, value: string) => boolean;
  onChange: (value: string) => void;
};

type Props<T, TColumn extends string> = {
  rows?: T[];
  columns: DataTableColumn<T, TColumn>[];
  rowKey: (row: T, index: number) => string;
  search: string;
  searchPlaceholder: string;
  defaultSort: SortState<TColumn>;
  filters?: DataTableFilter<T>[];
  emptyLabel?: string;
  fetchData?: (params: {
    search: string;
    limit: number;
    offset: number;
    sortKey: TColumn;
    sortDirection: 'asc' | 'desc';
    filters: Record<string, string>;
  }) => Promise<{rows: T[]; total: number}>;
  onSearchChange: (value: string) => void;
};

const pageSizes = [25, 50, 100, 250];

export default function DataTable<T, TColumn extends string>({
  rows = [],
  columns,
  rowKey,
  search,
  searchPlaceholder,
  defaultSort,
  filters = [],
  emptyLabel = 'No rows found.',
  fetchData,
  onSearchChange,
}: Props<T, TColumn>) {
  const [sort, setSort] = useState<SortState<TColumn>>(defaultSort);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(50);
  const [serverRows, setServerRows] = useState<T[]>([]);
  const [serverTotal, setServerTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const filterValues = useMemo(() => {
    return Object.fromEntries(filters.map((filter) => [filter.key, filter.value]));
  }, [filters]);

  useEffect(() => {
    if (!fetchData) return;

    let cancelled = false;
    const loadData = fetchData;
    const timeout = window.setTimeout(() => {
      async function load() {
        setLoading(true);
        setError(null);

        try {
          const result = await loadData({
            search,
            limit,
            offset: (page - 1) * limit,
            sortKey: sort.column,
            sortDirection: sort.direction,
            filters: filterValues,
          });

          if (cancelled) return;
          setServerRows(result.rows);
          setServerTotal(result.total);
        } catch (err) {
          if (cancelled) return;
          setError(err instanceof Error ? err.message : 'Failed to load table data');
        } finally {
          if (!cancelled) setLoading(false);
        }
      }

      load();
    }, 200);

    return () => {
      cancelled = true;
      window.clearTimeout(timeout);
    };
  }, [fetchData, filterValues, limit, page, search, sort]);

  const visibleRows = useMemo(() => {
    if (fetchData) return serverRows;

    const normalizedSearch = search.trim().toLowerCase();
    const matching = rows.filter((row) => {
      const filterMatch = filters.every((filter) => filter.predicate(row, filter.value));

      if (!filterMatch) return false;
      if (!normalizedSearch) return true;

      return columns.some((column) => {
        return String(column.value(row) ?? '').toLowerCase().includes(normalizedSearch);
      });
    });

    const sortColumn = columns.find((column) => column.key === sort.column);

    if (!sortColumn) return matching;

    return [...matching].sort((left, right) => {
      const direction = sort.direction === 'asc' ? 1 : -1;
      return compareText(sortColumn.value(left), sortColumn.value(right)) * direction;
    });
  }, [columns, fetchData, filters, rows, search, serverRows, sort]);

  const totalRows = fetchData ? serverTotal : visibleRows.length;
  const totalPages = Math.max(1, Math.ceil(totalRows / limit));
  const safePage = Math.min(page, totalPages);
  const offset = (safePage - 1) * limit;
  const pageRows = fetchData ? visibleRows : visibleRows.slice(offset, offset + limit);

  function updateSearch(value: string) {
    setPage(1);
    onSearchChange(value);
  }

  function updateLimit(value: string) {
    setPage(1);
    setLimit(Number(value));
  }

  function updateSort(column: TColumn) {
    setPage(1);
    setSort((current) => nextSort(current, column));
  }

  return (
    <div className="archdocDataTableShell">
      <div className="archdocDataTableControls">
        <input
          value={search}
          onChange={(event) => updateSearch(event.target.value)}
          placeholder={searchPlaceholder}
          className="endpointTableSearch"
        />

        {filters.map((filter) => (
          <label className="archdocDataTableFilter" key={filter.key}>
            <span>{filter.label}</span>
            <select
              value={filter.value}
              onChange={(event) => {
                setPage(1);
                filter.onChange(event.target.value);
              }}
            >
              {filter.options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        ))}

        <label className="archdocDataTableFilter">
          <span>Rows</span>
          <select value={limit} onChange={(event) => updateLimit(event.target.value)}>
            {pageSizes.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="endpointTableScroll">
        <table className="endpointTable archdocDataTable">
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column.key} style={column.width ? {width: column.width} : undefined}>
                  {column.sortable ? (
                    <SortHeader
                      column={column.key}
                      label={column.label}
                      sort={sort}
                      onSort={updateSort}
                    />
                  ) : (
                    column.label
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={columns.length} className="archdocEmptyCell">
                  Loading rows...
                </td>
              </tr>
            ) : error ? (
              <tr>
                <td colSpan={columns.length} className="archdocEmptyCell">
                  {error}
                </td>
              </tr>
            ) : pageRows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="archdocEmptyCell">
                  {emptyLabel}
                </td>
              </tr>
            ) : (
              pageRows.map((row, index) => (
                <tr key={rowKey(row, offset + index)}>
                  {columns.map((column) => (
                    <td key={column.key}>{column.render ? column.render(row) : String(column.value(row) ?? '')}</td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="archdocDataTablePagination">
        <span>
          Page {safePage} of {totalPages} - {totalRows} rows
        </span>
        <div>
          <button type="button" disabled={safePage <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))}>
            Previous
          </button>
          <button type="button" disabled={safePage >= totalPages} onClick={() => setPage((value) => Math.min(totalPages, value + 1))}>
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
