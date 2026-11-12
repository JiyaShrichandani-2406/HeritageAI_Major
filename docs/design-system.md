# HeritageAI – Frontend Design System

## 1. Overview

The HeritageAI Design System defines the common visual styles and reusable UI components used throughout the HeritageAI application.

The frontend follows **Option B** of the approved HeritageAI UI design reference. It uses a warm heritage-inspired visual theme to reflect Indian culture, monuments, and historical places.

### Objectives
- Maintain a consistent UI across all frontend pages.
- Provide reusable React components.
- Improve readability and accessibility.
- Make collaboration between frontend team members easier.
- Avoid duplicate styling and inconsistent designs.

## 2. Technology Stack

| Technology | Purpose |
|---|---|
| React | Frontend UI development |
| Vite | Development server and build tool |
| Tailwind CSS | Styling and responsive layouts |
| React Router | Page navigation |
| Axios | Backend API communication |
| Lucide React | Icons |
| React Leaflet | Interactive maps |

## 3. Color Palette

The following initial color tokens are used throughout the frontend.

| Token | Hex Code | Purpose |
|---|---|---|
| Heritage Primary | #A64B2A | Primary buttons and highlights |
| Heritage Secondary | #E8D5B7 | Secondary buttons and backgrounds |
| Heritage Background | #FAF7F0 | Main page background |
| Heritage Accent | #C49A45 | Decorative highlights |
| Heritage Text | #292929 | Main text |
| Heritage Success | #39734D | Success and verified states |

These are implementation color values selected to reflect the approved warm heritage aesthetic. They are not claimed to be exact pixel samples from the design reference.

## 4. Typography

Two font families are used:

### Headings
- Font: Playfair Display
- Usage: Page titles, section headings, and important titles.

### Body Text
- Font: DM Sans
- Usage: Paragraphs, labels, descriptions, buttons, and form fields.

## 5. Spacing and Layout

Follow these general layout guidelines:

- Use consistent padding inside cards and sections.
- Maintain sufficient spacing between different UI elements.
- Use rounded corners for cards and buttons.
- Keep layouts clean and readable.
- Use responsive layouts for desktop, tablet, and mobile screens.

### Border Radius
- Cards: 16px
- Buttons and inputs: 10px

## 6. Reusable UI Components

All shared UI components are located in:

`frontend/src/components/ui/`

### Button.jsx

Reusable button component.

Supported variants:
- primary
- secondary
- outline

Example:

```jsx
import { Button } from "./components/ui";

<Button variant="primary">Explore Heritage</Button>
<Button variant="secondary">Cancel</Button>
<Button variant="outline">Learn More</Button>
```

### Card.jsx

Reusable container for displaying information.

Example:

```jsx
import { Card } from "./components/ui";

<Card>
  <h2>Heritage Monument</h2>
  <p>Explore Indian cultural heritage.</p>
</Card>
```

### Badge.jsx

Used to display information status.

Supported variants:
- default
- success
- warning
- danger
- verified
- estimated
- unknown

Example:

```jsx
import { Badge } from "./components/ui";

<Badge variant="verified">Verified</Badge>
<Badge variant="estimated">Estimated</Badge>
<Badge variant="unknown">Unknown</Badge>
```

### Input.jsx

Reusable input field for search and forms.

Example:

```jsx
import { Input } from "./components/ui";

<Input
  label="Search Monuments"
  placeholder="Enter monument name..."
/>
```

## 7. Component Imports

The shared components can be imported using:

```jsx
import {
  Button,
  Card,
  Badge,
  Input
} from "./components/ui";
```

The exports are maintained in:

`frontend/src/components/ui/index.js`

## 8. Information Status Guidelines

For data reliability and transparency, use the following status labels:

| Status | Meaning |
|---|---|
| Verified | Information supported by a verified source |
| Estimated | Approximate information that is not fully verified |
| Unknown | Information is currently unavailable or unverified |

Do not display estimated or unknown information as verified.

## 9. Responsive Design Guidelines

- Use flexible layouts instead of fixed-width page containers.
- Ensure buttons and input fields remain usable on smaller screens.
- Stack cards vertically on narrow screens.
- Keep navigation accessible on mobile devices.
- Ensure text remains readable at different screen sizes.

## 10. Development Guidelines for Team Members

1. Reuse existing UI components wherever possible.
2. Avoid creating duplicate Button, Card, Badge, or Input components.
3. Follow the shared color and typography tokens.
4. Maintain consistent spacing and rounded corners.
5. Keep page-specific components separate from shared UI components.
6. Test layouts on different screen sizes.
7. Coordinate changes to shared files with the frontend integrator.

## 11. Folder Structure

```text
frontend/
└── src/
    ├── components/
    │   └── ui/
    │       ├── Button.jsx
    │       ├── Card.jsx
    │       ├── Badge.jsx
    │       ├── Input.jsx
    │       └── index.js
    ├── App.jsx
    └── index.css

docs/
└── design-system.md
```

## 12. Ownership

**Responsible Member:** Member 1 – UI/UX Research and Frontend Foundation

**Deliverables:**
- Shared design system documentation.
- Color and typography guidelines.
- Reusable UI components.
- Component export structure.
- Initial component testing.

---

**Project:** HeritageAI – AI-Powered Indian Cultural Heritage Explorer Using RAG  
**Document:** Frontend Design System  
**Status:** Initial implementation completed