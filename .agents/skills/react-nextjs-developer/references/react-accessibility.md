# React Accessibility

Prefer semantic HTML before adding ARIA. Use native `button`, `a`, `input`,
`select`, `dialog`, headings, lists, and landmarks when they match the behavior.
In JSX, `aria-*` attributes keep their hyphenated spelling.

For a custom interactive pattern:

1. Follow the relevant WAI-ARIA Authoring Practices pattern.
2. Implement its keyboard interaction, focus movement, roles, states, and
   properties together.
3. Keep the accessible name stable and associate labels, descriptions, and
   errors with native IDs.
4. Test with role/name queries, keyboard input, focus assertions, and at least
   one browser-level flow.

Do not replace a native control with a custom ARIA implementation for styling
alone. Do not add a headless component package without explicit approval. If the
project already uses one, follow its documented composition and preserve its
keyboard behavior.

For dynamic status or validation feedback, use an appropriate live region and
avoid moving focus unless the interaction requires it.

Official references:
[React DOM components](https://react.dev/reference/react-dom/components) and
[WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/patterns/).
