# Email Helper - Code Quality & Documentation Standards

## 📋 Overview

This guide establishes the coding standards and documentation practices for the Email Helper project. Following these guidelines ensures consistency, maintainability, and AI-friendliness across the codebase.

---

## 🐍 Python Standards

### Module Documentation

Every Python module must start with a comprehensive docstring:

```python
#!/usr/bin/env python3
"""Module Title - Brief Description.

Comprehensive module description explaining:
- What this module does
- Key responsibilities and features
- How it integrates with other modules
- Important algorithms or patterns used

The module handles:
- Feature 1 with explanation
- Feature 2 with explanation
- Feature 3 with explanation

Key Features:
- Feature detail 1
- Feature detail 2
- Feature detail 3

Dependencies:
    - library1: Purpose of this dependency
    - library2: Purpose of this dependency
    - library3: Purpose of this dependency

Example Usage:
    >>> from module_name import ClassName
    >>> instance = ClassName()
    >>> result = instance.method()
    >>> print(result)

Author: Team Name
Version: X.Y.Z
Last Updated: YYYY-MM-DD
"""
```

### Class Documentation

```python
class ClassName:
    """Brief one-line description of the class.
    
    Detailed description explaining:
    - Class purpose and responsibility
    - Design patterns used
    - Integration points
    - Thread safety considerations
    - Performance characteristics
    
    The class handles:
    - Responsibility 1
    - Responsibility 2
    - Responsibility 3
    
    Attributes:
        attribute_name (type): Description of attribute.
            Additional context if needed.
        another_attr (type, optional): Description with default value.
    
    Thread Safety:
        Specify if thread-safe or not, and any restrictions.
    
    Performance Considerations:
        - Note any performance-critical aspects
        - Memory usage patterns
        - Scalability limits
    
    Example:
        >>> instance = ClassName(param1, param2)
        >>> result = instance.method()
        >>> print(result)
        
    See Also:
        - RelatedClass: Brief explanation of relationship
        - another_module.Function: How they interact
    """
    
    def __init__(self, param: Type):
        """Initialize the class.
        
        Args:
            param (Type): Description of parameter.
        
        Raises:
            ValueError: If param is invalid.
            TypeError: If param is wrong type.
        """
        pass
```

### Method Documentation

```python
def method_name(self, param1: str, param2: int = 0) -> Dict[str, Any]:
    """Brief one-line description of what method does.
    
    Detailed description explaining:
    - Method purpose and behavior
    - Algorithm used (if complex)
    - Side effects (if any)
    - Thread safety implications
    
    Supported Features:
        - Feature 1: Description
        - Feature 2: Description
        - Feature 3: Description
    
    Algorithm:
        1. Step 1 explanation
        2. Step 2 explanation
        3. Step 3 explanation
        4. Return processed result
    
    Args:
        param1 (str): Description of param1.
            Additional context about format or constraints.
        param2 (int, optional): Description of param2.
            Defaults to 0. Specify valid ranges.
        
    Returns:
        Dict[str, Any]: Description of return value structure.
            Specify dictionary keys and their types:
            - 'key1' (str): Description of this key
            - 'key2' (List[int]): Description of this key
            
    Raises:
        ValueError: When and why this is raised.
        TypeError: When and why this is raised.
        CustomError: When and why this is raised.
            
    Example:
        >>> obj = ClassName()
        >>> result = obj.method_name("input", 5)
        >>> print(result['key1'])
        'expected output'
        
        >>> # Edge case example
        >>> result2 = obj.method_name("", 0)
        >>> print(result2)
        {'key1': '', 'key2': []}
    
    Performance:
        O(n) time complexity where n is length of param1.
        O(1) space complexity.
    
    Notes:
        - Important note 1
        - Important note 2
        - Gotcha or limitation
    
    See Also:
        - related_method(): How it relates
        - helper_function(): How it's used
    """
    pass
```

### Type Hints

Always use type hints for function signatures:

```python
from typing import Dict, List, Optional, Tuple, Any, Union

def process_data(
    data: List[Dict[str, Any]], 
    config: Optional[Dict[str, str]] = None
) -> Tuple[List[str], int]:
    """Process data with configuration.
    
    Args:
        data: List of data dictionaries
        config: Optional configuration dictionary
    
    Returns:
        Tuple of (processed items, count)
    """
    pass

# Use Union for multiple types
def flexible_input(value: Union[str, int, float]) -> str:
    """Accept multiple input types."""
    return str(value)

# Use Optional for nullable values
def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Return user dict or None if not found."""
    pass
```

### Code Comments

Use clear, descriptive comments:

```python
def complex_function(data: List[int]) -> List[int]:
    """Process data with complex logic."""
    
    # Step 1: Filter out invalid values (negative numbers)
    # We need this because the algorithm assumes positive values
    filtered = [x for x in data if x >= 0]
    
    # Step 2: Apply transformation algorithm
    # This uses a sliding window approach for O(n) performance
    transformed = []
    window_size = 3
    
    for i in range(len(filtered) - window_size + 1):
        # Calculate window average for smoothing
        window = filtered[i:i + window_size]
        avg = sum(window) / len(window)
        transformed.append(int(avg))
    
    # Step 3: Return sorted results for consistent output
    return sorted(transformed)
```

### Error Handling

```python
def safe_operation(data: str) -> Dict[str, Any]:
    """Perform operation with comprehensive error handling.
    
    Args:
        data: Input string to process
        
    Returns:
        Dictionary with results or error information
        
    Example:
        >>> result = safe_operation("valid input")
        >>> print(result['success'])
        True
    """
    try:
        # Attempt the operation
        result = risky_function(data)
        
        return {
            'success': True,
            'data': result,
            'error': None
        }
        
    except ValueError as e:
        # Handle expected errors with specific messages
        logger.error(f"Invalid input data: {e}")
        return {
            'success': False,
            'data': None,
            'error': f"Invalid input: {str(e)}"
        }
        
    except Exception as e:
        # Catch unexpected errors and log them
        logger.exception(f"Unexpected error in safe_operation: {e}")
        return {
            'success': False,
            'data': None,
            'error': "An unexpected error occurred"
        }
```

---

## ⚛️ TypeScript/React Standards

### Component Documentation

```typescript
/**
 * ComponentName - Brief description of component
 * 
 * Detailed description explaining:
 * - Component purpose and responsibility
 * - When to use this component
 * - Key features and capabilities
 * - Integration patterns
 * 
 * Features:
 * - Feature 1 with explanation
 * - Feature 2 with explanation
 * - Feature 3 with explanation
 * 
 * @example
 * ```tsx
 * <ComponentName
 *   prop1="value"
 *   prop2={42}
 *   onAction={handleAction}
 * />
 * ```
 * 
 * @see RelatedComponent
 * @see ../hooks/useCustomHook
 */
interface ComponentProps {
  /** Description of prop1 - what it does and valid values */
  prop1: string;
  
  /** Description of prop2 - include units or constraints */
  prop2: number;
  
  /** Callback when action occurs - describe parameters */
  onAction: (result: ActionResult) => void;
  
  /** Optional prop with default behavior explained */
  prop3?: boolean;
}

const ComponentName: React.FC<ComponentProps> = ({ 
  prop1, 
  prop2, 
  onAction,
  prop3 = false 
}) => {
  // Component implementation
  
  return (
    <div>{/* JSX */}</div>
  );
};

export default ComponentName;
```

### Hook Documentation

```typescript
/**
 * useCustomHook - Brief description of hook purpose
 * 
 * Detailed explanation of:
 * - What the hook does
 * - When to use it
 * - Side effects or limitations
 * 
 * @param param1 - Description of parameter
 * @param options - Configuration options
 * @returns Object containing state and handlers
 * 
 * @example
 * ```tsx
 * const { data, loading, error, refetch } = useCustomHook('id', {
 *   enabled: true,
 *   onSuccess: handleSuccess
 * });
 * ```
 * 
 * @see https://link-to-relevant-docs
 */
function useCustomHook(
  param1: string,
  options?: HookOptions
): HookResult {
  // Hook implementation
}
```

### Type Definitions

```typescript
/**
 * User data structure from API
 * 
 * Represents a user entity with authentication and profile information.
 * All fields are required unless marked optional.
 */
interface User {
  /** Unique user identifier (UUID format) */
  id: string;
  
  /** User's email address (validated format) */
  email: string;
  
  /** Display name (3-50 characters) */
  username: string;
  
  /** Account creation timestamp (ISO 8601 format) */
  createdAt: string;
  
  /** Optional profile picture URL */
  avatarUrl?: string;
}

/**
 * API response wrapper for typed responses
 * 
 * @template T - The type of data in the response
 */
interface ApiResponse<T> {
  /** Whether the request succeeded */
  success: boolean;
  
  /** Response data (only present if success is true) */
  data?: T;
  
  /** Error message (only present if success is false) */
  error?: string;
  
  /** HTTP status code */
  statusCode: number;
}
```

---

## 🎨 CSS/Styling Standards

### File Organization

```css
/* ============================================
   Section Name (e.g., Color System)
   ============================================ */

/* Subsection: Primary Colors */
:root {
  --color-primary: #0078D4;     /* Microsoft Blue - main brand color */
  --color-secondary: #00B294;   /* Teal - accent color */
}

/* Subsection: Spacing Scale */
:root {
  --space-sm: 0.5rem;   /* 8px - tight spacing */
  --space-md: 1rem;     /* 16px - default spacing */
  --space-lg: 1.5rem;   /* 24px - comfortable spacing */
}
```

### Component Styles

```css
/* ============================================
   ComponentName Styles
   Description of component styling approach
   ============================================ */

/* Base styles - default appearance */
.component-name {
  /* Layout */
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  
  /* Visual */
  background: var(--color-bg-primary);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  
  /* Animation */
  transition: all var(--transition-base);
}

/* Hover state - interactive feedback */
.component-name:hover {
  /* Lift effect for depth */
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

/* Active state - pressed appearance */
.component-name:active {
  transform: translateY(0);
}

/* Disabled state - non-interactive appearance */
.component-name:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}
```

### Animation Documentation

```css
/* ============================================
   AnimationName Animation
   Description: What this animation does and when it's used
   Duration: 300ms
   Easing: ease-out
   ============================================ */
@keyframes animationName {
  /* Starting state */
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  
  /* Ending state */
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Usage example */
.animated-element {
  animation: animationName var(--transition-base) ease-out;
}
```

---

## 📝 Git Commit Messages

Follow conventional commits format:

```
type(scope): brief description

Detailed explanation of what changed and why.
Include any breaking changes or important notes.

Fixes #123
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

### Examples

```
feat(auth): add OAuth2 authentication flow

Implement OAuth2 authentication using Microsoft identity platform.
Users can now sign in with their Microsoft accounts.

- Add OAuth2 configuration
- Implement token refresh logic
- Add authentication middleware

Closes #45
```

```
fix(email): resolve duplicate email detection issue

Fixed bug where emails with similar subjects were incorrectly
marked as duplicates. Now uses content similarity threshold.

- Update similarity calculation algorithm
- Add unit tests for edge cases
- Improve performance by 30%

Fixes #67
```

---

## ✅ Code Review Checklist

### Before Submitting PR

- [ ] All functions have type hints (Python) or proper types (TypeScript)
- [ ] All public functions have comprehensive docstrings/JSDoc
- [ ] Code follows project naming conventions
- [ ] Complex logic has explanatory comments
- [ ] Error handling is comprehensive
- [ ] No console.log or debug print statements
- [ ] Tests are written and passing
- [ ] Documentation is updated
- [ ] Code is formatted (prettier/black)
- [ ] No linting errors

### Documentation Quality

- [ ] Module/file has header documentation
- [ ] All parameters are documented
- [ ] Return values are explained
- [ ] Examples are provided
- [ ] Edge cases are noted
- [ ] Performance characteristics mentioned (if relevant)
- [ ] Related functions are cross-referenced

### Code Quality

- [ ] No duplicate code
- [ ] Functions are focused and single-purpose
- [ ] Variable names are descriptive
- [ ] Magic numbers are replaced with constants
- [ ] Error messages are user-friendly
- [ ] Code is DRY (Don't Repeat Yourself)

---

## 🎯 Best Practices Summary

### Python

1. **Always use type hints** - Helps IDEs and AI assistants
2. **Document everything public** - Classes, methods, constants
3. **Use docstring examples** - Helps users understand quickly
4. **Handle errors gracefully** - Don't let exceptions propagate
5. **Follow PEP 8** - Consistent style across codebase

### TypeScript/React

1. **Prefer functional components** - Use hooks over class components
2. **Type everything** - No `any` unless absolutely necessary
3. **Document props and hooks** - JSDoc comments for all exports
4. **Use proper semantic HTML** - Accessibility matters
5. **Keep components focused** - Single responsibility principle

### CSS

1. **Use CSS variables** - Consistent theming
2. **Mobile-first approach** - Start small, scale up
3. **Hardware acceleration** - Prefer transform and opacity
4. **Document animations** - Explain purpose and timing
5. **Respect user preferences** - reduced-motion support

---

## 📚 Resources

- [PEP 8 - Python Style Guide](https://pep8.org/)
- [PEP 257 - Docstring Conventions](https://www.python.org/dev/peps/pep-0257/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

---

## 🔄 Maintaining Standards

### Regular Reviews

- Schedule quarterly code quality audits
- Update standards as project evolves
- Share learnings from code reviews
- Celebrate good examples

### Tools

- **Python**: black, pylint, mypy, pydocstyle
- **TypeScript**: prettier, eslint, tsc --strict
- **Git**: commitlint, husky for git hooks
- **CI/CD**: Automated checks in pipeline

### Continuous Improvement

- Learn from mistakes
- Update guidelines based on team feedback
- Stay current with best practices
- Document new patterns as they emerge

---

This living document should be updated as the project evolves and new patterns emerge.
