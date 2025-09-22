{
  "task": "Repository cleanup and code quality improvement for email helper project",
  "summary": "Systematic cleanup and refactoring to improve maintainability, reduce technical debt, and modernize codebase architecture",
  "groups": [
    {
      "id": "G1",
      "title": "Documentation & Standards Cleanup",
      "description": "Fix documentation issues, standardize formatting, and improve code consistency across the project",
      "inputs": ["task files", "markdown docs", "Python source files", "linting rules"],
      "outputs": ["clean markdown files", "standardized code format", "updated documentation", "style guide compliance"],
      "acceptance": [
        "All markdown linting errors resolved", 
        "Python code follows PEP 8 standards",
        "Consistent docstring format across modules",
        "Updated README and technical documentation"
      ],
      "dependencies": [],
      "priority": "medium",
      "skills": ["documentation", "markdown", "python-formatting", "technical-writing"],
      "coordination": {
        "type": "artifact",
        "artifact": "style_guide.md",
        "when": "on-complete"
      }
    },
    {
      "id": "G2", 
      "title": "Code Quality & Dead Code Elimination",
      "description": "Remove unused code, fix imports, eliminate duplication, and improve error handling patterns",
      "inputs": ["Python source files", "static analysis tools", "import dependency graph"],
      "outputs": ["cleaned source files", "removal report", "improved error handling", "reduced complexity metrics"],
      "acceptance": [
        "No unused imports or dead code",
        "Duplicate code consolidated into utilities", 
        "Consistent error handling patterns",
        "Warning messages standardized"
      ],
      "dependencies": [],
      "priority": "high",
      "skills": ["python", "static-analysis", "refactoring", "code-cleanup"],
      "coordination": {
        "type": "artifact", 
        "artifact": "cleanup_report.json",
        "when": "on-complete"
      }
    },
    {
      "id": "G3",
      "title": "Architecture Refactoring & Modularization", 
      "description": "Break down monolithic components, extract service layers, and improve module organization",
      "inputs": ["unified_gui.py", "component architecture", "service layer patterns"],
      "outputs": ["modular GUI components", "service layer abstractions", "improved separation of concerns", "refactored utilities"],
      "acceptance": [
        "GUI components properly separated",
        "Business logic extracted from UI",
        "Clear module boundaries established",
        "Utility functions consolidated"
      ],
      "dependencies": ["G2"],
      "priority": "high", 
      "skills": ["python", "architecture", "refactoring", "design-patterns"],
      "coordination": {
        "type": "integration",
        "artifact": "refactored_modules",
        "when": "post-G2"
      }
    },
    {
      "id": "G4",
      "title": "Testing & Quality Assurance Enhancement",
      "description": "Improve test coverage, remove obsolete tests, and implement automated quality checks", 
      "inputs": ["existing test suite", "coverage reports", "CI configuration"],
      "outputs": ["enhanced test coverage", "automated quality gates", "integration test suite", "CI pipeline improvements"],
      "acceptance": [
        "Test coverage above 80% for core modules",
        "All obsolete tests removed or updated", 
        "Integration tests for critical workflows",
        "Automated quality checks in CI"
      ],
      "dependencies": ["G1", "G2", "G3"],
      "priority": "medium",
      "skills": ["testing", "pytest", "ci-cd", "quality-assurance"],
      "coordination": {
        "type": "validation",
        "artifact": "test_results.json", 
        "when": "final-validation"
      }
    }
  ],
  "orchestration": {
    "coordinator_agent": "Quality Assurance Lead",
    "sync_points": [
      {
        "after": "G1",
        "before": "G3", 
        "action": "style-standards-review"
      },
      {
        "after": "G2",
        "before": "G3",
        "action": "code-cleanup-validation"
      },
      {
        "after": "G3", 
        "before": "G4",
        "action": "architecture-integration-test"
      }
    ]
  }
}