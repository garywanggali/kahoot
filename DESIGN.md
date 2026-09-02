# Kahoot OpenDesign System Specification

> Version: 1.0.0-trial
> Workspace: kahoot
> Status: Draft on `feat/opendesign-ui`

This document defines the core visual design tokens, interactive components, micro-animations, and typography contracts for the Kahoot quiz platform based on OpenDesign principles.

---

## 1. Design Tokens

### Color System
```css
:root {
  /* Brand Accents (Kahoot Classic 4-Colors) */
  --kh-red: #E21B3C;
  --kh-red-dark: #B80F2A;
  --kh-blue: #1368CE;
  --kh-blue-dark: #0B4A99;
  --kh-yellow: #FFA602;
  --kh-yellow-dark: #D48800;
  --kh-green: #26890C;
  --kh-green-dark: #196105;

  /* Theme Surfaces (Dark Vibe & Glassmorphism) */
  --bg-primary: #120926;
  --bg-secondary: #1F1142;
  --bg-surface: rgba(255, 255, 255, 0.08);
  --bg-surface-hover: rgba(255, 255, 255, 0.14);
  --border-glass: rgba(255, 255, 255, 0.12);
  --border-glass-glow: rgba(255, 255, 255, 0.28);

  /* Typography Colors */
  --text-primary: #FFFFFF;
  --text-secondary: rgba(255, 255, 255, 0.75);
  --text-muted: rgba(255, 255, 255, 0.50);

  /* Feedback Colors */
  --feedback-correct: #26890C;
  --feedback-wrong: #E21B3C;
  --badge-gold: #FFD700;
  --badge-silver: #C0C0C0;
  --badge-bronze: #CD7F32;
}
```

### Typography
- **Primary Headings & Game Stats**: `'Outfit', -apple-system, sans-serif` (Weights: 600, 700, 900)
- **Body & Controls**: `'Inter', system-ui, -apple-system, sans-serif` (Weights: 400, 500, 600)
- **Monospace/PINs**: `'Outfit', 'SF Mono', monospace` (Letter-spacing: 0.15em)

---

## 2. Component Design Specifications

### 1. Game Canvas & Background
- Rich radial & linear gradient (`radial-gradient(circle at 50% 0%, #301768 0%, #120926 70%)`).
- Floating ambient glow particles for dynamic atmosphere.

### 2. Glassmorphism Card
- Background: `rgba(255, 255, 255, 0.08)`
- Backdrop-filter: `blur(20px)`
- Border: `1px solid rgba(255, 255, 255, 0.14)`
- Border radius: `24px`
- Box shadow: `0 24px 48px -12px rgba(0, 0, 0, 0.5)`

### 3. Tactile 3D Answer Buttons
- **4 Shapes / Icons**:
  - A (Red): ▲ Triangle
  - B (Blue): ◆ Diamond
  - C (Yellow): ● Circle
  - D (Green): ■ Square
- **Tactile Effect**:
  - `box-shadow: 0 6px 0 var(--dark-accent)`
  - Active: `transform: translateY(4px); box-shadow: 0 2px 0 var(--dark-accent)`
- **Hover**: Brightness +5%, subtle upward elevation.

### 4. Countdown Timer Bar
- Smooth color transition gradient: Emerald (100%~50%) -> Yellow (50%~20%) -> Coral Pulse (20%~0%).
- Rounded pill shape with glowing progress indicator.

### 5. Leaderboard & Podium
- Top 3 rank highlighting:
  - 1st: Gold gradient + subtle trophy badge
  - 2nd: Silver gradient
  - 3rd: Bronze gradient
- Score transition with smooth slide-in animation.

### 6. Danmaku Floating Stream
- Translucent capsule chips with glowing border and player name badges.
- Smooth floating upward animation with staggered paths.

---

## 3. Responsive Breakpoints
- **Mobile (< 768px)**: Full-bleed 2x2 grid buttons for rapid thumb tapping, enlarged PIN input.
- **Desktop / Screen (> 768px)**: Max width 960px, spacious typography for projector presentation.
