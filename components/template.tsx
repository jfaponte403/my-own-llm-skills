// The hook, the provider and the context come from the `hooks` skill.
import { useProducts } from '@/hooks/useProducts';
import { ProductsProvider, useProductsContext } from '@/contexts/products.context';
// The domain model comes from the `services` skill: already mapped, ready to render.
import { IProduct } from '@/types/product';

// ═════════════════════════════════════════════════════════════
// pages/ProductsPage.tsx
// ═════════════════════════════════════════════════════════════

// The page only composes: it mounts the provider so both children share one state.
export const ProductsPage = () => (
  <ProductsProvider>
    <div className="flex-1 p-8 bg-background">
      <div className="max-w-4xl mx-auto space-y-6">
        <ProductToolbar />
        <ProductList />
      </div>
    </div>
  </ProductsProvider>
);

// ═════════════════════════════════════════════════════════════
// components/products/ProductList.tsx
// ═════════════════════════════════════════════════════════════

export const ProductList = () => {
  const { products, isLoading, error, removeProduct } = useProductsContext();

  // Loading and error leave before the happy path, never as a ternary around it.
  if (isLoading) {
    return <p className="text-muted-foreground">Loading products…</p>;
  }

  if (error) {
    return <p className="text-destructive">{error}</p>;
  }

  return (
    <div className="grid grid-cols-2 gap-6">
      {products.map((product: IProduct) => (
        // Keyed by the entity id: an index would re-use the wrong node on delete.
        <ProductCard key={product.id} product={product} onRemove={removeProduct} />
      ))}
    </div>
  );
};

// ═════════════════════════════════════════════════════════════
// components/products/ProductToolbar.tsx
// ═════════════════════════════════════════════════════════════

export const ProductToolbar = () => {
  // Identical to a hook-backed component: only this line changes.
  const { products, isLoading, refresh } = useProductsContext();

  return (
    <div className="flex items-center justify-between">
      <h1 className="text-3xl font-bold text-foreground">Products ({products.length})</h1>

      <button
        type="button"
        onClick={refresh}
        disabled={isLoading}
        className="h-9 px-4 rounded-xl bg-ai-primary text-white text-sm hover:opacity-95 disabled:opacity-50"
      >
        Refresh
      </button>
    </div>
  );
};

// ═════════════════════════════════════════════════════════════
// components/products/ProductCard.tsx
// ═════════════════════════════════════════════════════════════

export interface IProductCardProps {
  product: IProduct;
  onRemove: (id: string) => void;
}

// A leaf: props in, JSX out, no hook — reusable and testable on its own.
export const ProductCard = ({ product, onRemove }: IProductCardProps) => (
  <article className="p-6 rounded-xl border border-border bg-ai-surface">
    <img src={product.imageUrl} alt={product.name} className="w-full h-40 object-cover rounded-lg" />

    <h2 className="mt-4 text-xl font-semibold text-foreground">{product.name}</h2>
    <p className="text-muted-foreground">{product.description}</p>

    {/* Formatted once by the mapper, never here. */}
    <p className="mt-2 text-lg text-ai-primary">{product.formattedPrice}</p>

    <button
      type="button"
      onClick={() => onRemove(product.id)}
      className="mt-4 h-9 px-4 rounded-xl border border-border text-sm hover:bg-background"
    >
      Delete
    </button>
  </article>
);

// ═════════════════════════════════════════════════════════════
// components/products/ProductPicker.tsx
// ═════════════════════════════════════════════════════════════

export interface IProductPickerProps {
  onPick: (product: IProduct) => void;
}

// Same shape as ProductList, backed by the plain hook: this widget owns its
// own state instead of sharing the page's, so only the first line differs.
export const ProductPicker = ({ onPick }: IProductPickerProps) => {
  const { products, isLoading, error } = useProducts();

  if (isLoading) {
    return <p className="text-muted-foreground">Loading products…</p>;
  }

  if (error) {
    return <p className="text-destructive">{error}</p>;
  }

  return (
    <ul className="divide-y divide-border">
      {products.map((product: IProduct) => (
        <li key={product.id}>
          <button
            type="button"
            onClick={() => onPick(product)}
            className="w-full px-4 py-3 text-left text-foreground hover:bg-background"
          >
            {product.name} — {product.formattedPrice}
          </button>
        </li>
      ))}
    </ul>
  );
};
