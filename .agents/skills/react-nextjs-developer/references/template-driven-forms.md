# Native Uncontrolled Forms

Use native uncontrolled controls for simple forms. Give every submitted control
a `name` and read values from `FormData` in the action or submit handler.

```tsx
export function SearchForm() {
  return (
    <form action="/search">
      <label htmlFor="query">Search</label>
      <input id="query" name="query" type="search" required />
      <button type="submit">Search</button>
    </form>
  );
}
```

Use `defaultValue` or `defaultChecked` for initial uncontrolled values. Do not
later switch the same input to controlled ownership.

Prefer native validation attributes for immediate browser feedback, but repeat
all validation on the server. Use semantic labels, fieldsets, legends, and
described error messages. Avoid imperative DOM reads when `FormData` is enough.

Official references:
[React form](https://react.dev/reference/react-dom/components/form) and
[Next.js forms](https://nextjs.org/docs/app/guides/forms).
