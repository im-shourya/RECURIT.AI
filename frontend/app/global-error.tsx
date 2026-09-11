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
          * { box-sizing: border-box; margin: 0; padding: 0; }
          body {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: #F7F8F7;
            color: #171A1F;
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
            color: rgba(23, 26, 31, 0.05);
            margin-bottom: -1.5rem;
            user-select: none;
          }
          .error-title {
            font-size: 1.5rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            color: #171A1F;
            margin-bottom: 0.75rem;
          }
          .error-description {
            font-size: 1rem;
            line-height: 1.6;
            color: #5F6670;
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
            border-radius: 8px;
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
            background: #2C52BA;
            color: #ffffff;
          }
          .btn-primary:hover {
            background: #2449A6;
          }
          .btn-secondary {
            background: transparent;
            color: #171A1F;
            border: 1px solid #D7DCE2;
          }
          .btn-secondary:hover {
            background: rgba(162, 171, 195, 0.2);
          }
        `}</style>
      </head>
      <body>
        <div className="error-container">
          <div className="error-code">500</div>
          <h1 className="error-title">Something Went Wrong</h1>
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
              Go to Dashboard
            </a>
          </div>
        </div>
      </body>
    </html>
  )
}
