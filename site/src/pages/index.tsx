import type {ReactNode} from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

const workspaceLinks = [
  {
    title: 'API Endpoints',
    text: 'Review generated FastAPI routes, linkage coverage, response models, parameters, and source locations.',
    to: '/docs/architecture/generated/api-endpoints',
  },
  {
    title: 'Interfaces',
    text: 'Inspect endpoint-to-service links and mark generated matches for follow-up review.',
    to: '/docs/architecture/generated/interfaces',
  },
  {
    title: 'Operations',
    text: 'Browse service operations, endpoint coverage, generated status, and overlay review markers.',
    to: '/docs/architecture/generated/operations',
  },
  {
    title: 'Validation',
    text: 'Triage direct DB access, unlinked endpoints, duplicate IDs, and architectural warnings.',
    to: '/docs/architecture/generated/validation',
  },
];

export default function Home(): ReactNode {
  return (
    <Layout
      title="Archdoc Review Workspace"
      description="Editable architecture catalog review workspace for generated archdoc JSON.">
      <main className={styles.workspace}>
        <section className={styles.hero}>
          <div className={styles.heroInner}>
            <p className={styles.kicker}>Utilis architecture documentation</p>
            <Heading as="h1">Archdoc Review Workspace</Heading>
            <p className={styles.lede}>
              Generated architecture facts stay deterministic. Human review,
              labels, and status markers live in overlays managed by the
              separate UI backend.
            </p>
            <div className={styles.actions}>
              <Link className="button button--primary" to="/docs/architecture/generated/api-endpoints">
                Open Endpoint Review
              </Link>
              <Link className="button button--secondary" to="/docs/architecture/generated/validation">
                Open Validation
              </Link>
            </div>
          </div>
        </section>

        <section className={styles.grid} aria-label="Archdoc review areas">
          {workspaceLinks.map((item) => (
            <Link className={styles.tile} to={item.to} key={item.to}>
              <Heading as="h2">{item.title}</Heading>
              <p>{item.text}</p>
            </Link>
          ))}
        </section>
      </main>
    </Layout>
  );
}
