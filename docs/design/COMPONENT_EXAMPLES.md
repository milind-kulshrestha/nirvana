# Component Examples

Production-ready React component examples that implement the Nirvana design system. Use these as templates for building consistent, thoughtfully-designed interfaces.

## Table of Contents

1. [Button](#button)
2. [Card](#card)
3. [Input](#input)
4. [Badge](#badge)
5. [Modal](#modal)
6. [Navigation](#navigation)
7. [Form](#form)
8. [Data Table](#data-table)
9. [Empty State](#empty-state)
10. [Loading State](#loading-state)

---

## Button

The simplest, most elegant button component. Single responsibility: clear, accessible, responsive.

### Basic Button

```jsx
export function Button({
  variant = 'primary',
  size = 'md',
  disabled = false,
  children,
  className = '',
  ...props
}) {
  const baseStyles = `
    inline-flex items-center justify-center gap-2
    font-500 rounded-md
    transition-all duration-fast ease-standard
    focus:outline-none focus:ring-2 focus:ring-offset-2
    disabled:opacity-50 disabled:cursor-not-allowed
  `;

  const variants = {
    primary: 'bg-primary text-white hover:bg-primary/90 focus:ring-primary/50 active:scale-98',
    secondary: 'bg-neutral-200 text-neutral-900 hover:bg-neutral-300 focus:ring-neutral-400 active:scale-98',
    ghost: 'text-neutral-600 hover:bg-neutral-100 focus:ring-neutral-400 active:opacity-75',
    danger: 'bg-danger text-white hover:bg-danger/90 focus:ring-danger/50 active:scale-98',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-6 py-3 text-sm',
    lg: 'px-8 py-4 text-base',
  };

  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}

// Usage
<Button variant="primary" size="md">
  Click me
</Button>
```

### With Icon

```jsx
import { Plus } from 'lucide-react';

<Button variant="primary">
  <Plus className="w-4 h-4" />
  <span>New Watchlist</span>
</Button>
```

### Disabled State

```jsx
<Button variant="primary" disabled>
  Processing...
</Button>
```

---

## Card

Simple container with subtle depth. No decoration, just refined presentation.

### Basic Card

```jsx
export function Card({ children, className = '', hoverable = false }) {
  return (
    <div
      className={`
        bg-white dark:bg-neutral-800
        rounded-lg
        border border-neutral-200 dark:border-neutral-700
        shadow-sm ${hoverable ? 'hover:shadow-md' : ''}
        transition-shadow duration-fast
        ${className}
      `}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className = '' }) {
  return (
    <div className={`px-6 py-4 border-b border-neutral-200 dark:border-neutral-700 ${className}`}>
      {children}
    </div>
  );
}

export function CardBody({ children, className = '' }) {
  return <div className={`px-6 py-4 ${className}`}>{children}</div>;
}

export function CardFooter({ children, className = '' }) {
  return (
    <div className={`
      px-6 py-4
      border-t border-neutral-200 dark:border-neutral-700
      bg-neutral-50 dark:bg-neutral-900
      rounded-b-lg
      ${className}
    `}>
      {children}
    </div>
  );
}

// Usage
<Card hoverable>
  <CardHeader>
    <h3 className="text-headline font-600">Card Title</h3>
  </CardHeader>
  <CardBody>
    <p className="text-body text-neutral-600">Card content goes here.</p>
  </CardBody>
  <CardFooter>
    <Button variant="ghost" size="sm">Learn more</Button>
  </CardFooter>
</Card>
```

---

## Input

Conversational input fields with subtle focus states.

### Text Input

```jsx
export function Input({
  label,
  error,
  disabled = false,
  helpText,
  ...props
}) {
  return (
    <div className="flex flex-col gap-2">
      {label && (
        <label className="text-label font-500 text-neutral-700 dark:text-neutral-300">
          {label}
        </label>
      )}
      <input
        className={`
          w-full px-4 py-3
          bg-white dark:bg-neutral-800
          border rounded-md
          text-neutral-900 dark:text-neutral-50
          placeholder:text-neutral-400 dark:placeholder:text-neutral-500
          focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary
          transition-all duration-fast
          text-body
          ${error ? 'border-danger focus:border-danger focus:ring-danger/20' : 'border-neutral-300 dark:border-neutral-600'}
          ${disabled ? 'bg-neutral-100 dark:bg-neutral-700 cursor-not-allowed opacity-50' : ''}
        `}
        disabled={disabled}
        {...props}
      />
      {error && <p className="text-body-sm text-danger">{error}</p>}
      {helpText && <p className="text-body-sm text-neutral-500">{helpText}</p>}
    </div>
  );
}

// Usage
<Input
  label="Email Address"
  type="email"
  placeholder="name@example.com"
  helpText="We'll never share your email."
/>

<Input
  label="Password"
  type="password"
  error="Password must be at least 8 characters"
/>
```

### Textarea

```jsx
export function Textarea({
  label,
  error,
  rows = 4,
  ...props
}) {
  return (
    <div className="flex flex-col gap-2">
      {label && (
        <label className="text-label font-500 text-neutral-700 dark:text-neutral-300">
          {label}
        </label>
      )}
      <textarea
        rows={rows}
        className={`
          w-full px-4 py-3
          bg-white dark:bg-neutral-800
          border rounded-md
          text-neutral-900 dark:text-neutral-50
          placeholder:text-neutral-400
          focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary
          transition-all duration-fast
          text-body
          resize-none
          ${error ? 'border-danger' : 'border-neutral-300 dark:border-neutral-600'}
        `}
        {...props}
      />
      {error && <p className="text-body-sm text-danger">{error}</p>}
    </div>
  );
}
```

---

## Badge

Minimal status indicators. Color conveys meaning, not decoration.

### Badge Component

```jsx
export function Badge({
  variant = 'neutral',
  children,
  className = ''
}) {
  const variants = {
    primary: 'bg-primary/10 text-primary dark:bg-primary/20',
    success: 'bg-success/10 text-success dark:bg-success/20',
    warning: 'bg-warning/10 text-warning dark:bg-warning/20',
    danger: 'bg-danger/10 text-danger dark:bg-danger/20',
    neutral: 'bg-neutral-200 text-neutral-700 dark:bg-neutral-700 dark:text-neutral-300',
  };

  return (
    <span className={`
      inline-flex items-center gap-1
      px-3 py-1.5 rounded-full
      text-label font-500
      whitespace-nowrap
      ${variants[variant]}
      ${className}
    `}>
      {children}
    </span>
  );
}

// Usage
<Badge variant="success">Active</Badge>
<Badge variant="warning">Pending</Badge>
<Badge variant="danger">Declined</Badge>
<Badge variant="neutral">Neutral</Badge>
```

---

## Modal

Simple, focused dialog. Minimal overlay, glass-morphic backdrop.

### Modal Component

```jsx
import { X } from 'lucide-react';

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  actions,
  size = 'md',
}) {
  if (!isOpen) return null;

  const sizes = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 dark:bg-black/60 backdrop-blur-sm z-40"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
        <Card className={`w-full ${sizes[size]} rounded-lg`}>
          {/* Header */}
          <CardHeader className="flex items-center justify-between">
            <h2 className="text-headline font-600">{title}</h2>
            <button
              onClick={onClose}
              className="text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 p-1 rounded hover:bg-neutral-100 dark:hover:bg-neutral-700 transition-colors"
              aria-label="Close modal"
            >
              <X className="w-4 h-4" />
            </button>
          </CardHeader>

          {/* Body */}
          <CardBody className="max-h-96 overflow-y-auto">
            {children}
          </CardBody>

          {/* Footer */}
          {actions && (
            <CardFooter className="flex gap-3 justify-end">
              {actions}
            </CardFooter>
          )}
        </Card>
      </div>
    </>
  );
}

// Usage
const [isOpen, setIsOpen] = useState(false);

<>
  <Button onClick={() => setIsOpen(true)}>Open Modal</Button>

  <Modal
    isOpen={isOpen}
    onClose={() => setIsOpen(false)}
    title="Confirm Action"
    actions={
      <>
        <Button variant="secondary" onClick={() => setIsOpen(false)}>
          Cancel
        </Button>
        <Button variant="primary">Confirm</Button>
      </>
    }
  >
    <p className="text-body text-neutral-600 dark:text-neutral-400">
      Are you sure you want to continue?
    </p>
  </Modal>
</>
```

---

## Navigation

Clean header with semantic navigation.

### Header Navigation

```jsx
import { Menu, X } from 'lucide-react';

export function Header({ user, onLogout }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 bg-white dark:bg-neutral-800 border-b border-neutral-200 dark:border-neutral-700">
      <div className="container flex items-center justify-between h-16">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <h1 className="text-headline font-600">Nirvana</h1>
        </div>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-8">
          <a href="/watchlists" className="text-body hover:text-primary transition-colors">
            Watchlists
          </a>
          <a href="/discover" className="text-body hover:text-primary transition-colors">
            Discover
          </a>
          <a href="/etf" className="text-body hover:text-primary transition-colors">
            ETF Dashboard
          </a>
        </nav>

        {/* User Menu */}
        <div className="flex items-center gap-4">
          {user && (
            <div className="flex items-center gap-3">
              <span className="text-body text-neutral-600 dark:text-neutral-400">
                {user.email}
              </span>
              <Button variant="ghost" size="sm" onClick={onLogout}>
                Log out
              </Button>
            </div>
          )}
        </div>

        {/* Mobile Menu Button */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2 hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded-md"
        >
          {mobileMenuOpen ? (
            <X className="w-5 h-5" />
          ) : (
            <Menu className="w-5 h-5" />
          )}
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-700">
          <nav className="container py-4 space-y-2">
            <a
              href="/watchlists"
              className="block px-3 py-2 rounded-md hover:bg-neutral-200 dark:hover:bg-neutral-600"
            >
              Watchlists
            </a>
            <a
              href="/discover"
              className="block px-3 py-2 rounded-md hover:bg-neutral-200 dark:hover:bg-neutral-600"
            >
              Discover
            </a>
            <a
              href="/etf"
              className="block px-3 py-2 rounded-md hover:bg-neutral-200 dark:hover:bg-neutral-600"
            >
              ETF Dashboard
            </a>
          </nav>
        </div>
      )}
    </header>
  );
}
```

---

## Form

Complete form with validation and error handling.

### Form Example

```jsx
import { useState } from 'react';

export function WatchlistForm({ onSubmit, isLoading }) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });
  const [errors, setErrors] = useState({});

  const validate = () => {
    const newErrors = {};
    if (!formData.name.trim()) newErrors.name = 'Watchlist name is required';
    if (formData.name.length > 50) newErrors.name = 'Name must be 50 characters or less';
    return newErrors;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const newErrors = validate();

    if (Object.keys(newErrors).length === 0) {
      onSubmit(formData);
    } else {
      setErrors(newErrors);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Input
        label="Watchlist Name"
        placeholder="e.g., Tech Stocks"
        value={formData.name}
        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
        error={errors.name}
        disabled={isLoading}
      />

      <Textarea
        label="Description (Optional)"
        placeholder="Add notes about this watchlist..."
        value={formData.description}
        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
        disabled={isLoading}
        rows={4}
      />

      <div className="flex gap-3 justify-end">
        <Button variant="secondary" disabled={isLoading}>
          Cancel
        </Button>
        <Button variant="primary" type="submit" disabled={isLoading}>
          {isLoading ? 'Creating...' : 'Create Watchlist'}
        </Button>
      </div>
    </form>
  );
}
```

---

## Data Table

Clean, scannable table design for stock data.

### Data Table Component

```jsx
export function DataTable({ columns, data, loading }) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-12 bg-neutral-200 dark:bg-neutral-700 rounded animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-neutral-200 dark:border-neutral-700">
            {columns.map((col) => (
              <th
                key={col.key}
                className="px-4 py-3 text-left text-label font-500 text-neutral-600 dark:text-neutral-400"
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr
              key={idx}
              className="border-b border-neutral-100 dark:border-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-700/50 transition-colors"
            >
              {columns.map((col) => (
                <td key={col.key} className="px-4 py-3 text-body">
                  {col.render ? col.render(row[col.key], row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Usage
<DataTable
  columns={[
    { key: 'symbol', label: 'Symbol' },
    {
      key: 'price',
      label: 'Price',
      render: (value) => `$${value.toFixed(2)}`,
    },
    {
      key: 'change',
      label: 'Change',
      render: (value) => (
        <span className={value >= 0 ? 'text-success' : 'text-danger'}>
          {value >= 0 ? '+' : ''}{value.toFixed(2)}%
        </span>
      ),
    },
  ]}
  data={stocks}
  loading={loading}
/>
```

---

## Empty State

Friendly, helpful empty states that guide users toward action.

### Empty State Component

```jsx
import { Plus, TrendingUp } from 'lucide-react';

export function EmptyState({
  icon: Icon = TrendingUp,
  title,
  description,
  action,
  actionLabel = 'Get Started',
}) {
  return (
    <Card className="col-span-full">
      <div className="flex flex-col items-center justify-center py-16 px-6">
        <Icon className="w-12 h-12 text-neutral-400 dark:text-neutral-600 mb-4" />
        <h3 className="text-headline font-600 mb-2 text-neutral-900 dark:text-neutral-50">
          {title}
        </h3>
        <p className="text-body text-neutral-600 dark:text-neutral-400 mb-6 text-center max-w-md">
          {description}
        </p>
        {action && (
          <Button variant="primary" onClick={action}>
            <Plus className="w-4 h-4" />
            {actionLabel}
          </Button>
        )}
      </div>
    </Card>
  );
}

// Usage
<EmptyState
  title="No watchlists yet"
  description="Create your first watchlist to start tracking stocks"
  action={() => setShowCreateModal(true)}
  actionLabel="Create Watchlist"
/>
```

---

## Loading State

Clear, minimal loading indicators.

### Loading Skeleton

```jsx
export function Skeleton({ className = '' }) {
  return (
    <div
      className={`bg-neutral-200 dark:bg-neutral-700 rounded animate-pulse ${className}`}
    />
  );
}

// Usage
<div className="space-y-4">
  <Skeleton className="h-8 w-48" />
  <Skeleton className="h-4 w-32" />
  <div className="grid grid-cols-3 gap-4">
    {[1, 2, 3].map((i) => (
      <Skeleton key={i} className="h-32" />
    ))}
  </div>
</div>
```

### Loading Spinner

```jsx
export function LoadingSpinner({ size = 'md' }) {
  const sizeClass = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  }[size];

  return (
    <div className={`${sizeClass} border-2 border-neutral-300 dark:border-neutral-600 border-t-primary rounded-full animate-spin`} />
  );
}

// Usage
<div className="flex items-center gap-2">
  <LoadingSpinner size="md" />
  <span className="text-body text-neutral-600">Loading data...</span>
</div>
```

---

## Best Practices

### ✅ DO

- **Use semantic HTML** — `<button>`, `<input>`, `<form>`, etc.
- **Compose small components** — Button, Input, Card are primitives
- **Test accessibility** — Tab navigation, screen readers, WCAG AA
- **Respect motion preferences** — `prefers-reduced-motion`
- **Keep props minimal** — Only expose what's necessary
- **Use CSS for styling** — Tailwind classes, not inline styles

### ❌ DON'T

- **Build monolithic components** — Decompose into reusable pieces
- **Over-abstract props** — Keep interfaces simple and predictable
- **Add decorative elements** — Every pixel must serve function
- **Ignore error states** — Always show validation feedback
- **Create custom inputs** — Use semantic `<input>` and style it
- **Hardcode colors** — Use CSS variables from design system

---

*Last Updated: March 2026*
*These components are templates. Adapt to your needs while maintaining design principles.*
