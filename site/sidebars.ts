import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  architectureSidebar: [
    'architecture/overview',
    'architecture/data-dictionary',
    'architecture/raci-matrix',
    'architecture/payout-process',
    'architecture/utilis-handbook',
    {
      type: 'category',
      label: 'Generated Catalogs',
      items: [
        'architecture/generated/api-endpoints',
        'architecture/generated/interfaces',
        'architecture/generated/operations',
        'architecture/generated/service-actions',
        'architecture/generated/user-stories',
        'architecture/generated/validation',
      ],
    },
  ],
};

export default sidebars;
