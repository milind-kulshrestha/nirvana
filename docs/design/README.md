# Nirvana Design System

Welcome to Nirvana's design system—a comprehensive guide to building beautiful, functional interfaces inspired by Apple, Jony Ive, and Dieter Rams.

## The Philosophy

> *"Simplicity is the ultimate sophistication."* — Steve Jobs

Nirvana is designed around **elegant simplicity**. Every pixel, every color, every interaction is thoughtfully crafted to serve the user. We believe that great design is invisible—it gets out of the way and lets content shine.

Our approach is rooted in three foundational principles:

1. **Function First** — Form follows function rigorously
2. **Clarity Over Decoration** — Remove everything unnecessary
3. **Precision in Details** — Excellence in every interaction

## What's in This Folder

### 📖 [DESIGN_GUIDE.md](./DESIGN_GUIDE.md)
**Start here.** The comprehensive design philosophy document covering:
- Core design principles
- Color system (palette, usage rules, psychology)
- Typography system (fonts, scale, hierarchy)
- Spacing & layout (grid, responsive breakpoints)
- Component design (buttons, cards, inputs, badges, dividers)
- Interactions & motion (transitions, animations, easing)
- Glassmorphism & blur effects
- Dark mode implementation
- Accessibility guidelines
- Implementation checklists

**Read this first to understand the "why" behind our design decisions.**

### ⚙️ [TAILWIND_CONFIG.md](./TAILWIND_CONFIG.md)
**Implementation reference.** Complete Tailwind configuration and CSS variables:
- Full `tailwind.config.js` with color palette, spacing, and typography
- `src/index.css` with CSS layers and utility classes
- Dark mode configuration
- Ready-to-use component classes (`.btn`, `.card`, `.input`, `.badge`, etc.)
- Quick reference guide

**Copy these configurations into your project and you're ready to build.**

### 🎨 [COMPONENT_EXAMPLES.md](./COMPONENT_EXAMPLES.md)
**Code templates.** Production-ready React component examples:
- Button (variants, sizes, disabled states)
- Card (header, body, footer)
- Input & Textarea
- Badge (status indicators)
- Modal (dialog with backdrop)
- Navigation (header with mobile menu)
- Form (validation, error handling)
- Data Table (scannable layout)
- Empty State (helpful guidance)
- Loading State (skeleton & spinner)

**Copy these components into your codebase as starting points. Adapt as needed while maintaining design principles.**

## Quick Start

### For Designers
1. Read [DESIGN_GUIDE.md](./DESIGN_GUIDE.md) for philosophy and principles
2. Understand color psychology and typography hierarchy
3. Use this as a reference when creating designs or critiquing work
4. Ensure all mockups follow spacing scale and color rules

### For Developers
1. Copy Tailwind config from [TAILWIND_CONFIG.md](./TAILWIND_CONFIG.md)
2. Update `tailwind.config.js` with color palette and spacing scale
3. Update `src/index.css` with provided CSS layers
4. Reference [COMPONENT_EXAMPLES.md](./COMPONENT_EXAMPLES.md) when building components
5. Use component templates as starting points

### For Product Managers
1. Skim [DESIGN_GUIDE.md](./DESIGN_GUIDE.md) to understand the design language
2. Reference [COMPONENT_EXAMPLES.md](./COMPONENT_EXAMPLES.md) to understand what's possible
3. When requesting features, consider how they fit into the design system
4. Use design principles as a framework for prioritization

## Design Principles at a Glance

### Simplicity Over Decoration
```
❌ Remove: Decorative flourishes, unnecessary colors, ornamental elements
✅ Keep: Elements that serve function, purposeful whitespace, essential interactions
```

### Human-Centered Clarity
```
❌ Don't: Overwhelm with options, bury important information, require guessing
✅ Do: Guide with clear hierarchy, make actions obvious, provide helpful feedback
```

### Precision & Polish
```
❌ Avoid: Rough edges, inconsistent spacing, sloppy interactions
✅ Aim for: Precise alignment, consistent padding, refined transitions
```

### Function First
```
❌ Don't: Choose form before thinking about function
✅ Do: Let function determine visual hierarchy and interaction patterns
```

### Timeless Over Trendy
```
❌ Skip: Gimmicks, novelty for novelty's sake, dated trends
✅ Invest in: Fundamentals, elegant restraint, graceful aging
```

## Color System at a Glance

### Palette
- **Neutral (85%)**: Grayscale foundation (`--neutral-50` to `--neutral-900`)
- **Primary (10%)**: Apple Blue (`#0071e3`) for actions and focus
- **Semantic (5%)**: Green (success), Orange (warning), Red (danger)

### Usage Rule
- Start with neutral
- Add primary for CTAs
- Use semantic colors only for status/emotion
- Never use more than one primary accent per view

## Typography at a Glance

### Font Stack
System fonts only: `-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`

### Scale
- **Display 2XL** (42px): Page title, hero
- **Display Large** (28px): Section header
- **Headline** (18px): Card title, emphasis
- **Body** (14px): Main content
- **Label** (12px): UI labels, badges
- **Caption** (11px): Timestamps, hints

### Hierarchy
Use weight (400, 500, 600) and color (neutral-900, neutral-700, neutral-500) to establish hierarchy, not size alone.

## Spacing System at a Glance

```
4px   (xs)   — Micro gaps
8px   (sm)   — Tight spacing
12px  (md)   — Standard
16px  (lg)   — Default
24px  (xl)   — Generous
32px  (2xl)  — Major breaks
48px  (3xl)  — Section separation
64px  (4xl)  — Hero spacing
```

**Rule**: Use this scale consistently. Never guess at spacing values.

## Component Checklist

When building any component, ensure it has:

- [ ] **Clear purpose** — What problem does it solve?
- [ ] **Semantic HTML** — Using correct elements (`<button>`, `<input>`, etc.)
- [ ] **Accessible focus** — Keyboard navigation, clear focus states
- [ ] **Responsive design** — Works on 320px, 768px, 1024px+
- [ ] **Dark mode** — All variants in light and dark
- [ ] **Hover states** — Subtle feedback, not jarring
- [ ] **Disabled state** — Clearly communicated, not removed
- [ ] **Error handling** — Clear error messages, not alerts
- [ ] **Loading states** — Skeletons or spinners, not blank
- [ ] **Empty states** — Helpful guidance, not blank screens

## Design Audit Checklist

Before shipping any UI:

- [ ] All text meets WCAG AA contrast (4.5:1 minimum)
- [ ] Focus states are visible and consistent
- [ ] Spacing uses the system grid (no random values)
- [ ] Colors follow palette rules (neutral + accent + semantic)
- [ ] Typography follows scale (no custom sizes)
- [ ] Dark mode maintains hierarchy and readability
- [ ] Mobile tested at 320px, 768px, 1024px
- [ ] No decorative elements (everything serves function)
- [ ] Interactions are subtle (150-250ms transitions)
- [ ] Buttons are 44px+ on mobile (touch-friendly)

## Common Patterns

### Button Hierarchy
```
Primary (strong CTA)   → bg-primary text-white
Secondary (alt CTA)    → bg-neutral-200 text-neutral-900
Ghost (minimal)        → text-neutral-600 hover:bg-neutral-100
Danger (destructive)   → bg-danger text-white
```

### Data Presentation
```
Positive   → Green (#34c759)
Negative   → Red (#ff3b30)
Neutral    → Gray (#7a7a7a)
Warning    → Orange (#ff9500)
```

### Layout Rhythm
```
Content blocks:  24-32px separation
Related groups:  16px separation
Adjacent items:  8-12px separation
```

## Tools & Resources

### Color Contrast
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Polychroma Color Tool](https://www.polychroma.app/)

### Accessibility
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Apple Accessibility Guidelines](https://developer.apple.com/accessibility/)

### Design Inspiration
- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [Dieter Rams: Ten Principles of Good Design](https://www.vitsoe.com/us/article/ten-principles-good-design)
- [Steve Jobs on Design](https://www.youtube.com/watch?v=kxF2oJ7Yy64)

### Development
- [Tailwind CSS Documentation](https://tailwindcss.com)
- [Radix UI (headless components)](https://www.radix-ui.com)
- [Lucide Icons](https://lucide.dev)

## FAQ

### Should I use dark mode?
Yes. Provide both light and dark automatically using CSS class strategy. Use `dark:` prefix in Tailwind.

### Can I customize components?
Yes, but stay within the design system. Don't invent new colors, spacing values, or animations. If you need something new, propose it to the team.

### What about animations?
Keep them subtle (150-250ms) and purposeful. Avoid decorative flourishes. Always respect `prefers-reduced-motion`.

### How do I handle loading states?
Use skeleton screens for expected content, spinners for uncertain duration. Always show something—never a blank space.

### Can I deviate from the palette?
Only with team discussion. The palette is deliberately constrained. Constraints drive creativity and consistency.

### What about the AI Sidebar?
The AI Sidebar should use the same color system as the rest of the app. Move away from hardcoded white + indigo toward integrated design.

## Contributing to the Design System

Found an issue? Want to propose a change? Here's how:

1. **Discuss** — Bring up the topic in design/dev sync
2. **Test** — Implement as variant or proposal
3. **Validate** — Ensure WCAG AA, mobile-friendly, accessible
4. **Document** — Update relevant guide (DESIGN_GUIDE.md, TAILWIND_CONFIG.md, or COMPONENT_EXAMPLES.md)
5. **Share** — Show the team and gather feedback

---

## Summary

This design system is our north star. It's not restrictive—it's liberating. By agreeing on principles and patterns, we can move faster and build more cohesively.

**Remember**: The goal is not to make everything look the same, but to make everything *feel* the same. Users should feel the care, precision, and thoughtfulness in every interaction.

**Every design decision should answer one question: Does this serve the user?**

If not, remove it.

---

## Document Structure

```
docs/design/
├── README.md                    (this file)
├── DESIGN_GUIDE.md              (philosophy, principles, system)
├── TAILWIND_CONFIG.md           (implementation configuration)
└── COMPONENT_EXAMPLES.md        (production-ready components)
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | March 2026 | Initial design system created |

---

*Last Updated: March 2026*

*"The design of the world is in the details." — Steve Jobs*
