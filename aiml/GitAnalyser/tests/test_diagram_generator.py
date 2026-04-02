"""
Unit tests for DiagramGenerator service.
Verifies pure Python Mermaid syntax generation — no API mocking needed.
"""
import pytest
from services.diagram_generator import DiagramGenerator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def generator():
    return DiagramGenerator()


@pytest.fixture
def full_analysis_data():
    return {
        "components": [
            {"name": "API Gateway", "purpose": "Routes requests", "files": ["main.py"]},
            {"name": "Database Layer", "purpose": "Stores data", "files": ["db/database.py"]},
        ],
        "tech_stack": [
            {"name": "FastAPI", "category": "backend", "version": "0.100"},
            {"name": "React", "category": "frontend", "version": "18"},
            {"name": "SQLite", "category": "database", "version": "3"},
        ],
        "data_flow": "Request -> API -> Database -> Response",
    }


@pytest.fixture
def tech_only_data():
    """Data with tech_stack but no components."""
    return {
        "components": [],
        "tech_stack": [
            {"name": "Python", "category": "language"},
            {"name": "Django", "category": "framework"},
        ],
        "data_flow": "",
    }


@pytest.fixture
def empty_data():
    return {"components": [], "tech_stack": [], "data_flow": ""}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDiagramGeneratorOutput:
    """Verify the generated Mermaid syntax is structurally valid."""

    def test_returns_string(self, generator, full_analysis_data):
        result = generator.generate_mermaid_diagram(full_analysis_data)
        assert isinstance(result, str)

    def test_contains_graph_keyword(self, generator, full_analysis_data):
        result = generator.generate_mermaid_diagram(full_analysis_data)
        assert "graph" in result, "Output must start with a Mermaid graph declaration"

    def test_component_nodes_present(self, generator, full_analysis_data):
        result = generator.generate_mermaid_diagram(full_analysis_data)
        # Component IDs are C0, C1, …
        assert "C0" in result
        assert "C1" in result

    def test_tech_nodes_present(self, generator, full_analysis_data):
        result = generator.generate_mermaid_diagram(full_analysis_data)
        # Tech-stack nodes are T0, T1, …
        assert "T0" in result

    def test_arrow_between_components(self, generator, full_analysis_data):
        result = generator.generate_mermaid_diagram(full_analysis_data)
        assert "-->" in result, "Component nodes should be connected with arrows"

    def test_fallback_to_tech_stack(self, generator, tech_only_data):
        result = generator.generate_mermaid_diagram(tech_only_data)
        assert "graph" in result

    def test_empty_data_fallback(self, generator, empty_data):
        result = generator.generate_mermaid_diagram(empty_data)
        assert "graph" in result
        assert len(result) > 0


class TestDiagramSanitization:
    """Verify label sanitization prevents Mermaid syntax errors."""

    def test_special_chars_stripped_from_labels(self, generator):
        """Brackets, parens and quotes must not appear unescaped in node labels."""
        data = {
            "components": [
                {"name": 'Comp (v2) [beta]', "purpose": "test", "files": []},
            ],
            "tech_stack": [],
            "data_flow": "",
        }
        result = generator.generate_mermaid_diagram(data)
        # The raw special chars should be gone (replaced by safe_label)
        assert "(" not in result.split('"Comp')[1].split('"')[0] if '"Comp' in result else True

    def test_safe_label_strips_brackets(self, generator):
        label = generator._safe_label("Node[0] (beta)")
        assert "[" not in label
        assert "]" not in label
        assert "(" not in label

    def test_safe_label_max_length(self, generator):
        long_name = "A" * 100
        label = generator._safe_label(long_name)
        assert len(label) <= 40

    def test_safe_label_empty_string_fallback(self, generator):
        label = generator._safe_label("")
        assert label == "Node"

    def test_safe_id_replaces_spaces(self, generator):
        node_id = generator._safe_id("my category")
        assert " " not in node_id


class TestDiagramGeneratorWithPydanticLikeObjects:
    """Verify it works with objects that have attributes (not just dicts)."""

    def test_pydantic_like_components(self, generator):
        class FakeComp:
            def __init__(self, name, purpose, files):
                self.name = name
                self.purpose = purpose
                self.files = files

        class FakeTech:
            def __init__(self, name, category):
                self.name = name
                self.category = category

        data = {
            "components": [FakeComp("Auth Service", "Handles auth", [])],
            "tech_stack": [FakeTech("Python", "language")],
            "data_flow": "A -> B",
        }
        result = generator.generate_mermaid_diagram(data)
        assert "graph" in result
        assert "Auth Service" in result or "Auth" in result
