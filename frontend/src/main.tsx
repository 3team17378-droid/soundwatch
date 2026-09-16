import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, Guard } from "./auth";
import {
  AuditPage,
  AuthPage,
  Dashboard,
  Detail,
  Landing,
  Layout,
  NotFound,
  Progress,
  Records,
  SystemPage,
  Upload,
  UsersPage,
} from "./pages";
import { MapPage } from "./map";
import "./styles.css";
const client = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<AuthPage />} />
            <Route path="/register" element={<AuthPage register />} />
            <Route element={<Guard />}>
              <Route path="/app" element={<Layout />}>
                <Route index element={<Dashboard />} />
                <Route path="upload" element={<Upload />} />
                <Route path="records" element={<Records />} />
                <Route path="records/:id" element={<Detail />} />
                <Route path="jobs/:id" element={<Progress />} />
                <Route path="map" element={<MapPage />} />
                <Route path="statistics" element={<Dashboard statistics />} />
                <Route element={<Guard admin />}>
                  <Route path="admin/reviews" element={<Records admin />} />
                  <Route path="admin/reviews/:id" element={<Detail admin />} />
                  <Route path="admin/users" element={<UsersPage />} />
                  <Route path="admin/audit" element={<AuditPage />} />
                  <Route path="admin/system" element={<SystemPage />} />
                </Route>
                <Route path="*" element={<NotFound />} />
              </Route>
            </Route>
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
