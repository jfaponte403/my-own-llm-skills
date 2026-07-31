---
name: services
description: >
  Write services: the object that owns one capability, talks to the
  outside world (an HTTP API, an LLM provider) and hands models back to
  its caller. Covers the frontend service with its mapper (raw API shape
  → UI model) and the backend service with its injected adapters and its
  registry of cases. Use when the user asks to "create service", "write
  service", "add service", or "new service".
---

# Writing a service

Follow these rules whenever you create a service, using `template.ts` (frontend) or `template.py` (backend) as the base. Assume Pydantic v2 on the Python side.

This is the only skill that spans both sides of the stack, because a service is the same idea in both: the caller states *what* it wants, the service knows *how* to get it. `template.ts` shows a `Product` CRUD over `ApiClient`; `template.py` shows a `FileAnalyzerService` that routes each file to a different LLM provider by mime type. Both entities are **illustrative, not required** — the models come from the `models` skill, persistence from the `repository` skill, and on the backend the caller is usually a handler from the `lambdas` skill.

## Rules

1. **One service per capability, not per screen or per handler.** `ProductService` groups everything you can do to a product; `FileAnalyzerService` groups everything you can analyze. A service that exists to serve one component is a function, not a service.
2. **The caller never speaks the transport.** No `fetch`/`axios` inside a React component, no `requests` or provider SDK inside a Lambda handler. If you are writing a URL, a header or an API key outside a service, the service is missing.
3. **Models in, models out — never a raw payload.** The frontend service returns `IProduct`, never `IProductRaw`; the Python service takes a `FileToAnalyze` and returns an `AnalysisResult`, never loose kwargs or a `dict`.
4. **Convert at the boundary with a mapper.** One pure `mapXxx(raw)` function absorbs the API's shape — `snake_case` names, missing fields, prices that travel as strings — and computes every derived display value (`formattedPrice`) once, so no consumer re-derives it. When the API changes, exactly one function changes, and `IProductRaw` never escapes the service: if a component imports it, the decoupling is already gone.
5. **No state and no presentation logic in the service.** The frontend service is a plain object of `async` methods — no React, no hooks, no store writes, no toasts. The caller decides what to render.
6. **Depend on abstractions and inject them.** `FileAnalyzer` is an `ABC`, and each concrete analyzer receives its already-built SDK client through the constructor. A class that reads its own API key or builds its own client cannot be tested without the network.
7. **Extend by registering, not by editing.** When a service handles several cases, each case is a class the service receives in a registry and looks up by a key taken from the input: `FileAnalyzerService` maps `application/pdf` → OpenAI, `image/png` → Gemini, `text/plain` → Claude. Supporting a new type is a new class plus one line at the composition root — never a new `if`/`elif` inside the service.
8. **The result shape is the service's, not the provider's.** Every analyzer returns the same `AnalysisResult` whichever SDK produced it, so swapping a provider is one line at the composition root and no caller notices.
9. **Errors propagate; the service doesn't swallow them.** Let the request reject, let the SDK raise, raise `UnsupportedFileType` on an unregistered key. `@http_validator` on the backend and the error boundary on the frontend decide what the user sees — a service that returns `null` on failure hides the reason.

## File layout

```
# frontend (TypeScript)
src/
  types/
    product.ts                     # IProductRaw (API) + IProduct (UI) + requests
  services/
    apiClient.ts                   # shared client + getAuthConfig (once per project)
    mappers/
      product.mapper.ts            # mapProduct: raw -> domain
    product.service.ts             # ProductService: list/get/create/update/remove

# backend (Python)
models/
  analysis/
    file_to_analyze.py             # input model
    analysis_result.py             # output model, same for every provider
services/
  file_analyzer.py                 # the port: mime types + provider + analyze
  analyzers/
    pdf_analyzer.py                # application/pdf -> OpenAI
    image_analyzer.py              # image/* -> Gemini
    text_analyzer.py               # text/plain -> Claude
  file_analyzer_service.py         # the capability: registry + dispatch
```

## Counter-example: don't call the API straight from the component

❌ **Bad** — the component owns the transport and re-derives the format:

```tsx
const ProductList = () => {
  const [products, setProducts] = useState<any[]>([]);

  useEffect(() => {
    axios.get('/products', { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => setProducts(res.data))
      .catch(() => setProducts([]));
  }, []);

  return (
    <ul>
      {products.map((p) => (
        <li key={p.product_id}>
          {p.name} — ${parseFloat(p.price || '0').toFixed(2)}
        </li>
      ))}
    </ul>
  );
};
```

✅ **Good** — the service owns the call and the shape, the hook owns the state, the component owns the render:

```tsx
// hooks/useProducts.ts — from the `hooks` skill
export function useProducts() {
  const [products, setProducts] = useState<IProduct[]>([]);

  useEffect(() => {
    ProductService.list().then(setProducts);
  }, []);

  return { products };
}

// components/products/ProductList.tsx — from the `components` skill
const ProductList = () => {
  const { products } = useProducts();

  return (
    <ul>
      {products.map((product) => (
        <li key={product.id}>
          {product.name} — {product.formattedPrice}
        </li>
      ))}
    </ul>
  );
};
```

The bad version spreads the API's `product_id`/`price` naming across every component that renders a product, formats the price differently in each one, hard-codes the auth header next to the JSX, and swallows the failure into an empty list so nobody can tell "no products" from "the request died". The good version cannot: the component only ever sees `IProduct`, and renaming a field in the API is one edit in the mapper.

Where the state and the failure go from there is the `hooks` skill's job — the hook above is trimmed to the seam, and a real one also returns `isLoading` and `error`.
