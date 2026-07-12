import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const config: Config = {
  title: 'Archdoc',
  tagline: 'Deterministic architecture catalog review',
  future: {
    v4: true,
  },

  url: 'https://teamprojekt.docs.kevinkraft.de',
  baseUrl: '/',

  organizationName: 'utilis',
  projectName: 'archdoc',

  onBrokenLinks: 'throw',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      logo: {
        alt: 'Archdoc',
        src: 'img/archdoc-logo.png',
      },
      items: [
        {
          to: '/',
          label: 'Workspace',
          position: 'left',
          activeBaseRegex: '^/$',
        },
        {
          type: 'docSidebar',
          sidebarId: 'architectureSidebar',
          position: 'left',
          label: 'Architecture',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {
              label: 'Architecture Overview',
              to: '/docs/architecture/overview',
            },
            {
              label: 'Data Dictionary',
              to: '/docs/architecture/data-dictionary',
            },
          ],
        },
        {
          title: 'Review',
          items: [
            {
              label: 'API Endpoints',
              to: '/docs/architecture/generated/api-endpoints',
            },
            {
              label: 'Validation',
              to: '/docs/architecture/generated/validation',
            },
          ],
        },
      ],
      copyright: `Copyright (c) ${new Date().getFullYear()} Kevin Kraft · Licensed under the Apache License 2.0 · Developed as part of the IBU seminar project.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
