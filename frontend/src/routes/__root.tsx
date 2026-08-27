import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { type ReactNode } from "react";
import { Toaster } from "sonner";

import appCss from "../styles.css?url";

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="font-mono text-6xl font-bold text-emerald-500">404</h1>
        <h2 className="mt-4 font-display text-xl font-semibold text-foreground">
          Intelligence Record Not Found
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          The requested intelligence dossier or node does not exist or has been reclassified.
        </p>
        <div className="mt-6">
          <Link
            to="/dashboard"
            className="inline-flex items-center justify-center rounded-md bg-emerald-600 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-white transition-colors hover:bg-emerald-500"
          >
            Return to Command Center
          </Link>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error("NetraGraph UI Error:", error);
  const router = useRouter();

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md rounded-xl border border-border bg-card p-6 text-center shadow-2xl">
        <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-red-500/10 text-red-400">
          <span className="font-mono text-xl font-bold">!</span>
        </div>
        <h1 className="mt-4 font-display text-lg font-bold text-foreground">
          System Exception Intercepted
        </h1>
        <p className="mt-2 text-xs text-muted-foreground">
          A runtime state conflict occurred. Telemetry recorded for review.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="inline-flex items-center justify-center rounded-md bg-emerald-600 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-white transition-colors hover:bg-emerald-500"
          >
            Re-initialize Console
          </button>
          <a
            href="/dashboard"
            className="inline-flex items-center justify-center rounded-md border border-border bg-secondary/50 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-foreground transition-colors hover:bg-secondary"
          >
            Command Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "NetraGraph AI — Criminal Network Analysis & Investigative Intelligence System" },
      {
        name: "description",
        content:
          "NetraGraph AI is a professional criminal network analysis, link intelligence, and investigative command system for intelligence analysts and law enforcement agencies.",
      },
      { property: "og:title", content: "NetraGraph AI — Criminal Network Analysis & Investigative Intelligence System" },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
    links: [
      {
        rel: "stylesheet",
        href: appCss,
      },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap",
      },
      { rel: "icon", href: "/favicon.svg", type: "image/svg+xml" },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body className="bg-background text-foreground antialiased selection:bg-emerald-600/20 selection:text-emerald-900">
        {children}
        <Toaster
          position="bottom-right"
          toastOptions={{
            style: {
              background: "#FFFFFF",
              border: "1px solid #D9E2EC",
              color: "#0F172A",
              fontFamily: "Inter, sans-serif",
              fontSize: "13px",
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.08)",
            },
          }}
        />
        <Scripts />
      </body>
    </html>
  );
}

import { ThemeProvider } from "@/lib/theme";

function RootComponent() {
  const { queryClient } = Route.useRouteContext();

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <Outlet />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
