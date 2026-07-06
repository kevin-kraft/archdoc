import React from 'react';

type SourceRef = {
  file?: string;
  line_start?: number;
};

type ActionLike = {
  id?: string;
  kind?: string;
  resource?: string;
  entity?: string;
  call_name?: string;
  action?: string;
  access?: string;
  query?: any;
  source?: SourceRef;
};

export function DetailBlock({title, children}: {title: string; children: React.ReactNode}) {
  return (
    <section className="archdocDetailBlock">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

export function DetailItem({label, value}: {label: string; value?: unknown}) {
  if (value === undefined || value === null || value === '') {
    return null;
  }

  return (
    <>
      <dt>{label}</dt>
      <dd>{String(value)}</dd>
    </>
  );
}

export function OperationActionSequence({
  actions,
  title,
}: {
  actions: ActionLike[];
  title: string;
}) {
  const visibleActions = [...actions]
    .filter((action) => action.kind !== 'type_usage')
    .sort((left, right) => (left.source?.line_start ?? 0) - (right.source?.line_start ?? 0))
    .slice(0, 18);

  if (!visibleActions.length) {
    return <DetailBlock title={title}><p className="archdocMuted">No actions detected.</p></DetailBlock>;
  }

  return (
    <DetailBlock title={title}>
      <ol className="archdocInspectorSequence">
        {visibleActions.map((action) => (
          <li key={action.id ?? `${action.kind}-${actionLabel(action)}`}>
            <strong>{labelForActionKind(action.kind ?? 'action')}</strong>
            <span>{actionLabel(action)}</span>
            <small>{sourceLabel(action.source)}</small>
          </li>
        ))}
      </ol>
    </DetailBlock>
  );
}

export function OperationTypeUsageList({actions}: {actions: ActionLike[]}) {
  const typeActions = [...actions]
    .filter((action) => action.kind === 'type_usage')
    .sort((left, right) => (left.source?.line_start ?? 0) - (right.source?.line_start ?? 0));

  if (!typeActions.length) {
    return null;
  }

  const uniqueTypes = Array.from(
    new Map(typeActions.map((action) => [action.resource ?? action.entity ?? action.call_name ?? action.id, action])).values(),
  ).slice(0, 12);

  return (
    <DetailBlock title="Type Usage">
      <div className="archdocInspectorTokenList">
        {uniqueTypes.map((action) => (
          <span key={action.id ?? `${action.resource}-${action.source?.line_start ?? ''}`}>
            <strong>{action.resource ?? action.entity ?? action.call_name}</strong>
            <small>{sourceLabel(action.source)}</small>
          </span>
        ))}
      </div>
    </DetailBlock>
  );
}

export function QueryDetails({query}: {query: any}) {
  return (
    <>
      <DetailBlock title="Query">
        <dl className="archdocDetailsList">
          <DetailItem label="Variable" value={query.variable} />
          <DetailItem label="Operation" value={query.operation} />
          <DetailItem label="Entities" value={(query.entities ?? []).join(', ')} />
          <DetailItem label="Limit" value={query.limit} />
        </dl>
        <pre className="archdocCodeBlock">{query.expression}</pre>
      </DetailBlock>
      <QueryPartList title="Filters" values={query.filters} />
      <QueryPartList title="Joins" values={query.joins} />
      <QueryPartList title="Ordering" values={query.ordering} />
      {Array.isArray(query.entity_details) && query.entity_details.length ? (
        <>
          {query.entity_details.map((entity: any) => (
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
        </>
      ) : null}
    </>
  );
}

export function QueryPartList({title, values}: {title: string; values?: string[]}) {
  const items = Array.isArray(values) ? values.filter(Boolean) : [];

  return (
    <DetailBlock title={title}>
      {items.length ? (
        <ul className="archdocQueryPartList">
          {items.map((item, index) => (
            <li key={`${title}-${index}`}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="archdocMuted">None detected.</p>
      )}
    </DetailBlock>
  );
}

export function EntityFieldTable({fields}: {fields: any[]}) {
  if (!fields.length) {
    return <p className="archdocMuted">No mapped fields detected.</p>;
  }

  return (
    <div className="archdocEntityFieldTableWrap">
      <table className="archdocEntityFieldTable">
        <thead>
          <tr>
            <th>Field</th>
            <th>Type</th>
            <th>Mapping</th>
          </tr>
        </thead>
        <tbody>
          {fields.map((field) => (
            <tr key={`${field.name}-${field.source?.line_start ?? ''}`}>
              <td>{field.name}</td>
              <td>{field.annotation ?? ''}</td>
              <td>{field.value_call ?? field.value ?? ''}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function actionLabel(action: ActionLike) {
  const base = action.query
    ? queryLabel(action.query)
    : action.resource ?? action.entity ?? action.call_name ?? action.action ?? action.kind ?? 'action';

  if (action.kind === 'database_action') {
    return compactLabel(`${databaseActionVerb(action)} ${base}`);
  }

  if (action.kind === 'database_transaction') {
    return compactLabel(action.resource ?? action.action ?? action.call_name ?? 'transaction');
  }

  return compactLabel(base);
}

export function labelForActionKind(kind: string) {
  return kind.replace(/_/g, ' ');
}

export function sourceLabel(source?: SourceRef) {
  if (!source?.file) {
    return undefined;
  }

  return `${source.file}${source.line_start ? `:${source.line_start}` : ''}`;
}

function databaseActionVerb(action: ActionLike) {
  const callName = String(action.call_name ?? '');

  if (callName.endsWith('.get')) return 'get';
  if (callName.endsWith('.execute')) return 'execute';
  if (callName.endsWith('.add')) return 'add';
  if (callName.endsWith('.delete')) return 'delete';

  if (action.action === 'read') return 'read';
  if (action.action === 'create') return 'create';
  if (action.action === 'update') return 'update';
  if (action.action === 'delete') return 'delete';

  return action.action ?? 'db';
}

function queryLabel(query: any) {
  const operation = query.operation ?? 'query';
  const entities = Array.isArray(query.entities) && query.entities.length
    ? ` ${query.entities.slice(0, 3).join(', ')}`
    : '';
  const filters = Array.isArray(query.filters) && query.filters.length
    ? ` where ${query.filters.slice(0, 2).join(' && ')}`
    : '';

  return `${operation}${entities}${filters}`;
}

function compactLabel(value: string) {
  if (value.length <= 72) return value;
  return `${value.slice(0, 69)}...`;
}
