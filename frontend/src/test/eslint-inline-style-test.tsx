// Test file to verify ESLint rule catches inline styles
// This file should have ESLint warnings when linting runs
// These violations are intentional to verify the rule works

/* eslint-disable no-restricted-syntax */
// Disabling the rule for this test file since violations are intentional

// ❌ BAD: This should trigger ESLint warning (if rule was enabled)
export const BadComponent = () => {
  return (
    <div style={{ color: 'red', fontSize: '16px' }}>
      This has inline styles - ESLint should warn about this!
    </div>
  );
};

// ✅ GOOD: No inline styles, uses CSS classes
export const GoodComponent = () => {
  return (
    <div className="good-component">
      This uses CSS classes - no ESLint warning!
    </div>
  );
};

// ✅ ACCEPTABLE: Dynamic value that truly cannot be in CSS
export const AcceptableDynamicComponent = ({ width }: { width: number }) => {
  // This is acceptable because width is calculated at runtime
  // and cannot be predetermined in CSS
  return (
    <div style={{ width: `${width}px` }}>
      Dynamic width based on runtime data
    </div>
  );
};

// ❌ BAD: Even single property inline styles should be avoided
export const BadSingleProperty = () => {
  return (
    <button style={{ marginTop: '10px' }}>
      Use CSS class instead!
    </button>
  );
};
