"""
Dependency analyzer - parses common manifest files without any API calls.
Extracts frameworks, libraries, and languages to enrich LLM context.
"""
import json
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Set

try:
    import tomllib  # Python 3.11+
except Exception:
    tomllib = None


class DependencyAnalyzer:
    """Parse dependency files to infer frameworks, libraries, and languages."""

    JS_FRAMEWORKS = {
        "react", "vue", "angular", "svelte", "next", "nuxt",
        "express", "nestjs", "koa", "fastify", "electron"
    }
    PY_FRAMEWORKS = {
        "django", "flask", "fastapi", "tornado", "pyramid",
        "streamlit", "dash"
    }
    JAVA_FRAMEWORKS = {"spring", "spring-boot", "quarkus", "micronaut"}
    GO_FRAMEWORKS = {"gin", "echo", "fiber", "chi"}
    RUST_FRAMEWORKS = {"actix-web", "rocket", "axum", "warp"}

    def analyze_dependencies(self, file_contents: Dict[str, str]) -> Dict[str, List[str]]:
        frameworks: Set[str] = set()
        libraries: Set[str] = set()
        languages: Set[str] = set()

        for path, content in file_contents.items():
            lower_path = path.lower()

            if lower_path.endswith("package.json"):
                languages.update(["JavaScript", "TypeScript"])
                deps = self._parse_package_json(content)
                self._classify_js(deps, frameworks, libraries)

            elif lower_path.endswith("requirements.txt"):
                languages.add("Python")
                deps = self._parse_requirements_txt(content)
                self._classify_python(deps, frameworks, libraries)

            elif lower_path.endswith("pom.xml"):
                languages.add("Java")
                deps = self._parse_pom_xml(content)
                self._classify_java(deps, frameworks, libraries)

            elif lower_path.endswith("go.mod"):
                languages.add("Go")
                deps = self._parse_go_mod(content)
                self._classify_go(deps, frameworks, libraries)

            elif lower_path.endswith("cargo.toml"):
                languages.add("Rust")
                deps = self._parse_cargo_toml(content)
                self._classify_rust(deps, frameworks, libraries)

        return {
            "frameworks": sorted(frameworks),
            "libraries": sorted(libraries),
            "languages": sorted(languages)
        }

    def _parse_package_json(self, content: str) -> Set[str]:
        try:
            data = json.loads(content)
        except Exception:
            return set()
        deps = set()
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            if isinstance(data.get(key), dict):
                deps.update(data[key].keys())
        return {d.lower() for d in deps}

    def _parse_requirements_txt(self, content: str) -> Set[str]:
        deps = set()
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            name = re.split(r"[<=>!~\[]", line, maxsplit=1)[0].strip()
            if name:
                deps.add(name.lower())
        return deps

    def _parse_pom_xml(self, content: str) -> Set[str]:
        deps = set()
        try:
            root = ET.fromstring(content)
        except Exception:
            return deps
        for dep in root.findall(".//{*}dependency/{*}artifactId"):
            if dep.text:
                deps.add(dep.text.strip().lower())
        return deps

    def _parse_go_mod(self, content: str) -> Set[str]:
        deps = set()
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("module") or line.startswith("//"):
                continue
            if line.startswith("require"):
                line = line.replace("require", "", 1).strip()
            if line.startswith("(") or line.startswith(")"):
                continue
            parts = line.split()
            if parts:
                deps.add(parts[0].lower())
        return deps

    def _parse_cargo_toml(self, content: str) -> Set[str]:
        if not tomllib:
            return set()
        try:
            data = tomllib.loads(content)
        except Exception:
            return set()
        deps = set()
        for key in ("dependencies", "dev-dependencies", "build-dependencies"):
            section = data.get(key, {})
            if isinstance(section, dict):
                deps.update(section.keys())
        return {d.lower() for d in deps}

    def _classify_js(self, deps: Set[str], frameworks: Set[str], libraries: Set[str]) -> None:
        for dep in deps:
            if dep in self.JS_FRAMEWORKS:
                frameworks.add(dep)
            else:
                libraries.add(dep)

    def _classify_python(self, deps: Set[str], frameworks: Set[str], libraries: Set[str]) -> None:
        for dep in deps:
            if dep in self.PY_FRAMEWORKS:
                frameworks.add(dep)
            else:
                libraries.add(dep)

    def _classify_java(self, deps: Set[str], frameworks: Set[str], libraries: Set[str]) -> None:
        for dep in deps:
            if dep in self.JAVA_FRAMEWORKS or dep.startswith("spring"):
                frameworks.add(dep)
            else:
                libraries.add(dep)

    def _classify_go(self, deps: Set[str], frameworks: Set[str], libraries: Set[str]) -> None:
        for dep in deps:
            name = dep.split("/")[-1]
            if name in self.GO_FRAMEWORKS:
                frameworks.add(name)
            else:
                libraries.add(name)

    def _classify_rust(self, deps: Set[str], frameworks: Set[str], libraries: Set[str]) -> None:
        for dep in deps:
            if dep in self.RUST_FRAMEWORKS:
                frameworks.add(dep)
            else:
                libraries.add(dep)
