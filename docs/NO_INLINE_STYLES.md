# ESLint Rule: No Inline Styles

## Overview

This project enforces a strict "no inline styles" policy for React components. All styling must be done through CSS classes defined in `frontend/src/styles/unified.css`.

## Why This Rule Exists

1. **Consistency**: All styles in one place makes the codebase easier to maintain
2. **Reusability**: CSS classes can be shared across components
3. **Performance**: CSS classes are more performant than inline styles
4. **Maintainability**: Easier to update styles globally
5. **Design System**: Enforces use of our unified design system

## The Rule

The ESLint configuration includes a `no-restricted-syntax` rule that warns when `style` attributes are used in JSX:

```javascript
'no-restricted-syntax': [
  'warn',
  {
    selector: 'JSXAttribute[name.name="style"]',
    message: 'Inline styles are forbidden. Use CSS classes from unified.css instead...',
  },
],
```

## How to Follow the Rule

### ❌ WRONG - Inline Styles
```typescript
// Don't do this
<div style={{ color: 'red', fontSize: '14px', marginTop: '20px' }}>
  Error message
</div>

<button style={{ backgroundColor: '#007bff' }}>
  Click me
</button>
```

### ✅ CORRECT - CSS Classes
```typescript
// Do this instead
<div className="error-message">
  Error message
</div>

<button className="btn-primary">
  Click me
</button>
```

```css
/* In unified.css */
.error-message {
  color: red;
  font-size: 14px;
  margin-top: 20px;
}

.btn-primary {
  background-color: #007bff;
}
```

## Legitimate Exceptions

There are **very rare** cases where inline styles are acceptable. Only use inline styles when:

1. **The value is calculated at runtime and cannot be predetermined**
2. **The value depends on props or state that cannot be expressed in CSS**

### ✅ ACCEPTABLE - Dynamic Runtime Values
```typescript
// This is acceptable because width is calculated at runtime
const ProgressBar = ({ progress }: { progress: number }) => {
  return (
    <div className="progress-bar">
      <div 
        className="progress-bar-fill" 
        style={{ width: `${progress}%` }}  // OK: runtime calculation
      >
        {progress}%
      </div>
    </div>
  );
};

// This is acceptable because position is based on mouse coordinates
const Tooltip = ({ x, y, text }: { x: number; y: number; text: string }) => {
  return (
    <div 
      className="tooltip" 
      style={{ left: `${x}px`, top: `${y}px` }}  // OK: dynamic positioning
    >
      {text}
    </div>
  );
};
```

### When to Disable the Rule

If you have a legitimate exception, you can disable the rule for that specific line:

```typescript
// eslint-disable-next-line no-restricted-syntax
<div style={{ width: `${calculatedWidth}px` }}>
  Content
</div>
```

**Always add a comment explaining why the exception is necessary.**

## How to Run ESLint

### Check for violations
```powershell
cd frontend
npm run lint
```

### Auto-fix violations
```powershell
npm run lint:fix
```

**Note:** The inline style rule cannot be auto-fixed. You must manually move styles to CSS classes.

## Current Violations

As of the last check, there are inline styles in the following files that should be refactored:

- `frontend/src/pages/Newsletters.tsx` - Link styles
- `frontend/src/pages/FYI.tsx` - Link styles
- `frontend/src/pages/Settings.tsx` - Padding and margin styles
- `frontend/src/pages/AccuracyDashboard.tsx` - Progress bar widths (acceptable)
- `frontend/src/components/Task/SimpleTaskList.tsx` - Progress bar widths (acceptable)
- `frontend/src/components/Task/ProgressTracker.tsx` - Progress indicators (acceptable)
- `frontend/src/components/Email/ProgressBar.tsx` - Bar widths (acceptable)

## Refactoring Guide

To refactor inline styles to CSS classes:

1. **Identify the inline style**
   ```typescript
   <a href="#/emails" style={{color: '#00f9ff', textDecoration: 'underline'}}>
   ```

2. **Create a CSS class in unified.css**
   ```css
   .link-primary {
     color: #00f9ff;
     text-decoration: underline;
   }
   ```

3. **Replace with class name**
   ```typescript
   <a href="#/emails" className="link-primary">
   ```

4. **Test the change**
   - Verify visual appearance matches
   - Check responsive behavior
   - Ensure no regressions

## BEM Naming Convention

When creating new CSS classes, follow BEM (Block Element Modifier) naming:

```css
/* Block */
.card { }

/* Element */
.card__header { }
.card__body { }
.card__footer { }

/* Modifier */
.card--highlighted { }
.card__header--large { }
```

## Testing

To verify the ESLint rule works:

1. Create a component with inline styles
2. Run `npm run lint`
3. Verify you see a warning about the inline style
4. Refactor to use CSS classes
5. Run `npm run lint` again
6. Verify the warning is gone

## Continuous Integration

The ESLint check runs automatically in CI/CD on every pull request. PRs with inline style violations will show a warning but won't fail the build (level: `warn`). However, we strongly encourage fixing all warnings before merging.

## Related Documentation

- [Unified CSS System](./UNIFIED_CSS.md)
- [Component Styling Guide](./COMPONENT_STYLING.md)
- [Contributing Guidelines](../CONTRIBUTING.md)

## Questions?

If you're unsure whether your use case qualifies as an exception, ask in your PR and tag a maintainer for guidance.
