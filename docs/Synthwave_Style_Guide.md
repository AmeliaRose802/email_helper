# 🪩 Synthwave App Style Guide  
**For:** Design team  
**Purpose:** Maintain a cohesive retro-futuristic synthwave aesthetic across UI, marketing, and iconography for the AI email processing app.

---

## 🎨 Color Palette

### Core Brand Colors
| Name | Hex | Usage |
|------|-----|--------|
| **Neon Magenta** | `#FF00E6` | Primary brand color, CTA glow |
| **Electric Cyan** | `#00E6FF` | Secondary accent, highlights |
| **Hyper Violet** | `#7A2CF7` | Gradient midpoint, UI depth |
| **Sunset Orange** | `#FF6A00` | Warm accent / success color |
| **Aurora Yellow** | `#FFC857` | Alert / highlight accent |
| **Night Navy** | `#0B0B2B` | Primary background |
| **Deep Plum** | `#2B0A3D` | Secondary background |

### Chrome Accents
| Name | Hex | Usage |
|------|-----|--------|
| **Chrome Light** | `#E0F7FF` | Metallic shine |
| **Chrome Mid** | `#A8D8F8` | Edge gradient |
| **Chrome Dark** | `#6BA7C8` | Shadowed chrome |

### Neutrals
| Name | Hex | Usage |
|------|-----|--------|
| **Onyx** | `#0B0B17` | Dark surfaces |
| **Graphite** | `#1E1E2A` | Panels, inputs |
| **Slate** | `#34344A` | Secondary surfaces |
| **Fog** | `#A1A1B5` | Muted text |
| **Mist** | `#D8D8E8` | Primary text |
| **Pure White** | `#FFFFFF` | Highlights |

### Optional Accent
| Name | Hex | Usage |
|------|-----|--------|
| **Microsoft Blue** | `#0078D4` | Optional Outlook nod |

---

## 🌅 Gradients

| Name | Description | CSS |
|------|--------------|-----|
| **Brand Neon** | Magenta → Cyan glow | `linear-gradient(135deg, #FF00E6 0%, #00E6FF 100%)` |
| **Sunset Horizon** | Warm sunset fade | `linear-gradient(180deg, #FF6A00 0%, #FF2E88 45%, #7A2CF7 100%)` |
| **Neon Orbit** | Deep space atmosphere | `radial-gradient(circle at 50% 120%, #7A2CF7 0%, rgba(122,44,247,0) 60%), linear-gradient(135deg, #00E6FF, #FF00E6)` |

---

## ✨ Effects

**Text Glow (Magenta)**
```
text-shadow: 0 0 6px #FF00E6, 0 0 16px rgba(255,0,230,0.8), 0 0 36px rgba(255,0,230,0.4);
```

**Outline Glow (Cyan)**
```
box-shadow: 0 0 0 2px #00E6FF inset, 0 0 12px #00E6FF, 0 0 28px rgba(0,230,255,0.6);
```

**Chrome Shine**
```
box-shadow: inset 0 1px 0 #E0F7FF, inset 0 -1px 0 #6BA7C8;
```

---

## 🔠 Typography

| Type | Font | Use | Notes |
|------|------|-----|-------|
| **Primary** | Inter / SF Pro | Body, UI | Clean, legible |
| **Display** | Orbitron / Michroma | Titles, logos | Adds retro flair |
| **Weights** | 400 / 600 / 800 | | |
| **Tracking** | +0.2–0.4px | | Retro tech feel |

---

## 🧩 Components

### Buttons

| Type | Background | Text | Glow |
|------|-------------|------|------|
| **Primary CTA** | Brand Neon gradient | Dark (Onyx) | Magenta glow |
| **Secondary** | Deep Plum | White | Cyan outline |

**Hover:** 2% scale up, brighter glow  
**Active:** return to base size, dim glow

---

### Cards / Panels

- Background: plum → navy gradient, 85% opacity  
- Border: subtle 1px white (10% opacity)  
- Shadow: violet glow + black soft shadow  
- Optional chrome top-line: `#E0F7FF`

---

### Inputs

- BG: Graphite  
- Border: 1px solid Slate  
- Focus: Cyan outline glow

---

### Icons & Favicon

- Simplify to **1–2 colors** (magenta + cyan).  
- Avoid text below 24px.  
- Favicon (16×16): one envelope or AI node glyph, **high contrast**, soft outer glow only.  

---

## ⚡ Motion

| Property | Value |
|-----------|--------|
| Duration | 180–220ms |
| Curve | `cubic-bezier(0.22, 1, 0.36, 1)` |
| Hover | Scale 1.02 + 5% brightness |
| Active | Scale 0.99, reduce glow |

---

## 🔲 Layout & Spacing

| Property | Value |
|-----------|--------|
| **Grid** | 8pt base |
| **Radius** | 14–20px (rounded-2xl) |
| **Spacing** | 4, 8, 12, 16, 24, 32, 48px |

---

## 🧠 Accessibility

- Use high-contrast text (Magenta/Cyan on Navy = ✅)  
- Add outlines for focus states  
- Disable glow animations when `prefers-reduced-motion` is enabled  
- Avoid pure magenta on plum without outline

---

## ✅ Do / 🚫 Don’t

**Do**
- Pair magenta and cyan for hero moments  
- Keep UI clean, balanced with dark space  
- Use chrome edges to create depth

**Don’t**
- Layer multiple glows of different hues  
- Use gradients on text longer than one word  
- Overcrowd icons with small details

---

## 💾 Assets

| Type | Resolution | Description |
|------|-------------|-------------|
| **App Icon** | 1024×1024 | Full neon grid + sunset |
| **Favicon** | 64×64 / 32×32 / 16×16 | Minimal envelope or AI node |
| **Logo Lockup** | SVG | Wordmark with magenta glow |

---

## 🧩 Implementation References

- CSS variable tokens: `tokens.css`  
- Tailwind extension: `tailwind.config.js`  
- Icon glow example: `.icon-neon { color: var(--clr-cyan); text-shadow: 0 0 8px #00E6FF; }`

---

*Designed for visual clarity, futuristic optimism, and nostalgic retro-tech energy.*
