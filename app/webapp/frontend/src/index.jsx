import React from 'react';
import ReactDOM from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

import 'bootstrap/dist/css/bootstrap.min.css'

import Root from './root';
import ErrorPage, { ResponseError } from './errors';

import Server from './routes/server';
import Dashboard from './routes/dashboard';

import './index.css';

// TODO seperate some sub-routes into seperate files because this will probably get really big otherwise
const router = createBrowserRouter([
  {
    path: "/",
    element: <Root />,
    children: [
      {
        errorElement: <ErrorPage />,
        // TODO better way to handle nested path with common prefix? can't use children because that would render all elements above it...
        children: [
          {
            path: "servers",
            element: <Dashboard />,
          },
          {
            path: "servers/:type",
            element: <div>nothing here...</div>,
          },
          {
            path: "servers/:type/:serverId",
            element: <Server />
          },
          {
            path: "dashboard",
            element: <Dashboard />
          },
          {
            path: "signin",
            element: <p>No actual sign in page yet...</p>
          },
          {
            path: "*",
            element: <ErrorPage title="Page not Found" subtitle="That page doesn't seem to exist. Let me check the back." />
          }
        ]
      },
    ],
  },
])

const query = new QueryClient({
  defaultOptions: {
    queries: {
      // This function stops retries from happening if it was a bad response,
      // for example a 404 or 500, but the actual request succeeded
      retry: (failureCount, error) => {
        return !(error instanceof ResponseError || failureCount >= 2);
      }
    }
  }
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <QueryClientProvider client={query}>
      <RouterProvider router={router} />
      <ReactQueryDevtools />
    </QueryClientProvider>
  </React.StrictMode>
);
