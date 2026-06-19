# 🎨 Design System & Visual Identity: Universal Stock

This document covers the UI/UX design choices, styling tokens, glassmorphism specs, and visual assets designed for the **Universal Stock** frontend dashboard.

---

## 1. Visual Philosophy: Premium Glassmorphism Dark Mode

The interface uses a tailored dark mode theme designed to feel premium, deep, and cohesive. It shifts away from pure black `#000` or plain gray backgrounds, using HSL-based dark blue-gray tints combined with semi-transparent frosted-glass overlays (glassmorphism).

```css
/* Color Palette - Custom HSL Variables */
:root {
  --bg-main: hsl(230, 25%, 8%);         /* Deep Obsidian Blue Background */
  --panel-bg: rgba(20, 24, 45, 0.55);   /* Translucent Frosted Glass Card */
  --panel-border: rgba(255, 255, 255, 0.08); /* Soft glass outline */
  
  --primary: hsl(184, 100%, 50%);       /* Vibrant Cyan - Interactive */
  --primary-glow: rgba(0, 240, 255, 0.3);
  
  --secondary: hsl(270, 85%, 65%);     /* Electric Purple - Accents & Gradients */
  --success: hsl(150, 100%, 50%);       /* Neon Green - Positive Stock Mut */
  --danger: hsl(345, 100%, 60%);        /* Coral Red - Stock Depletion & Alerts */
  
  --text-main: hsl(210, 30%, 96%);      /* Crisp Off-White */
  --text-muted: hsl(215, 15%, 60%);     /* Neutral Muted Gray */
}
```

### Glassmorphism Card Formula:
To create the "frosted glass" depth, every panel relies on a layered combination of backing blur, semi-transparent background, subtle outer outline, and micro-shadowing:
```css
.glass-panel {
  background: var(--panel-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--panel-border);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  border-radius: 16px;
  padding: 1.5rem;
}
```

---

## 2. Layout & Typography

The application utilizes a responsive dashboard layout designed to adapt seamlessly across desktop monitors, tablets, and mobile phones.

*   **Desktop Layout:** Displays a fixed left-side navigation sidebar (`width: 260px`) and a scrollable main content area (`margin-left: 260px`, `width: calc(100% - 260px)`).
*   **Mobile Layout (Viewport < 768px):**
    - **Header Bar:** A top-floating `60px` header bar with a frosted glass backdrop (`rgba(15, 17, 26, 0.8)` + `backdrop-filter: blur(12px)`) and a vibrant primary-colored hamburger button (☰).
    - **Drawer Sidebar:** The sidebar slides in from the left on request (`transform: translateX(-100%)` transitioning to `translateX(0)` when opened). It features a manual close button (✕) and is locked with a z-index of 100.
    - **Backdrop Overlay:** A semi-transparent blurred backdrop overlay covers the active page content (`backdrop-filter: blur(4px)`) and intercepts click events to close the drawer automatically if a tap occurs outside the navigation menu.
*   **Grid Systems:** Grid structures use dynamic layouts (e.g., `grid-template-columns: repeat(auto-fit, minmax(240px, 1fr))`) to adapt dynamically without layout fragmentation.
*   **Responsive Table Scrolling:** All tables are wrapped in a container class (`.table-container` or `.table-responsive-container`) with `overflow-x: auto` and `-webkit-overflow-scrolling: touch` enabled. This isolates wider tables, allowing smooth finger-swipe horizontal scrolling on mobile viewports without warping the main grid boundaries.
*   **Typography:** The font system is loaded from Google Fonts:
    - **Outfit:** Used for main page headers, card values, and key titles (gives a high-tech modern appeal).
    - **Inter:** Used for body texts, descriptions, and data tables (provides readable, clean proportions).
    - **Monospace Code Fonts:** (e.g., Fira Code, JetBrains Mono) reserved for SKU numbers and security API keys.

---

## 3. Micro-Animations & Skeleton Shimmers

An interface that feels alive encourages interaction and gives quick system updates. The system employs three key animation styles:

### A. Skeleton Shimmer Loading Screen
To prevent layout jumps when fetching asynchronously, we avoid crude "Loading..." texts, replacing them with pulsing light skeletons mimicking the visual structures:

```css
@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.skeleton {
  background: linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.03) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite linear;
  border-radius: 4px;
}
```

### B. WebSocket Stock Mutation Flashing
When another user updates stock quantities on the backend, rows in the active inventory table update in real-time with a momentary visual glow:
*   **Stock IN (Positive Mutation):** Row turns translucent green and fades out back to normal over 1.5 seconds.
*   **Stock OUT (Negative Mutation):** Row turns translucent red and fades out back to normal over 1.5 seconds.

---

## 4. Performance Optimization: Native React-SVG Charts

Traditional chart libraries (e.g., Chart.js, Recharts) are heavy and drastically degrade edge compilation, JS bundle size, and load times. 

To maintain excellent edge page load performance (first contentful paint under **100ms** on Vercel), we designed the dashboard graphs using **native inline React-SVG graphics**.

```xml
<svg viewBox="0 0 600 200" width="100%" height="100%">
  <!-- Scaled dynamically based on transactions -->
  <rect x="60" y="30" width="18" height="120" fill="var(--primary)" rx="3" />
  <rect x="82" y="50" width="18" height="100" fill="var(--danger)" rx="3" />
</svg>
```

### Advantages of Native SVGs:
1.  **Lightweight:** Weighs less than `1KB` of code, saving ~150KB of JavaScript libraries.
2.  **Fully Styled with CSS:** Chart bars react to color tokens, transition timers, and hover changes directly.
3.  **Responsive Scaling:** Vector scaling automatically fits parent divs without recalculations.
4.  **No Canvas Lag:** Renders cleanly at any zoom level or high-DPI screens.
