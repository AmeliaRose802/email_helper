# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) that document significant architectural decisions made in the Email Helper project.

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision along with its context and consequences. ADRs help future developers understand:
- Why certain architectural choices were made
- What alternatives were considered
- What trade-offs were accepted
- What constraints influenced the decision

## ADR Index

### Current ADRs

1. [ADR-001: Backend/Src Separation](ADR-001-backend-src-separation.md)
   - **Status**: Accepted
   - **Decision**: Maintain separate backend/ and src/ directories for FastAPI backend and legacy desktop app
   - **Context**: Support both modern web/mobile API and legacy desktop application

2. [ADR-002: Dependency Injection Pattern](ADR-002-dependency-injection-pattern.md)
   - **Status**: Accepted
   - **Decision**: Use FastAPI dependency injection for backend services
   - **Context**: Need testable, loosely coupled architecture with flexible provider selection

3. [ADR-003: Testing Strategy](ADR-003-testing-strategy.md)
   - **Status**: Accepted
   - **Decision**: Multi-layered testing with pytest markers for unit, integration, and E2E tests
   - **Context**: Complex application with multiple integration points requiring comprehensive test coverage

4. [ADR-004: Error Handling Approach](ADR-004-error-handling-approach.md)
   - **Status**: Accepted
   - **Decision**: Graceful degradation with fallback providers and consistent error responses
   - **Context**: Multiple service providers with varying availability and reliability

## ADR Format

Each ADR follows this structure:

```markdown
# ADR-XXX: Title

## Status
[Proposed | Accepted | Deprecated | Superseded by ADR-XXX]

## Context
What is the issue that we're seeing that motivates this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult to do because of this change?

## Alternatives Considered
What other options did we consider?

## Related Decisions
What other ADRs are related to this one?
```

## How to Create a New ADR

1. Copy the template from `ADR-template.md`
2. Number it sequentially (ADR-XXX)
3. Fill in all sections with relevant information
4. Submit for review as part of your PR
5. Update this index once approved

## Workflow

- **Proposed**: Initial state when ADR is drafted
- **Accepted**: Decision has been made and is being implemented
- **Deprecated**: No longer applicable but kept for historical reference
- **Superseded**: Replaced by a newer ADR

## Related Documentation

- [Code Quality Standards](../CODE_QUALITY_STANDARDS.md)
- [Dependency Injection README](../../backend/core/DEPENDENCY_INJECTION_README.md)
- [Test Organization](../../test/TEST_ORGANIZATION.md)

## Purpose

These ADRs serve to:
- Document the reasoning behind architectural decisions
- Prevent undoing good decisions due to lack of understanding
- Provide context for new developers joining the project
- Create a historical record of how the architecture evolved
- Enable informed discussion about future architectural changes
