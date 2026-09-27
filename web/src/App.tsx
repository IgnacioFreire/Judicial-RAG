import { Route, Routes } from "react-router"

import { AppShell } from "@/components/AppShell"
import { DocumentDetailPage } from "@/pages/DocumentDetail"
import { DocumentsPage } from "@/pages/Documents"
import { OverviewPage } from "@/pages/Overview"
import { SettingsPage } from "@/pages/Settings"
import { WorkspaceProvider } from "@/workspace"

export default function App() {
  return (
    <WorkspaceProvider>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<OverviewPage />} />
          <Route path="documents" element={<DocumentsPage />} />
          <Route path="documents/:name" element={<DocumentDetailPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </WorkspaceProvider>
  )
}
