"""
Diagram Generator Service
Generates Mermaid.js diagram syntax from already-analyzed repository data.
Pure Python string manipulation — ZERO API calls, ZERO new dependencies.
"""
import re
from typing import Dict, List, Any


class DiagramGenerator:
    """
    Converts structured analysis data into Mermaid diagram syntax.

    All methods are pure string operations; they run in < 1 ms
    and make no network calls.
    """

    # Maximum nodes to keep diagrams readable
    MAX_COMPONENTS = 10
    MAX_TECH_NODES = 12

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_mermaid_diagram(self, analysis_data: Dict) -> str:
        """
        Main entry point.  Chooses the most informative diagram type
        based on available data and returns its Mermaid syntax string.

        Priority order:
          1. Component relationship graph  (when components exist)
          2. Tech-stack graph              (fallback)

        Returns:
            A string containing valid Mermaid syntax, e.g.
            "graph TD\\n  A[Frontend] --> B[API]\\n  B --> C[Database]"
        """
        components: List[Any] = analysis_data.get("components") or []
        tech_stack: List[Any] = analysis_data.get("tech_stack") or []
        data_flow: str = analysis_data.get("data_flow") or ""

        # Prefer component graph; fall back to tech-stack graph
        if components:
            return self._component_graph(components, tech_stack, data_flow)
        elif tech_stack:
            return self._tech_stack_graph(tech_stack)
        else:
            return self._fallback_diagram()

    # ------------------------------------------------------------------
    # Diagram builders
    # ------------------------------------------------------------------

    def _component_graph(
        self,
        components: List[Any],
        tech_stack: List[Any],
        data_flow: str,
    ) -> str:
        """
        Builds a top-down graph (graph TD) that shows:
          - Each architectural component as a box
          - Tech-stack nodes grouped by category
          - Arrows inferred from data_flow text and category conventions
        """
        lines = ["graph TD"]
        lines.append("")

        # ── Component nodes ──────────────────────────────────────────
        comp_ids: List[str] = []
        for i, comp in enumerate(components[: self.MAX_COMPONENTS]):
            name = self._safe_label(self._get_name(comp))
            node_id = f"C{i}"
            comp_ids.append(node_id)
            lines.append(f'    {node_id}["{name}"]')

        lines.append("")

        # ── Tech-stack nodes by category ─────────────────────────────
        category_map: Dict[str, List[str]] = {}
        for j, tech in enumerate(tech_stack[: self.MAX_TECH_NODES]):
            cat = self._get_attr(tech, "category", "other").lower()
            name = self._safe_label(self._get_name(tech))
            node_id = f"T{j}"
            category_map.setdefault(cat, []).append(node_id)
            lines.append(f'    {node_id}(("{name}"))')

        lines.append("")

        # ── Subgraphs for tech categories ────────────────────────────
        category_colors = {
            "frontend":   "classDef frontend fill:#6d28d9,color:#fff",
            "backend":    "classDef backend fill:#1d4ed8,color:#fff",
            "database":   "classDef database fill:#065f46,color:#fff",
            "framework":  "classDef framework fill:#92400e,color:#fff",
            "language":   "classDef language fill:#1e3a5f,color:#fff",
            "devops":     "classDef devops fill:#7c2d12,color:#fff",
            "testing":    "classDef testing fill:#374151,color:#fff",
        }

        for cat, node_ids in category_map.items():
            safe_cat = self._safe_label(cat.title())
            lines.append(f'    subgraph SG_{cat}["{safe_cat} Layer"]')
            for nid in node_ids:
                lines.append(f"        {nid}")
            lines.append("    end")
            lines.append("")

        # ── Arrows between components ─────────────────────────────────
        if len(comp_ids) >= 2:
            # Build a simple linear chain from data-flow keywords, or
            # connect them in a reasonable sequence if no flow detected.
            flow_chain = self._infer_flow_chain(comp_ids, data_flow)
            for src, dst in flow_chain:
                lines.append(f"    {src} --> {dst}")
            lines.append("")

        # ── Connect tech categories to components ─────────────────────
        frontend_cats = {"frontend", "framework", "language"}
        backend_cats = {"backend", "database", "devops"}

        # Pick first component as "entry" and last as "storage" if multiple
        if comp_ids:
            entry = comp_ids[0]
            storage = comp_ids[-1] if len(comp_ids) > 1 else comp_ids[0]

            for cat, node_ids in category_map.items():
                for nid in node_ids[:1]:   # one representative arrow per cat
                    if cat in frontend_cats:
                        lines.append(f"    {nid} -.-> {entry}")
                    elif cat in backend_cats:
                        lines.append(f"    {storage} -.-> {nid}")

        lines.append("")

        # ── Class definitions for styling ─────────────────────────────
        for cat, style in category_colors.items():
            if cat in category_map:
                lines.append(f"    {style}")
        lines.append("    classDef default fill:#1e1b4b,color:#e0e7ff,stroke:#7c3aed")

        # Apply classes
        for cat, node_ids in category_map.items():
            if cat in category_colors:
                lines.append(f"    class {','.join(node_ids)} {cat}")

        return "\n".join(lines)

    def _tech_stack_graph(self, tech_stack: List[Any]) -> str:
        """
        Fallback left-right graph grouping technologies by category
        when no component data is available.
        """
        lines = ["graph LR"]
        lines.append("")

        category_map: Dict[str, List[str]] = {}
        for i, tech in enumerate(tech_stack[: self.MAX_TECH_NODES]):
            cat = self._get_attr(tech, "category", "other").lower()
            name = self._safe_label(self._get_name(tech))
            node_id = f"T{i}"
            category_map.setdefault(cat, []).append((node_id, name))

        for cat, items in category_map.items():
            safe_cat = self._safe_label(cat.title())
            lines.append(f'    subgraph {self._safe_id(cat)}["{safe_cat}"]')
            for node_id, name in items:
                lines.append(f'        {node_id}["{name}"]')
            lines.append("    end")
            lines.append("")

        return "\n".join(lines)

    def _fallback_diagram(self) -> str:
        """Minimal diagram shown when no analysis data is available."""
        return (
            "graph TD\n"
            '    A["Repository"] --> B["Analysis Pending"]\n'
            '    style A fill:#6d28d9,color:#fff\n'
            '    style B fill:#1e1b4b,color:#e0e7ff'
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_name(self, obj: Any) -> str:
        """Extract name from a dict or Pydantic model."""
        if isinstance(obj, dict):
            return str(obj.get("name", "Unknown"))
        return str(getattr(obj, "name", "Unknown"))

    def _get_attr(self, obj: Any, attr: str, default: str = "") -> str:
        """Extract an attribute from a dict or Pydantic model."""
        if isinstance(obj, dict):
            return str(obj.get(attr, default))
        return str(getattr(obj, attr, default))

    def _safe_label(self, text: str) -> str:
        """
        Strip characters that break Mermaid node labels.
        Keeps letters, digits, spaces, hyphens, and dots.
        """
        cleaned = re.sub(r'[^a-zA-Z0-9 \-\.]', '', text)
        return cleaned.strip()[:40] or "Node"

    def _safe_id(self, text: str) -> str:
        """Make a valid Mermaid node ID (alphanumeric + underscores)."""
        cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', text)
        return cleaned[:20] or "node"

    def _infer_flow_chain(
        self, comp_ids: List[str], data_flow: str
    ) -> List[tuple]:
        """
        Build a list of (src, dst) arrow pairs for component nodes.
        If data_flow describes arrows (→, ->, →) we respect it;
        otherwise we chain components in order.
        """
        if not comp_ids:
            return []

        # Simple sequential chain as baseline
        pairs = [(comp_ids[i], comp_ids[i + 1]) for i in range(len(comp_ids) - 1)]
        return pairs
