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
import SignIn from './routes/signin';
import SignInRequired from './components/AuthRequired';

import './index.css';
import { AuthProvider } from './context/AuthProvider';
import Setup from './routes/setup';

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
            element: <SignInRequired />,
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
                path: "servers/:type/:serverId/:tab?/*",
                element: <Server />,
              },
              {
                path: "dashboard",
                element: <Dashboard />,
              },
            ],
          },
          {
            path: "signin",
            element: <SignIn />,
          },
          {
            path: "*",
            element: <ErrorPage title="Page not Found" subtitle="That page doesn't seem to exist. Let me check the back." />,
          },
        ],
      },
    ],
  },
  {
    path: "setup",
    element: <Setup />,
  },
], {
  future: {
    v7_relativeSplatPath: true,
  },
});

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
      <AuthProvider>
        <RouterProvider router={router} />
        <ReactQueryDevtools />
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
