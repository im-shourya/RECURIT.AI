"""
Security headers for every API response.

The API only ever returns JSON, redirects and file streams, so its policy can
be far stricter than a web page's: nothing it serves should run script, load
subresources or be framed. The exception is the interactive docs, which are
an HTML page that loads Swagger UI and ReDoc from a CDN.
"""

from starlette.types import ASGIApp, Message, Receive, Scope, Send

# Pages that render HTML and would break under the API's policy.
DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")

API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"

BASE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    # Candidate tokens travel in URL paths; never leak them in a Referer.
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}

# Two years, the value the HSTS preload list asks for. Only sent in
# production: over plain-HTTP localhost it would be ignored at best, and
# pinning a developer's browser to HTTPS for a local port at worst.
HSTS = "max-age=63072000; includeSubDomains"


def headers_for(path: str, production: bool) -> dict[str, str]:
    headers = dict(BASE_HEADERS)
    if not path.startswith(DOCS_PATHS):
        headers["Content-Security-Policy"] = API_CSP
    if production:
        headers["Strict-Transport-Security"] = HSTS
    return headers


class SecurityHeadersMiddleware:
    """
    Pure ASGI rather than BaseHTTPMiddleware, so streamed responses (file
    downloads, CSV export) are not buffered to add a few headers.

    Headers a route set itself are left alone.
    """

    def __init__(self, app: ASGIApp, production: bool) -> None:
        self.app = app
        self.production = production

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        extra = headers_for(scope.get("path", ""), self.production)

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                raw = list(message.get("headers", []))
                present = {name.lower() for name, _ in raw}
                for name, value in extra.items():
                    if name.lower().encode() not in present:
                        raw.append((name.encode(), value.encode()))
                message["headers"] = raw
            await send(message)

        await self.app(scope, receive, send_with_headers)
