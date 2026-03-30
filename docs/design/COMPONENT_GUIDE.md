# Component Usage Guide

A practical reference for using Nirvana's UI components consistently. Every example follows the [Design Guide](./DESIGN_GUIDE.md).

---

## Design System Tokens

All components use CSS custom properties defined in `index.css`. Never hardcode colors.

### Colors (use these, not `gray-500` or `indigo-600`)

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `bg-background` | `#fafafa` | `#0a0a0a` | Page background |
| `bg-card` | `#ffffff` | `#1a1a1a` | Card/surface |
| `bg-muted` | `#f5f5f5` | `#262626` | Subtle background |
| `text-foreground` | `#161616` | `#f5f5f5` | Primary text |
| `text-muted-foreground` | `#7a7a7a` | `#a6a6a6` | Secondary text |
| `bg-primary` | `#0071e3` | `#0b84ff` | Primary accent (blue) |
| `text-primary` | `#0071e3` | `#0b84ff` | Links, CTAs |
| `border-border` | `#e8e8e8` | `#3a3a3a` | Borders |
| `border-input` | `#d9d9d9` | `#3a3a3a` | Input borders |

### Semantic Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `text-success` / `bg-success` | `#34c759` | Growth, gains, positive |
| `text-destructive` / `bg-destructive` | `#ff3b30` | Decline, errors, negative |
| `text-warning` / `bg-warning` | `#ff9500` | Caution, attention |

### Semantic Background Patterns

```jsx
// Positive indicator
<span className="bg-success/10 text-success">+2.4%</span>

// Negative indicator
<span className="bg-destructive/10 text-destructive">-1.8%</span>

// Warning indicator
<span className="bg-warning/10 text-warning">Hold</span>

// Primary highlight
<div className="bg-primary/5 border-primary/20">Watchlist item</div>
```

---

## Button

```jsx
import { Button } from '@/components/ui/button';

// Primary (blue) — main CTAs
<Button>Create Watchlist</Button>

// Secondary — less prominent actions
<Button variant="secondary">Cancel</Button>

// Outline — bordered, neutral
<Button variant="outline">Refresh</Button>

// Ghost — invisible until hover
<Button variant="ghost" size="icon"><Settings /></Button>

// Destructive — dangerous actions
<Button variant="destructive">Delete</Button>

// Sizes
<Button size="sm">Small</Button>   // h-8
<Button size="default">Default</Button> // h-10
<Button size="lg">Large</Button>   // h-11
<Button size="icon">Icon</Button>  // h-10 w-10
```

### Do's and Don'ts

- **Do** use `variant="default"` for the single primary action per view
- **Do** use `variant="outline"` for secondary actions in headers
- **Don't** use multiple primary buttons in the same context
- **Don't** use raw `<button>` elements — always use the Button component

---

## Card

```jsx
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';

<Card>
  <CardHeader>
    <CardTitle>Watchlist Name</CardTitle>
    <CardDescription>Created Jan 1, 2026</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Content here */}
  </CardContent>
  <CardFooter>
    <Badge>5 stocks</Badge>
  </CardFooter>
</Card>
```

- Padding is `p-4` (16px) by default
- Hover lifts shadow from `shadow-sm` to `shadow-md`
- Use `bg-card` not `bg-white` for dark mode support

---

## Input

```jsx
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

<div className="space-y-2">
  <Label htmlFor="symbol">Ticker Symbol</Label>
  <Input
    id="symbol"
    placeholder="e.g., AAPL"
    value={value}
    onChange={handleChange}
  />
</div>
```

- Focus shows blue border + subtle blue ring (`ring-primary/20`)
- Height is `h-10` with `rounded-lg`
- Always pair with `<Label>` for accessibility

---

## Badge

```jsx
import { Badge } from '@/components/ui/badge';

// Variants
<Badge>Default (blue)</Badge>
<Badge variant="secondary">Secondary (gray)</Badge>
<Badge variant="success">Success (green bg)</Badge>
<Badge variant="warning">Warning (orange bg)</Badge>
<Badge variant="destructive">Destructive (red bg)</Badge>
<Badge variant="outline">Outline (bordered)</Badge>
```

- All badges use `rounded-full` (pill shape)
- Semantic variants use `bg-color/10 text-color` pattern (subtle, not loud)

---

## Dialog

```jsx
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogTrigger } from '@/components/ui/dialog';

<Dialog open={open} onOpenChange={setOpen}>
  <DialogTrigger asChild>
    <Button>Open</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Title</DialogTitle>
      <DialogDescription>Description text.</DialogDescription>
    </DialogHeader>
    {/* form content */}
    <DialogFooter>
      <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
      <Button type="submit">Confirm</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

- Overlay uses `bg-black/40` with `backdrop-blur-sm` (not opaque)
- Content uses `rounded-lg`

---

## Tabs

```jsx
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';

<Tabs defaultValue="price">
  <TabsList>
    <TabsTrigger value="price">Price History</TabsTrigger>
    <TabsTrigger value="valuation">Valuation</TabsTrigger>
  </TabsList>
  <TabsContent value="price">{/* ... */}</TabsContent>
  <TabsContent value="valuation">{/* ... */}</TabsContent>
</Tabs>
```

---

## Inline Tab Pattern (non-shadcn)

For pill-style tab groups used in headers/filters:

```jsx
<div className="flex gap-0.5 bg-muted rounded-lg p-1">
  {tabs.map((t) => (
    <button
      key={t.key}
      onClick={() => setTab(t.key)}
      className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-fast ${
        tab === t.key
          ? 'bg-background shadow-sm text-foreground'
          : 'text-muted-foreground hover:text-foreground'
      }`}
    >
      {t.label}
    </button>
  ))}
</div>
```

---

## Financial Data Patterns

### Price Display

```jsx
// Price — use font-mono for numbers
<span className="text-xl font-semibold text-foreground font-mono">
  ${price.toFixed(2)}
</span>

// Change — color by direction
<span className={`text-sm font-medium font-mono ${
  isPositive ? 'text-success' : 'text-destructive'
}`}>
  {isPositive ? '+' : ''}{change.toFixed(2)} ({changePercent.toFixed(2)}%)
</span>
```

### Status Badges

```jsx
// MA200 status
<span className={`inline-flex items-center text-xs px-2.5 py-0.5 rounded-full font-medium ${
  isAboveMA ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'
}`}>
  {isAboveMA ? '↑ Above' : '↓ Below'} MA200
</span>

// Analyst consensus
<span className="bg-success/10 text-success text-xs font-medium px-2.5 py-0.5 rounded-full">
  Buy (+12%)
</span>
```

### Performance Tiles

```jsx
// Color function for returns
const getColor = (value) => {
  if (value == null) return 'bg-muted text-muted-foreground';
  if (value > 0) return 'bg-success/10 text-success';
  return 'bg-destructive/10 text-destructive';
};
```

---

## Chart Tooltips

Use design system colors in chart tooltip styles:

```jsx
<Tooltip
  contentStyle={{
    backgroundColor: 'hsl(var(--card))',
    border: '1px solid hsl(var(--border))',
    borderRadius: '8px',
    color: 'hsl(var(--foreground))',
  }}
/>
```

Chart colors from the design guide:
- Line/area (primary): `#0071e3`
- Candlestick up: `#34c759` (success)
- Candlestick down: `#ff3b30` (destructive)
- Grid lines: `#e8e8e8`
- Axis text: `#7a7a7a`

---

## Layout Patterns

### Page Header (sticky, blurred)

```jsx
<header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
  <div className="container mx-auto px-4 py-4 flex justify-between items-center">
    {/* content */}
  </div>
</header>
```

### Full-Screen App Layout

```jsx
<div className="flex h-screen w-screen overflow-hidden">
  <div className="flex-1 min-w-0 overflow-auto">
    {/* Main content */}
  </div>
  {user && <AISidebar />}
</div>
```

### Empty State

```jsx
<div className="flex flex-col items-center justify-center py-16">
  <Icon className="h-12 w-12 text-muted-foreground/50 mb-4" />
  <h3 className="text-lg font-semibold mb-2">No items yet</h3>
  <p className="text-muted-foreground mb-6 text-center">Description</p>
  <Button>Action</Button>
</div>
```

---

## Transition Tokens

Always use design system durations:

| Class | Duration | Usage |
|-------|----------|-------|
| `duration-fast` | 150ms | Hover/focus state changes |
| `duration-normal` | 250ms | Meaningful transitions |
| `duration-slow` | 350ms | Page transitions |

```jsx
// Standard interactive element
className="transition-colors duration-fast"

// Card hover
className="transition-shadow duration-fast"

// Entrance animation
className="animate-fade-in-up"
```

---

## Common Mistakes to Avoid

| Instead of... | Use... |
|---------------|--------|
| `bg-white` | `bg-card` or `bg-background` |
| `text-gray-500` | `text-muted-foreground` |
| `text-gray-900` | `text-foreground` |
| `border-gray-200` | `border-border` |
| `bg-indigo-600` | `bg-primary` |
| `text-indigo-600` | `text-primary` |
| `bg-indigo-50` | `bg-primary/5` |
| `text-green-600` | `text-success` |
| `text-red-600` | `text-destructive` |
| `bg-gray-100` | `bg-muted` |
| `rounded-md` (buttons) | `rounded-lg` |
| `transition` | `transition-colors duration-fast` |
| `shadow` (cards) | `shadow-sm` + `hover:shadow-md` |

---

*Last Updated: March 2026*
