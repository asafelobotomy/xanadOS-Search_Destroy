---
applyTo: "**/src/**/*.{tsx,jsx,vue,svelte,HTML}"
---

# Frontend/Accessibility-specific Copilot Instructions

- Follow WCAG 2.1 AA accessibility standards for all user-facing components
- Include alt text for images and aria-labels for interactive elements
- Test with keyboard navigation; ensure all interactive elements are focusable
- Ensure color contrast ratios meet WCAG standards (4.5:1 for normal text, 3:1 for large text)
- Use semantic HTML elements (button, nav, main, section, article) over generic divs
- Implement proper heading hierarchy (h1-h6) without skipping levels
- Add focus indicators that are visible and meet contrast requirements
- Use aria-describedby for form validation messages and help text
- Provide loading states and error messages that are announced to screen readers
- Test with screen readers (VoiceOver, NVDA, JAWS) and include findings in PR descriptions
