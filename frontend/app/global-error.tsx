'use client'

export default function GlobalError({
  error,
}: {
  error: Error & { digest?: string }
}) {
  // Log the error to the console so it will be forwarded to server logs
  console.error(error)

  return (
    <html>
      <head>
        <style>{`
          /* This page replaces the root layout, so the app's stylesheet is
             not loaded; the theme tokens are repeated here. */
          :root {
            --bg: #FBFBFD; --fg: #1D1D1F; --muted: #6E6E73; --ghost: rgb(29 29 31 / 0.06);
            --primary: #0B7A75; --primary-hover: #096560; --on-primary: #FFFFFF;
            --border: #D2D2D7; --hover: #EEEEF1;
          }
          @media (prefers-color-scheme: dark) {
            :root {
              --bg: #0B0B0C; --fg: #F5F5F7; --muted: #A1A1A6; --ghost: rgb(245 245 247 / 0.06);
              --primary: #2BC4B4; --primary-hover: #4FD3C5; --on-primary: #04201E;
              --border: #38383A; --hover: #2C2C2E;
            }
          }
          * { box-sizing: border-box; margin: 0; padding: 0; }
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', system-ui, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--fg);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
          }
          .error-container {
            max-width: 480px;
            text-align: center;
          }
          .error-code {
            font-size: 8rem;
            font-weight: 700;
            line-height: 1;
            letter-spacing: -0.04em;
            color: var(--ghost);
            margin-bottom: -1.5rem;
            user-select: none;
          }
          .error-title {
            font-size: 1.5rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            color: var(--fg);
            margin-bottom: 0.75rem;
          }
          .error-description {
            font-size: 1rem;
            line-height: 1.6;
            color: var(--muted);
            margin-bottom: 2rem;
            max-width: 360px;
            margin-left: auto;
            margin-right: auto;
          }
          .error-actions {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            align-items: center;
          }
          @media (min-width: 640px) {
            .error-actions {
              flex-direction: row;
              justify-content: center;
            }
          }
          .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            height: 44px;
            padding: 0 24px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            font-family: inherit;
            cursor: pointer;
            transition: all 150ms ease;
            text-decoration: none;
            border: none;
            min-width: 140px;
          }
          .btn-primary {
            background: var(--primary);
            color: var(--on-primary);
          }
          .btn-primary:hover {
            background: var(--primary-hover);
          }
          .btn-secondary {
            background: transparent;
            color: var(--fg);
            border: 1px solid var(--border);
          }
          .btn-secondary:hover {
            background: var(--hover);
          }
        `}</style>
      </head>
      <body>
        <div className="error-container">
          <div className="error-code">500</div>
          <h1 className="error-title">Something went wrong</h1>
          <p className="error-description">
            An unexpected error occurred. Please try refreshing the page.
          </p>
          <div className="error-actions">
            <button
              className="btn btn-primary"
              onClick={() => window.location.reload()}
            >
              Try again
            </button>
            <a href="/" className="btn btn-secondary">
              Go to the home page
            </a>
          </div>
        </div>
      </body>
    </html>
  )
}
