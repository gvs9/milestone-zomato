---
name: Culinary Intelligence System
colors:
  surface: '#11131a'
  surface-dim: '#11131a'
  surface-bright: '#373941'
  surface-container-lowest: '#0c0e15'
  surface-container-low: '#191b22'
  surface-container: '#1d1f26'
  surface-container-high: '#282a31'
  surface-container-highest: '#33343c'
  on-surface: '#e2e2ec'
  on-surface-variant: '#e4bebc'
  inverse-surface: '#e2e2ec'
  inverse-on-surface: '#2e3038'
  outline: '#ab8987'
  outline-variant: '#5b403f'
  surface-tint: '#ffb3b1'
  primary: '#ffb3b1'
  on-primary: '#680011'
  primary-container: '#ff535a'
  on-primary-container: '#5b000e'
  inverse-primary: '#bb162c'
  secondary: '#edc157'
  on-secondary: '#3f2e00'
  secondary-container: '#906d00'
  on-secondary-container: '#fff7ee'
  tertiary: '#4ae183'
  on-tertiary: '#003919'
  tertiary-container: '#00a657'
  on-tertiary-container: '#003115'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdad8'
  primary-fixed-dim: '#ffb3b1'
  on-primary-fixed: '#410007'
  on-primary-fixed-variant: '#92001c'
  secondary-fixed: '#ffdf9b'
  secondary-fixed-dim: '#edc157'
  on-secondary-fixed: '#251a00'
  on-secondary-fixed-variant: '#5b4300'
  tertiary-fixed: '#6bfe9c'
  tertiary-fixed-dim: '#4ae183'
  on-tertiary-fixed: '#00210c'
  on-tertiary-fixed-variant: '#005228'
  background: '#11131a'
  on-background: '#e2e2ec'
  surface-variant: '#33343c'
typography:
  display-lg:
    fontFamily: Outfit
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Outfit
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  headline-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 20px
  margin-mobile: 16px
  margin-desktop: 64px
---

## Brand & Style

The design system is engineered for a premium food discovery experience, blending high-end editorial aesthetics with cutting-edge AI utility. The target audience is the discerning foodie who values speed, visual delight, and hyper-personalized recommendations.

The style is **Modern / Glassmorphic**, utilizing deep layered surfaces and subtle translucent overlays to create a sense of immersion. The emotional response should be one of "effortless luxury"—where the interface recedes to let high-resolution food photography take center stage, supported by a sophisticated dark UI that feels like a private members' club.

## Colors

The palette is centered on a "Deep Night" foundation to make the "Zomato Red" pop with intensity. 

- **Primary (Zomato Red):** Reserved for high-intent actions and brand moments.
- **Secondary (Gold):** Specifically for ratings, achievement badges, and premium tiering.
- **Neutral/Surface:** Uses a slight blue-tinted charcoal to prevent the "dead" look of pure black, maintaining a modern tech feel.
- **Success/Warning:** Used sparingly for status updates like "Order Confirmed" or "Limited Availability."

Apply a 5% white overlay on top of surface colors for interactive hover states to maintain depth without shifting hues.

## Typography

This design system uses a dual-font strategy. **Outfit** provides a geometric, high-energy feel for headlines, reflecting the modernity of the AI. **Inter** is utilized for all functional text and body copy to ensure maximum legibility at smaller sizes and during long-form reading of menus or reviews.

Use `display-lg` exclusively for hero sections and AI-generated "Big Reveal" recommendations. Ensure `label-sm` is always used with 0.05em letter spacing when in uppercase to maintain readability on dark backgrounds.

## Layout & Spacing

The layout follows a **Fluid Grid** model with high internal breathing room. 

- **Desktop:** 12-column grid with 20px gutters. Content is centered with a max-width of 1280px.
- **Mobile:** 4-column grid with 16px margins. 

Spacing follows a 4px baseline. Use `lg` (24px) for padding within restaurant cards and `xl` (32px) for vertical section spacing. AI chat interfaces should utilize "No Grid" contextual layouts, where messages are grouped with `xs` (8px) spacing and different intent blocks are separated by `md` (16px).

## Elevation & Depth

Hierarchy is established through **Tonal Layers** and **Ambient Shadows**. 

- **Level 0 (Background):** #0F1117 (The canvas).
- **Level 1 (Cards/Surfaces):** #1A1C23. These should have a subtle 1px border (#2D3039) to define edges against the background.
- **Level 2 (Modals/Popovers):** #252832. These use "Super-diffused" shadows: `0 20px 40px rgba(0,0,0,0.5)`.

To emphasize AI elements, use a "Glow" effect: a primary-colored drop shadow with 20% opacity and 30px blur. Glassmorphism (Backdrop-filter: blur(12px)) should be applied to top navigation bars and bottom mobile sheets to maintain context of the content beneath.

## Shapes

The design system employs a **Rounded** shape language to feel approachable and friendly, mirroring the organic nature of food.

- **Cards:** 16px radius. This larger radius creates a "premium container" look for food imagery.
- **Buttons:** 12px radius. Provides a distinct tactile feel, separating them from the sharper layout containers.
- **Inputs:** 10px radius. Balanced for form-factor efficiency.

Interactive elements (chips) should use a fully pill-shaped (100px) radius to signify clickability.

## Components

### Buttons
- **Primary:** Background #E23744, Text #FAFAFA. No border. On hover, background shifts to #FF4154 with a subtle glow.
- **Secondary:** Transparent background, 1px border #2D3039. Text #FAFAFA.
- **Ghost:** No background or border. Text #A0A8B4. For low-priority actions like "Cancel".

### Cards
Restaurant cards must feature a full-bleed image at the top (aspect ratio 16:9). The content area uses #1A1C23. Ratings (Gold #FFD166) are always placed in the top-right corner of the image within a semi-transparent dark glass blur tag.

### Inputs
Search bars and AI prompts use #1A1C23 with a 1px #2D3039 border. Upon focus, the border transitions to #E23744. Placeholder text remains #A0A8B4.

### Chips/Filters
Used for cuisine types. Inactive: #1A1C23 background, #A0A8B4 text. Active: #E23744 background, #FAFAFA text.

### AI Recommender Tray
A unique component utilizing a thin gradient border (Zomato Red to Gold) to distinguish AI-curated suggestions from standard search results.