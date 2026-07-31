---
name: hooks
description: >
  Write the hook that owns a screen's state: the data it fetches through a
  service, its loading and error flags, and every handler the UI calls.
  Covers the plain hook and the context that wraps it when sibling
  components share the same state. Use when the user asks to "create hook",
  "write hook", "add hook", "new hook", or "create context".
---

# Writing a hook

Follow these rules whenever you add a hook, using `template.tsx` as the base. Assume React 18+ with TypeScript.

A hook is where **all** the logic of a screen lives — state, effects, handlers and exception handling — so the component it feeds is nothing but a render function. `template.tsx` shows a `useProducts` that lists products and a `ProductsContext` that shares it; the entity is **illustrative, not required**. The service it calls comes from the `services` skill and the component that consumes it from the `components` skill.

## Rules

1. **All state and all effects live in the hook.** `useState`, `useEffect`, `useMemo`, refs — if a component declares one, it is doing the hook's job.
2. **Return a named object, never a tuple.** `{ products, isLoading, error, refresh }` — the caller destructures what it needs, and adding a key never breaks an existing consumer.
3. **Always expose data, loading and error.** Three states, so the component can tell "still loading" from "loaded and empty" from "the request died". Initialize `isLoading` to `true` when the hook fetches on mount.
4. **The hook calls a service, never the transport.** No `axios`, no `fetch`, no URL, no auth header — `ProductService.list()`. The hook receives the domain model (`IProduct`) and never the raw API shape.
5. **Catch here, once.** The `try`/`catch` that turns a rejection into `error` state belongs in the hook. This is the only layer that handles exceptions, which is why no component ever needs one.
6. **Handlers belong to the hook.** `refresh`, `removeProduct`, `openPreview` are functions the hook returns; the component only wires `onClick={removeProduct}`.
7. **Stabilize what you return.** Wrap returned functions in `useCallback` with real dependencies, so a child that takes one as a prop does not re-render on every keystroke, and an effect that depends on one does not loop.
8. **Reach for a context only when siblings share the state.** The provider calls the very same hook and publishes its return value unchanged — a context adds distribution, not logic. The hook must still work standalone.
9. **`useXxxContext` throws outside its provider.** Guard on `undefined` and throw a named error, so a misplaced component fails with a message instead of `Cannot read property of undefined`.

## File layout

```
src/
  hooks/
    useProducts.ts               # state + effects + handlers for one screen
  contexts/
    products.context.tsx         # ProductsProvider + useProductsContext
  app/
    routes.tsx                   # where the provider is mounted
  services/
    product.service.ts           # from the `services` skill
```

## Counter-example: don't leave the logic in the component

❌ **Bad** — the component owns the state, the effect and the failure:

```tsx
const ProductList = () => {
  const [products, setProducts] = useState<IProduct[]>([]);

  useEffect(() => {
    ProductService.list()
      .then(setProducts)
      .catch(() => setProducts([]));
  }, []);

  return (
    <ul>
      {products.map((product) => (
        <li key={product.id}>{product.name}</li>
      ))}
    </ul>
  );
};
```

✅ **Good** — the hook owns them, the component reads three flags:

```tsx
const ProductList = () => {
  const { products, isLoading, error } = useProducts();

  if (isLoading) return <ProductListSkeleton />;
  if (error) return <ErrorState message={error} />;

  return (
    <ul>
      {products.map((product: IProduct) => (
        <li key={product.id}>{product.name}</li>
      ))}
    </ul>
  );
};
```

The bad version swallows the failure into an empty list, so nobody can tell "no products" from "the request died", and it renders that empty list for a frame before the data arrives. It also cannot be reused: the second screen that needs products copies the same `useState` + `useEffect` + `catch`, and from then on the two drift apart. The good version cannot: the logic has exactly one home, and the component is a render function.
