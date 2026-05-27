'use client';

import { CnfExplorerProvider } from './CnfExplorerContext';
import { CnfExplorerToolbar } from './CnfExplorerToolbar';

export function CnfExplorerShell({ children }: { children: React.ReactNode }) {
  return (
    <CnfExplorerProvider>
      <CnfExplorerToolbar />
      {children}
    </CnfExplorerProvider>
  );
}
