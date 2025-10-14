# Email Helper - Animation & Style Quick Reference

## 🎨 CSS Variables Reference

### Colors
```css
/* Primary Colors */
--color-primary: #0078D4;        /* Microsoft Blue */
--color-primary-hover: #106EBE;  /* Darker Blue on hover */
--color-primary-light: #E8F4FD;  /* Light Blue backgrounds */
--color-secondary: #00B294;      /* Teal accent */
--color-accent: #8764B8;         /* Purple accent */

/* Status Colors */
--color-success: #107C10;        /* Green for success */
--color-danger: #D13438;         /* Red for errors */
--color-warning: #FFB900;        /* Yellow for warnings */

/* Text Colors */
--color-text-primary: #201F1E;   /* Main text */
--color-text-secondary: #605E5C; /* Secondary text */
--color-text-tertiary: #8A8886;  /* Tertiary text */
```

### Spacing
```css
--space-xs: 0.25rem;  /* 4px */
--space-sm: 0.5rem;   /* 8px */
--space-md: 1rem;     /* 16px */
--space-lg: 1.5rem;   /* 24px */
--space-xl: 2rem;     /* 32px */
--space-2xl: 3rem;    /* 48px */
```

### Typography
```css
--font-size-xs: 0.75rem;   /* 12px */
--font-size-sm: 0.875rem;  /* 14px */
--font-size-base: 1rem;    /* 16px */
--font-size-lg: 1.125rem;  /* 18px */
--font-size-xl: 1.25rem;   /* 20px */
--font-size-2xl: 1.5rem;   /* 24px */
--font-size-3xl: 2rem;     /* 32px */
```

### Effects
```css
/* Shadows */
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.04);
--shadow-md: 0 2px 8px rgba(0, 0, 0, 0.08);
--shadow-lg: 0 4px 16px rgba(0, 0, 0, 0.12);
--shadow-xl: 0 8px 32px rgba(0, 0, 0, 0.16);

/* Border Radius */
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;
--radius-full: 9999px;

/* Transitions */
--transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-base: 250ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1);
```

---

## ✨ Animation Recipes

### Page Entry Animation
```css
.component {
  animation: fadeIn var(--transition-base) ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
```

### Slide Down (Headers)
```css
.header {
  animation: slideDown var(--transition-slow) ease-out;
}

@keyframes slideDown {
  from {
    transform: translateY(-20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
```

### Scale In (Cards)
```css
.card {
  animation: scaleIn var(--transition-slow) ease-out;
}

@keyframes scaleIn {
  from {
    transform: scale(0.95);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}
```

### Staggered Animation (List Items)
```css
.item:nth-child(1) { animation-delay: 0.1s; }
.item:nth-child(2) { animation-delay: 0.2s; }
.item:nth-child(3) { animation-delay: 0.3s; }
```

### Hover Lift Effect
```css
.card {
  transition: all var(--transition-base);
}

.card:hover {
  transform: translateY(-8px);
  box-shadow: var(--shadow-lg);
}
```

### Button Ripple Effect
```css
.button {
  position: relative;
  overflow: hidden;
}

.button::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: translate(-50%, -50%);
  transition: width var(--transition-base), height var(--transition-base);
}

.button:hover::before {
  width: 400px;
  height: 400px;
}
```

### Pulsing Status Indicator
```css
.status-dot {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}
```

### Skeleton Loading
```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--color-bg-secondary) 25%,
    var(--color-bg-tertiary) 50%,
    var(--color-bg-secondary) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
```

### Spinner Loading
```css
.spinner {
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top: 3px solid currentColor;
  border-radius: 50%;
  animation: spin 0.8s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
```

---

## 🎯 React Animation Components

### Animated Counter
```typescript
const AnimatedCounter: React.FC<{ 
  end: number; 
  duration?: number;
  suffix?: string;
}> = ({ end, duration = 1000, suffix = '' }) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let startTime: number;
    let animationFrame: number;

    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime;
      const progress = Math.min((currentTime - startTime) / duration, 1);
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      setCount(Math.floor(easeOutQuart * end));

      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate);
      }
    };

    animationFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrame);
  }, [end, duration]);

  return <span>{count}{suffix}</span>;
};
```

### Skeleton Loader
```typescript
const SkeletonLoader: React.FC<{ 
  height?: string; 
  width?: string;
}> = ({ height = '20px', width = '100%' }) => (
  <div 
    className="skeleton" 
    style={{ height, width, display: 'inline-block' }}
  />
);
```

### Usage in Component
```typescript
const Dashboard: React.FC = () => {
  const { data, isLoading } = useQuery();

  return (
    <div>
      {isLoading ? (
        <SkeletonLoader height="30px" width="60%" />
      ) : (
        <AnimatedCounter end={data.count} suffix=" items" />
      )}
    </div>
  );
};
```

---

## 🎨 Common Patterns

### Gradient Text
```css
.gradient-text {
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

### Glassmorphism Effect
```css
.glass {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.5);
}
```

### Animated Underline
```css
.link::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
  transition: width var(--transition-base);
  border-radius: var(--radius-full);
}

.link:hover::after {
  width: 100%;
}
```

### Smooth Shadow Transition
```css
.card {
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--transition-base);
}

.card:hover {
  box-shadow: var(--shadow-lg);
}
```

---

## 📱 Responsive Patterns

### Mobile-First Breakpoints
```css
/* Mobile first (default) */
.component {
  flex-direction: column;
}

/* Tablet and up */
@media (min-width: 768px) {
  .component {
    flex-direction: row;
  }
}

/* Desktop and up */
@media (min-width: 1024px) {
  .component {
    max-width: 1400px;
  }
}
```

### Adaptive Spacing
```css
.container {
  padding: var(--space-md);
}

@media (min-width: 768px) {
  .container {
    padding: var(--space-xl);
  }
}

@media (min-width: 1024px) {
  .container {
    padding: var(--space-2xl);
  }
}
```

---

## ⚡ Performance Tips

### Hardware Acceleration
```css
/* Prefer transform over top/left */
.animated {
  transform: translateY(0);  /* ✅ Good */
  /* top: 0;  ❌ Avoid */
}

/* Use will-change sparingly */
.complex-animation {
  will-change: transform, opacity;
}
```

### Reduce Animation Scope
```css
/* Animate only transform and opacity for best performance */
.smooth {
  transition: transform var(--transition-base), 
              opacity var(--transition-base);
}

/* Avoid animating these properties */
.avoid {
  /* transition: width, height, margin;  ❌ Causes layout recalc */
}
```

### Respect User Preferences
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 🔧 Debug Tips

### Visualize Animations
```css
/* Temporarily slow down animations for debugging */
:root {
  --transition-fast: 1500ms !important;
  --transition-base: 2500ms !important;
  --transition-slow: 3500ms !important;
}
```

### Outline Boxes
```css
/* See component boundaries */
* {
  outline: 1px solid red !important;
}
```

### Check Animation State
```javascript
// In browser console
const element = document.querySelector('.animated');
console.log(getComputedStyle(element).animation);
console.log(getComputedStyle(element).transition);
```

---

## 📚 Resources

- [CSS Tricks - Animation Guide](https://css-tricks.com/almanac/properties/a/animation/)
- [MDN Web Docs - CSS Animations](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Animations)
- [Cubic Bezier Generator](https://cubic-bezier.com/)
- [Easing Functions Cheat Sheet](https://easings.net/)

---

## ✅ Checklist for New Animations

- [ ] Use CSS variables for timing and easing
- [ ] Add `animation-fill-mode: both` if needed
- [ ] Test with reduced motion preference
- [ ] Ensure 60fps performance
- [ ] Add appropriate delays for staggered effects
- [ ] Use hardware-accelerated properties (transform, opacity)
- [ ] Add fallback for older browsers if needed
- [ ] Test on mobile devices
- [ ] Verify animation completes correctly
- [ ] Document the animation in code comments
