---
name: components
description: >
  Write React components that only render: one call to their hook or their
  context at the top, early returns for loading and error, and JSX with no
  logic in it. Covers the screen component, the presentational leaf that
  takes props only, and the page that mounts a provider. Use when the user
  asks to "create component", "write component", "add component", or "new
  component".
---

# Writing a component

Follow these rules whenever you add a component, using `template.tsx` as the base. Assume React 18+ with TypeScript.

A component renders and nothing else: it calls its hook, returns JSX, and never learns where the data came from. `template.tsx` shows a `ProductList` fed by `useProducts()`, a `ProductToolbar` fed by `useProductsContext()` and a `ProductCard` fed by props — the entity is **illustrative, not required**. Everything the component does not do — state, effects, handlers, exception handling — belongs to the `hooks` skill, and the data it renders was already shaped by the `services` skill's mapper.

## Rules

1. **A component is a render function.** Its body is one hook call and a `return`. No `useState`, no `useEffect`, no `fetch`, no `try`/`catch`.
2. **One line of data dependency.** Destructure everything the component needs from a single `useXxx()` at the top, so its whole input is readable at a glance.
3. **Hook or context is a one-line swap.** A component backed by `useProducts()` becomes a context consumer by changing that single line to `useProductsContext()` — nothing else in the file moves.
4. **Early-return loading and error.** Handle them before the happy-path JSX instead of wrapping the whole tree in ternaries.
5. **No logic inside JSX.** No `.filter()`, `.sort()`, `parseFloat`, `toFixed` or date formatting between the braces — render `{product.formattedPrice}`, which the mapper already computed.
6. **Handlers are references, not bodies.** `onClick={removeProduct}`; if an inline arrow needs more than one statement, that statement belongs in the hook.
7. **A leaf component takes props and nothing else.** `ProductCard` renders what it is given and calls no hook — that is what makes it reusable and testable without mocking a service.
8. **Type props with an exported interface** (`IProductCardProps`) and declare the component as an arrow `const`. Never `React.FC`, never `any`. Annotate the callback parameter as well — `products.map((product: IProduct) => …)` — so the model being rendered is named in the file instead of left to inference.
9. **`key` is a stable id, never the array index.** Reordering or deleting with index keys re-uses the wrong DOM node and keeps stale state in it.

## File layout

```
src/
  pages/
    ProductsPage.tsx             # mounts <ProductsProvider>
  components/
    products/
      ProductList.tsx            # consumes useProductsContext()
      ProductToolbar.tsx         # consumes useProductsContext()
      ProductCard.tsx            # props only, no hook
      ProductPicker.tsx          # owns its state: consumes useProducts()
```

## Counter-example: don't compute inside the JSX

❌ **Bad** — the hook exists, but the component still does the work:

```tsx
const ProductList = () => {
  const { products, removeProduct } = useProducts();

  return (
    <ul>
      {products
        .filter((p) => p.price > 0)
        .sort((a, b) => a.name.localeCompare(b.name))
        .map((p, index) => (
          <li key={index}>
            {p.name} — ${p.price.toFixed(2)}
            <button
              onClick={() => {
                if (window.confirm('Delete?')) {
                  removeProduct(p.id);
                }
              }}
            >
              Delete
            </button>
          </li>
        ))}
    </ul>
  );
};
```

✅ **Good** — everything is already decided by the time the JSX runs:

```tsx
const ProductList = () => {
  const { visibleProducts, isLoading, error, confirmRemove } = useProducts();

  if (isLoading) return <ProductListSkeleton />;
  if (error) return <ErrorState message={error} />;

  return (
    <ul>
      {visibleProducts.map((product: IProduct) => (
        <li key={product.id}>
          {product.name} — {product.formattedPrice}
          <button onClick={() => confirmRemove(product.id)}>Delete</button>
        </li>
      ))}
    </ul>
  );
};
```

The bad version re-runs the filter and the sort on every single render, formats the price its own way so the next component that shows a product formats it differently, hides a confirmation flow inside an `onClick`, and keys the list by index — delete the first row and React keeps its DOM node for the second. None of that can be tested without mounting the component. The good version can: `visibleProducts` and `confirmRemove` are plain values returned by a hook.
