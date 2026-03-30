# Tailwind Configuration Guide

This document provides the complete Tailwind configuration to implement the Nirvana design system. Copy these configurations into your `tailwind.config.js` and `src/index.css`.

## tailwind.config.js

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Neutral Scale
        neutral: {
          50: '#fafafa',
          100: '#f5f5f5',
          200: '#e8e8e8',
          300: '#d9d9d9',
          400: '#a6a6a6',
          500: '#7a7a7a',
          600: '#595959',
          700: '#424242',
          800: '#2a2a2a',
          900: '#161616',
        },
        // Semantic Accent Colors
        primary: {
          DEFAULT: '#0071e3',
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          600: '#0071e3',
          700: '#0369a1',
          800: '#075985',
        },
        success: {
          DEFAULT: '#34c759',
          light: '#d1fae5',
          dark: '#065f46',
        },
        warning: {
          DEFAULT: '#ff9500',
          light: '#fef3c7',
          dark: '#92400e',
        },
        danger: {
          DEFAULT: '#ff3b30',
          light: '#fee2e2',
          dark: '#7f1d1d',
        },
      },
      spacing: {
        xs: '4px',
        sm: '8px',
        md: '12px',
        lg: '16px',
        xl: '24px',
        '2xl': '32px',
        '3xl': '48px',
        '4xl': '64px',
      },
      borderRadius: {
        none: '0',
        sm: '6px',
        md: '8px',
        lg: '12px',
        xl: '16px',
        full: '9999px',
      },
      boxShadow: {
        xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        sm: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)',
        md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
        lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
        xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
        '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        // Refined shadows for design system
        none: 'none',
        focus: '0 0 0 3px rgba(0, 113, 227, 0.1)',
      },
      transitionDuration: {
        fast: '150ms',
        normal: '250ms',
        slow: '350ms',
      },
      transitionTimingFunction: {
        standard: 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      backdropBlur: {
        xs: '2px',
        sm: '4px',
        md: '8px',
        lg: '12px',
      },
      fontSize: {
        // Display sizes
        'display-2xl': ['42px', { lineHeight: '51px', letterSpacing: '-0.5px', fontWeight: '600' }],
        'display-xl': ['36px', { lineHeight: '43px', letterSpacing: '-0.5px', fontWeight: '600' }],
        'display-lg': ['28px', { lineHeight: '34px', letterSpacing: '-0.5px', fontWeight: '600' }],
        'display': ['24px', { lineHeight: '29px', letterSpacing: '-0.5px', fontWeight: '600' }],
        // Headline sizes
        'headline': ['18px', { lineHeight: '28px', letterSpacing: '0', fontWeight: '600' }],
        'subheading': ['16px', { lineHeight: '24px', letterSpacing: '0', fontWeight: '500' }],
        // Body sizes
        'body-lg': ['16px', { lineHeight: '24px', letterSpacing: '0' }],
        'body': ['14px', { lineHeight: '21px', letterSpacing: '0' }],
        'body-sm': ['13px', { lineHeight: '20px', letterSpacing: '0' }],
        // Label sizes
        'label': ['12px', { lineHeight: '18px', letterSpacing: '0', fontWeight: '500' }],
        'caption': ['11px', { lineHeight: '17px', letterSpacing: '0' }],
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};
```

## src/index.css

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* Neutral palette */
    --neutral-50: #fafafa;
    --neutral-100: #f5f5f5;
    --neutral-200: #e8e8e8;
    --neutral-300: #d9d9d9;
    --neutral-400: #a6a6a6;
    --neutral-500: #7a7a7a;
    --neutral-600: #595959;
    --neutral-700: #424242;
    --neutral-800: #2a2a2a;
    --neutral-900: #161616;

    /* Accent colors */
    --primary: #0071e3;
    --success: #34c759;
    --warning: #ff9500;
    --danger: #ff3b30;

    /* Motion */
    --duration-fast: 150ms;
    --duration-normal: 250ms;
    --duration-slow: 350ms;
    --easing: cubic-bezier(0.4, 0, 0.2, 1);
  }

  .dark {
    --neutral-50: #fafafa;
    --neutral-100: #f5f5f5;
    --neutral-200: #3a3a3a;
    --neutral-300: #4a4a4a;
    --neutral-400: #6a6a6a;
    --neutral-500: #8e8e93;
    --neutral-600: #a6a6a6;
    --neutral-700: #c7c7cc;
    --neutral-800: #e5e5ea;
    --neutral-900: #f5f5f5;

    color-scheme: dark;
  }

  * {
    @apply border-neutral-200 dark:border-neutral-200;
  }

  html {
    @apply scroll-smooth;
  }

  body {
    @apply bg-neutral-50 text-neutral-900 dark:bg-neutral-900 dark:text-neutral-50;
    @apply font-body;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  /* Headings */
  h1 {
    @apply text-display-2xl font-600 tracking-tight;
  }

  h2 {
    @apply text-display-lg font-600 tracking-tight;
  }

  h3 {
    @apply text-display font-600 tracking-tight;
  }

  h4 {
    @apply text-headline font-600;
  }

  h5 {
    @apply text-subheading font-500;
  }

  h6 {
    @apply text-body font-500;
  }

  p {
    @apply text-body leading-relaxed;
  }

  a {
    @apply text-primary hover:text-primary/80 transition-colors duration-fast;
  }

  code {
    @apply font-mono text-sm bg-neutral-100 dark:bg-neutral-800 px-2 py-1 rounded;
  }

  pre {
    @apply bg-neutral-100 dark:bg-neutral-800 p-4 rounded-lg overflow-x-auto;
  }
}

@layer components {
  /* Button Base Styles */
  .btn {
    @apply inline-flex items-center justify-center gap-2
           px-lg py-md
           font-500 text-sm
           rounded-md
           transition-all duration-fast ease-standard
           focus:outline-none focus:ring-2 focus:ring-offset-2
           disabled:opacity-50 disabled:cursor-not-allowed
           cursor-pointer;
  }

  /* Button Variants */
  .btn-primary {
    @apply bg-primary text-white hover:bg-primary/90 dark:hover:bg-primary/80
           focus:ring-primary/50;
  }

  .btn-secondary {
    @apply bg-neutral-200 text-neutral-900 hover:bg-neutral-300 dark:bg-neutral-700 dark:text-neutral-50 dark:hover:bg-neutral-600
           focus:ring-neutral-400;
  }

  .btn-ghost {
    @apply text-neutral-600 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:bg-neutral-800
           px-md py-sm
           focus:ring-neutral-400;
  }

  .btn-danger {
    @apply bg-danger text-white hover:bg-danger/90
           focus:ring-danger/50;
  }

  /* Button Sizes */
  .btn-sm {
    @apply px-md py-sm text-sm;
  }

  .btn-lg {
    @apply px-2xl py-lg text-base;
  }

  /* Card Base */
  .card {
    @apply bg-white dark:bg-neutral-800
           rounded-lg
           border border-neutral-200 dark:border-neutral-700
           shadow-sm hover:shadow-md
           transition-shadow duration-fast;
  }

  .card-header {
    @apply px-lg py-lg border-b border-neutral-200 dark:border-neutral-700;
  }

  .card-body {
    @apply px-lg py-lg;
  }

  .card-footer {
    @apply px-lg py-lg border-t border-neutral-200 dark:border-neutral-700
           bg-neutral-50 dark:bg-neutral-900;
  }

  /* Input Base */
  .input {
    @apply w-full
           px-lg py-md
           bg-white dark:bg-neutral-800
           border border-neutral-300 dark:border-neutral-600
           rounded-md
           text-neutral-900 dark:text-neutral-50
           placeholder:text-neutral-400 dark:placeholder:text-neutral-500
           focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary dark:focus:border-primary
           transition-all duration-fast
           text-body;
  }

  .input:disabled {
    @apply bg-neutral-100 dark:bg-neutral-700 cursor-not-allowed opacity-50;
  }

  /* Badge */
  .badge {
    @apply inline-flex items-center gap-xs px-md py-sm
           rounded-full
           text-label font-500
           whitespace-nowrap;
  }

  .badge-primary {
    @apply bg-primary/10 text-primary dark:bg-primary/20;
  }

  .badge-success {
    @apply bg-success/10 text-success dark:bg-success/20;
  }

  .badge-warning {
    @apply bg-warning/10 text-warning dark:bg-warning/20;
  }

  .badge-danger {
    @apply bg-danger/10 text-danger dark:bg-danger/20;
  }

  .badge-neutral {
    @apply bg-neutral-200 text-neutral-700 dark:bg-neutral-700 dark:text-neutral-300;
  }

  /* Divider */
  .divider {
    @apply border-t border-neutral-200 dark:border-neutral-700;
  }

  /* Glass Effect */
  .glass {
    @apply bg-white/90 dark:bg-neutral-900/90
           backdrop-blur-md
           border border-white/20 dark:border-neutral-700/20;
  }

  /* Loading Skeleton */
  .skeleton {
    @apply bg-neutral-200 dark:bg-neutral-700 rounded animate-pulse;
  }

  /* Flex Center */
  .flex-center {
    @apply flex items-center justify-center;
  }

  /* Container */
  .container {
    @apply mx-auto px-lg sm:px-xl md:px-2xl max-w-6xl;
  }
}

/* Animations */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(-16px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@layer utilities {
  .animate-fadeInUp {
    animation: fadeInUp 250ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  .animate-slideInRight {
    animation: slideInRight 250ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  .transition-standard {
    @apply transition-all duration-normal ease-standard;
  }

  .transition-fast {
    @apply transition-all duration-fast ease-standard;
  }

  .text-truncate {
    @apply truncate;
  }

  .text-clamp-2 {
    @apply line-clamp-2;
  }

  .text-clamp-3 {
    @apply line-clamp-3;
  }

  /* Responsive typography */
  .text-responsive {
    @apply text-body sm:text-body-lg;
  }

  .heading-responsive {
    @apply text-display-lg md:text-display-xl lg:text-display-2xl;
  }

  /* Accessibility: Reduce motion for users who prefer it */
  @media (prefers-reduced-motion: reduce) {
    * {
      @apply !transition-none !animate-none;
    }
  }
}
```

## Quick Reference

### Color Usage

```jsx
// Primary Actions
<button className="btn btn-primary">Action</button>

// Secondary Actions
<button className="btn btn-secondary">Secondary</button>

// Ghost (Minimal)
<button className="btn btn-ghost">Ghost</button>

// Danger Zone
<button className="btn btn-danger">Delete</button>
```

### Spacing

```jsx
// Use spacing utilities consistently
<div className="p-lg">         {/* 16px padding */}
  <div className="mb-xl">      {/* 24px margin-bottom */}
    <span className="text-body">Text</span>
  </div>
</div>
```

### Responsive Design

```jsx
// Mobile-first, scale up
<div className="px-lg sm:px-xl md:px-2xl lg:px-3xl">
  <h1 className="text-display sm:text-display-lg md:text-display-xl">
    Responsive Heading
  </h1>
</div>
```

### Dark Mode

```jsx
// Automatic with class strategy
<div className="bg-neutral-50 dark:bg-neutral-900 text-neutral-900 dark:text-neutral-50">
  Dark mode ready
</div>
```

### Focus States

```jsx
<input
  className="input focus:ring-2 focus:ring-primary/20 focus:border-primary"
  placeholder="Accessible input"
/>
```

### Icons + Text

```jsx
<button className="btn btn-primary gap-md">
  <Icon className="w-4 h-4" />
  <span>With Icon</span>
</button>
```

## Migration Checklist

- [ ] Update `tailwind.config.js` with new color palette
- [ ] Update `src/index.css` with CSS layers
- [ ] Replace all shadcn/ui components with new color classes
- [ ] Update button styles across app
- [ ] Update input styles across app
- [ ] Test dark mode thoroughly
- [ ] Test all focus states (keyboard navigation)
- [ ] Update modal/overlay styling
- [ ] Test on mobile devices (320px, 768px)
- [ ] Verify contrast ratios (use WebAIM checker)

---

*This configuration implements the Nirvana Design Guide. Keep it synchronized as the design evolves.*
