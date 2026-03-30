# Nirvana Design Guide

## A Philosophy of Elegant Simplicity

Nirvana is built on the design principles of Apple, Steve Jobs, Jony Ive, and Dieter Rams. We believe in **simplicity through thoughtfulness**—every pixel serves a purpose, every interaction feels effortless, and every element is crafted with precision.

This guide embodies three core philosophies:

- **"Simplicity is the ultimate sophistication"** — Steve Jobs
- **"The details matter, you're either the one doing them right or you're not"** — Steve Jobs
- **"Good design is less, but better"** — Dieter Rams

---

## Core Design Principles

### 1. **Simplicity Over Decoration**
- Remove everything unnecessary; keep only what serves function
- Embrace white space as an active design element
- Let data and content breathe
- No decorative flourishes; every element has purpose

### 2. **Human-Centered Clarity**
- Design for the user, not the designer
- Information hierarchy guides without overwhelming
- Interactions are discoverable and intuitive
- Accessibility is non-negotiable

### 3. **Precision & Polish**
- Attention to every detail: spacing, corners, shadows, transitions
- Consistency across all contexts
- High-fidelity, refined aesthetic
- Nothing feels rough or unfinished

### 4. **Function First**
- Form follows function rigorously
- Visual hierarchy reflects information importance
- Every interaction has clear cause and effect
- Performance and usability are paramount

### 5. **Timeless Over Trendy**
- Design that will age gracefully
- Avoid novelty for novelty's sake
- Elegant, understated approach
- Invest in fundamentals, not gimmicks

---

## Color System

### Philosophy
Our palette is **restrained and refined**. We use neutral tones as the foundation with carefully chosen accents that feel natural, not loud. Every color has earned its place.

### Palette

#### Neutral Base
```css
--neutral-50:   #fafafa;  /* Nearly white, breathing room */
--neutral-100:  #f5f5f5;  /* Soft background */
--neutral-200:  #e8e8e8;  /* Subtle dividers */
--neutral-300:  #d9d9d9;  /* Input borders */
--neutral-400:  #a6a6a6;  /* Secondary text */
--neutral-500:  #7a7a7a;  /* Tertiary text */
--neutral-600:  #595959;  /* Body text */
--neutral-700:  #424242;  /* Emphasis text */
--neutral-800:  #2a2a2a;  /* Dark emphasis */
--neutral-900:  #161616;  /* Near black, main text */
```

#### Accent Colors
```css
--accent-primary:    #0071e3;  /* Apple Blue - refined, tech-forward */
--accent-secondary:  #34c759;  /* System Green - for positive/growth */
--accent-danger:     #ff3b30;  /* System Red - for alerts/decline */
--accent-warning:    #ff9500;  /* System Orange - for caution */
```

#### Semantic Colors
```css
--success:    #34c759;  /* Growth, wins, positive change */
--warning:    #ff9500;  /* Caution, needs attention */
--danger:     #ff3b30;  /* Decline, errors, destructive */
--neutral:    #8e8e93;  /* Neutral data point */
```

### Usage Rules

**Neutral (85% of design):**
- Backgrounds: `--neutral-50` to `--neutral-100`
- Text: `--neutral-900` on light, `--neutral-50` on dark
- Borders: `--neutral-200` (subtle, never harsh)
- Dividers: `--neutral-100` (barely perceptible)

**Accent (15% of design):**
- Primary CTAs: `--accent-primary`
- Status indicators: `--accent-secondary` (up), `--accent-danger` (down)
- Data visualization: Use all accents with hierarchy
- Never use more than one primary accent per view

**Dark Mode:**
- Background: `#0a0a0a` (not pure black—softer on eyes)
- Surface: `#1a1a1a` (card backgrounds)
- Text: `#f5f5f5` (not pure white—easier on eyes)
- Borders: `#3a3a3a` (more visible on dark)

### Color Psychology in Finance
- **Blue**: Trust, stability, tech-forward (our primary)
- **Green**: Growth, gains, confidence
- **Red**: Decline, caution, losses (never aggressive)
- **Gray**: Neutral, stable baseline
- **Orange**: Warning, attention-needed (not judgmental)

---

## Typography System

### Philosophy
Typography is **invisible perfection**. The user reads the content, not the typeface. Our fonts are chosen for clarity, modernity, and elegance—tools that get out of the way.

### Font Stack
```css
/* Display (Headlines, Hero) */
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "San Francisco", "Helvetica Neue", sans-serif;
font-weight: 600;
letter-spacing: -0.5px;

/* Body (Content, UI Labels) */
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "San Francisco", "Helvetica Neue", sans-serif;
font-weight: 400;
letter-spacing: 0;

/* Mono (Data, Code, Numbers) */
font-family: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", monospace;
font-weight: 400;
letter-spacing: 0;
```

**Why system fonts?**
- Feels native and familiar to each platform
- No web font bloat—instant rendering
- Users trust what feels of-the-system
- Perfect fallback chain

### Scale & Hierarchy

```
Display 2XL:   42px / 51px  | 600 weight | Headlines
Display XL:    36px / 43px  | 600 weight | Page titles
Display Large: 28px / 34px  | 600 weight | Section headers
Display:       24px / 29px  | 600 weight | Subsection headers

Headline:      18px / 28px  | 600 weight | Card titles, buttons
Subheading:    16px / 24px  | 500 weight | Label, emphasis

Body Large:    16px / 24px  | 400 weight | Main content
Body:          14px / 21px  | 400 weight | Body text, descriptions
Body Small:    13px / 20px  | 400 weight | Secondary text

Label:         12px / 18px  | 500 weight | UI labels, badges
Caption:       11px / 17px  | 400 weight | Timestamps, hints
```

### Line Height Philosophy
- Generous line height (1.5–1.7) for readability
- Tighter on headlines (1.2) for impact
- Never less than 1.4× for body text

### Letter Spacing
- Headlines: `-0.5px` (tighter, more impact)
- Body: `0` (neutral, clear)
- Mono: `0` (precision)

### Emphasis & Hierarchy
```css
/* Heavy Emphasis */
font-weight: 600;
color: --neutral-900;
letter-spacing: -0.3px;

/* Standard Emphasis */
font-weight: 500;
color: --neutral-800;

/* Regular */
font-weight: 400;
color: --neutral-700;

/* Deemphasized */
font-weight: 400;
color: --neutral-500;
font-size: 0.9em;
```

---

## Spacing & Layout System

### Philosophy
**Spacing is silence.** It provides breathing room, establishes hierarchy, and guides the eye. We use a consistent scale to create visual harmony.

### Spacing Scale
```css
4px   — Micro gaps (adjacent elements)
8px   — Tight spacing (icon + text, compact groups)
12px  — Standard padding (buttons, small components)
16px  — Default padding (cards, sections)
24px  — Generous spacing (section headers)
32px  — Major breaks (between sections)
48px  — Large breaks (between major sections)
64px  — Hero spacing (page introductions)
```

### Layout Grid
- **Container max-width**: `1240px` (breathing room on desktop)
- **Gutter**: `16px` (consistent margin around content)
- **Column gap**: `24px` (breathing between columns)
- **Row gap**: `24px–48px` (flexible for content rhythm)

### Responsive Breakpoints
```css
mobile:  320px   (phone baseline)
tablet:  768px   (iPad, small laptops)
desktop: 1024px  (standard desktop)
wide:    1440px  (large displays)
```

### Margin & Padding Rules
- **Outside container**: `16px` (mobile), `24px` (tablet), `32px` (desktop)
- **Inside card**: Always `16px` (consistent, predictable)
- **Between elements**: Use spacing scale (8px, 16px, 24px)
- **White space as element**: Never fill empty space just to fill it

---

## Component Design

### Buttons

#### Philosophy
Buttons are **clear calls-to-action**. They're obvious without screaming. Hierarchy is expressed through size and prominence, not color competition.

#### Primary Button
```jsx
<button className="
  px-6 py-3
  bg-blue-600 hover:bg-blue-700
  text-white text-sm font-500
  rounded-lg
  transition-colors duration-150
  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
  disabled:opacity-50 disabled:cursor-not-allowed
">
  Action
</button>
```

**Styling:**
- Background: `--accent-primary`
- Padding: `12px 24px` (generous, touchable)
- Border radius: `8px` (subtle, modern)
- Hover: Darker shade (not brighter)
- Active: Slight scale (0.98) for tactile feedback
- Focus: Ring, never outline (accessible)

#### Secondary Button
```jsx
<button className="
  px-6 py-3
  bg-neutral-200 hover:bg-neutral-300
  text-neutral-900 text-sm font-500
  rounded-lg
  transition-colors duration-150
  focus:outline-none focus:ring-2 focus:ring-neutral-400
">
  Secondary
</button>
```

**Styling:**
- Background: `--neutral-200`
- Text: `--neutral-900`
- Less prominent, but still clear

#### Ghost Button
```jsx
<button className="
  px-4 py-2
  text-neutral-600 hover:text-neutral-900
  hover:bg-neutral-100
  rounded-lg
  transition-colors duration-150
  font-500 text-sm
">
  Ghost
</button>
```

**Styling:**
- No background (invisible until interaction)
- Hover: Subtle background (appears)
- Lowest hierarchy

#### Button Sizes
```
Large:    16px / 12px 28px    (primary CTAs)
Standard: 14px / 12px 24px    (most buttons)
Small:    13px / 8px 16px     (secondary actions)
Icon:     40px × 40px         (icon buttons)
```

### Cards

#### Philosophy
Cards are **containers of content**. They're subtle, refined, and let content shine. Borders are barely perceptible; shadows provide depth through restraint.

```jsx
<div className="
  bg-white
  rounded-lg
  border border-neutral-200
  shadow-sm hover:shadow-md
  transition-shadow duration-200
  p-6
">
  {/* Content */}
</div>
```

**Styling:**
- Background: `--neutral-50`
- Border: `1px solid --neutral-200` (barely visible)
- Shadow: `0 1px 3px rgba(0,0,0,0.05)` (depth without drama)
- Hover shadow: `0 4px 12px rgba(0,0,0,0.08)` (subtle lift)
- Border radius: `8px–12px` (modern, gentle curves)
- Padding: `16px` (consistent breathing room)

### Input Fields

#### Philosophy
Inputs are **conversational**. They invite interaction without demanding it. Focus states are clear but subtle.

```jsx
<input className="
  w-full
  px-4 py-3
  bg-white
  border border-neutral-300 focus:border-blue-600
  rounded-lg
  text-neutral-900 placeholder:text-neutral-500
  focus:outline-none focus:ring-2 focus:ring-blue-500/20
  transition-all duration-150
  text-sm
"
  placeholder="Placeholder text"
/>
```

**Styling:**
- Border: `--neutral-300` (visible but neutral)
- Focus border: `--accent-primary`
- Focus ring: Subtle (20% opacity, not harsh)
- Padding: `12px 16px` (touchable, comfortable)
- Background: `--neutral-50`
- Placeholder: `--neutral-400` (visible, not distracting)

### Badges & Labels

#### Philosophy
Badges are **quick context**. They convey status without intrusion. Color is reserved for semantic meaning.

```jsx
<span className="
  inline-flex items-center
  px-3 py-1.5
  bg-green-100 text-green-700
  rounded-full
  text-xs font-500
  letter-spacing: 0;
">
  Active
</span>
```

**Variants:**
- **Success**: `bg-green-100 text-green-700`
- **Warning**: `bg-orange-100 text-orange-700`
- **Danger**: `bg-red-100 text-red-700`
- **Neutral**: `bg-neutral-200 text-neutral-700`

### Dividers

#### Philosophy
Dividers are **barely there**. They separate content with restraint, never dominating the visual space.

```jsx
<div className="border-t border-neutral-200" />
```

**Styling:**
- Color: `--neutral-200` (subtle)
- Weight: `1px` (never thicker)
- Margin: `16px 0` or `24px 0` (breathing room around)
- Rarely a full-width line; often inset to margins

---

## Interactions & Motion

### Philosophy
Motion is **purposeful**. It guides attention, provides feedback, and feels responsive. We avoid gratuitous animation; every transition earns its place.

### Duration & Easing
```css
/* Micro interactions (state changes) */
--duration-fast: 150ms;
--easing-standard: cubic-bezier(0.4, 0, 0.2, 1);

/* Meaningful transitions (entrance, exit) */
--duration-normal: 250ms;

/* Scenic transitions (page changes) */
--duration-slow: 350ms;
```

### Common Interactions

#### Button Feedback
```css
/* Hover */
transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1);
opacity: 0.85;

/* Active (press) */
transform: scale(0.98);

/* Focus (keyboard) */
outline: 2px solid --accent-primary;
outline-offset: 2px;
```

#### Card Hover
```css
transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1);
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
```

#### Input Focus
```css
border-color: --accent-primary;
box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.1);
transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1);
```

### Entrance Animations
```css
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

/* Apply to elements */
animation: fadeInUp 250ms cubic-bezier(0.4, 0, 0.2, 1);

/* Stagger children */
.item:nth-child(n) {
  animation-delay: calc(n * 50ms);
}
```

### Loading States
```jsx
/* Subtle pulse for loading data */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

<div className="animate-pulse bg-neutral-200 rounded h-8 w-24" />
```

### Disabled States
- Reduce opacity: `opacity: 0.5`
- Change cursor: `cursor: not-allowed`
- Never completely remove—always show something

---

## Glassmorphism & Blur Effects

### Philosophy
Glassmorphism adds **refined depth** without opacity. Use sparingly, only where it enhances clarity and hierarchy.

### Backdrop Blur
```css
/* Subtle background blur (modals, overlays) */
.modal-backdrop {
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
}

/* Glass effect (floating elements) */
.glass {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}
```

### Use Cases
- **Modal backdrops**: Light blur (4px) to show content behind
- **Floating headers**: Glass effect when scrolling
- **Sidebar overlays**: Subtle blur to focus attention
- **Hover states**: Micro glass effect on interactive elements

### Rule: Use Sparingly
- Only 1–2 blur effects per page
- Never use on primary content (buttons, input fields)
- Ensure text readability (contrast ratio 4.5:1 minimum)

---

## Dark Mode

### Philosophy
Dark mode is **not inverted colors**. It's a thoughtful redesign that maintains hierarchy and warmth.

### Color Adjustments
```css
:root.dark {
  --background:     #0a0a0a;
  --surface:        #1a1a1a;
  --surface-alt:    #262626;
  --text-primary:   #f5f5f5;
  --text-secondary: #a6a6a6;
  --border:         #3a3a3a;
  --accent-primary: #0b84ff;  /* Slightly brighter blue */
}
```

### Dark Mode Adjustments
- Backgrounds: Soften from pure black to `#0a0a0a` (less harsh)
- Text: Use `#f5f5f5` not `#ffffff` (easier on eyes)
- Borders: More visible (`#3a3a3a`) than light mode
- Shadows: Soften (dark on dark is less visible)
- Accents: Slightly brighten for contrast

### Card Styling (Dark)
```jsx
<div className="
  dark:bg-neutral-900 dark:border-neutral-800
  dark:shadow-md dark:shadow-black/30
">
  {/* Content */}
</div>
```

### Input Styling (Dark)
```jsx
<input className="
  dark:bg-neutral-800
  dark:border-neutral-700
  dark:text-neutral-50
  dark:placeholder:text-neutral-500
  dark:focus:border-blue-500
"
/>
```

---

## Implementation Guidelines

### Tailwind Configuration
```javascript
// tailwind.config.js
export default {
  theme: {
    extend: {
      colors: {
        neutral: {
          50: '#fafafa',
          100: '#f5f5f5',
          200: '#e8e8e8',
          // ... full scale
          900: '#161616',
        },
        blue: {
          600: '#0071e3', // accent-primary
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
        sm: '6px',
        md: '8px',
        lg: '12px',
      },
      transitionDuration: {
        fast: '150ms',
        normal: '250ms',
        slow: '350ms',
      },
    },
  },
};
```

### CSS Variables
```css
:root {
  --color-primary: #0071e3;
  --color-success: #34c759;
  --color-warning: #ff9500;
  --color-danger: #ff3b30;

  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 12px;
  --spacing-lg: 16px;
  --spacing-xl: 24px;

  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --easing: cubic-bezier(0.4, 0, 0.2, 1);
}
```

### React Component Pattern
```jsx
// Keep components simple and semantic
export function Button({ variant = 'primary', size = 'md', ...props }) {
  const baseClass = 'font-500 transition-all duration-fast rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2';

  const variants = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-neutral-200 text-neutral-900 hover:bg-neutral-300 focus:ring-neutral-400',
    ghost: 'text-neutral-600 hover:bg-neutral-100 focus:ring-neutral-400',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-6 py-3 text-sm',
    lg: 'px-8 py-4 text-base',
  };

  return (
    <button className={`${baseClass} ${variants[variant]} ${sizes[size]}`} {...props} />
  );
}
```

---

## Accessibility

### Contrast & Readability
- **Minimum WCAG AA**: 4.5:1 for text
- **Enhanced (AAA)**: 7:1 for critical information
- Test with tools: WebAIM Contrast Checker, Polychroma

### Focus States
- Always visible (ring or outline)
- Never remove default focus (replace, don't hide)
- Keyboard navigation: Tab through all interactive elements

### Color Alone
- Never convey information with color alone
- Use icons, text labels, or patterns alongside color
- Example: "✓ +2.4% (green)" instead of just green

### Motion & Animation
- Respect `prefers-reduced-motion`
- Provide static alternatives
- Keep animations under 500ms for accessibility

### Mobile & Touch
- Buttons: Minimum 44px × 44px (Apple standard)
- Spacing: More generous on mobile
- Text: Minimum 16px (prevents iOS zoom)

---

## Do's & Don'ts

### ✅ DO

- **Embrace white space** — Let elements breathe
- **Use consistent spacing** — Follow the scale religiously
- **Prioritize clarity** — Every design choice should have purpose
- **Test on real devices** — Especially mobile and touch
- **Keep interactions subtle** — Motion guides, doesn't distract
- **Use semantic colors** — Green for good, red for caution
- **Simplify ruthlessly** — Remove every element you can live without
- **Document patterns** — Make consistency easy to repeat

### ❌ DON'T

- **Add decorative elements** — No ornaments, only function
- **Use multiple accent colors** — One primary per context
- **Ignore focus states** — Accessibility is not optional
- **Animate everything** — Restraint is sophistication
- **Use low-contrast text** — Always test readability
- **Break the spacing scale** — Consistency beats uniqueness
- **Make users think** — Interactions should be obvious
- **Skimp on padding** — Breathing room is luxury

---

## Design Checklist

- [ ] Color palette follows neutral + accent rule
- [ ] Typography hierarchy is clear (scale, weight, color)
- [ ] Spacing uses consistent 8px grid
- [ ] All buttons are accessible (WCAG AA minimum)
- [ ] Focus states are visible and consistent
- [ ] Hover states are subtle (not dramatic)
- [ ] Motion respects `prefers-reduced-motion`
- [ ] Dark mode maintains hierarchy
- [ ] Mobile breakpoints tested (320px, 768px, 1024px)
- [ ] Touch targets are 44px+ on mobile
- [ ] Contrast ratios pass WCAG AA (4.5:1)
- [ ] Icons are consistent (style, weight, size)
- [ ] Loading states are clear
- [ ] Error messages are helpful, not harsh
- [ ] Empty states are thoughtful (not blank)

---

## Resources & References

- **Apple Design System**: https://developer.apple.com/design/
- **Dieter Rams: Ten Principles of Good Design**: https://www.vitsoe.com/us/article/ten-principles-good-design
- **Steve Jobs on Design**: https://www.youtube.com/watch?v=kxF2oJ7Yy64
- **Jony Ive on Simplicity**: https://www.youtube.com/watch?v=EHRx9drUhGU
- **WCAG Accessibility Guidelines**: https://www.w3.org/WAI/WCAG21/quickref/

---

## Summary

This design guide is a living document. As we build Nirvana, we'll discover patterns and refine our approach. But our north star remains constant:

**Simplicity through thoughtfulness. Elegance through restraint. Beauty through clarity.**

Every design decision should answer: *Does this serve the user?* If not, remove it.

---

*Last Updated: March 2026*
*Version: 1.0*
