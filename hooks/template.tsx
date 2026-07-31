import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
// The service and the domain model come from the `services` skill.
import { ProductService } from '@/services/product.service';
import { IProduct } from '@/types/product';
// The page comes from the `components` skill.
import { ProductsPage } from '@/pages/ProductsPage';

// ═════════════════════════════════════════════════════════════
// hooks/useProducts.ts
// ═════════════════════════════════════════════════════════════

export function useProducts() {
  const [products, setProducts] = useState<IProduct[]>([]);
  // Starts true: the hook fetches on mount, so the first render is a load.
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // The only layer that turns a rejection into UI state.
  const loadProducts = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      setProducts(await ProductService.list());
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : 'Could not load products');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  // Mutations are handlers on the hook, not callbacks written in the JSX.
  const removeProduct = useCallback(async (id: string) => {
    try {
      await ProductService.remove(id);
      setProducts((current: IProduct[]) => current.filter((product: IProduct) => product.id !== id));
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : 'Could not remove the product');
    }
  }, []);

  return {
    products,
    isLoading,
    error,
    refresh: loadProducts,
    removeProduct,
  };
}

// ═════════════════════════════════════════════════════════════
// contexts/products.context.tsx
// ═════════════════════════════════════════════════════════════

// Derived from the hook, so the context can never drift from what it shares.
type ProductsContextValue = ReturnType<typeof useProducts>;

const ProductsContext = createContext<ProductsContextValue | undefined>(undefined);

interface IProductsProviderProps {
  children: React.ReactNode;
}

// The provider adds distribution, not logic: same hook, published to the tree.
export const ProductsProvider = ({ children }: IProductsProviderProps) => {
  const products = useProducts();

  return <ProductsContext.Provider value={products}>{children}</ProductsContext.Provider>;
};

export const useProductsContext = (): ProductsContextValue => {
  const context = useContext(ProductsContext);

  // A misplaced component fails here, with a name, instead of on undefined.
  if (!context) {
    throw new Error('useProductsContext must be used inside <ProductsProvider>');
  }

  return context;
};

// ═════════════════════════════════════════════════════════════
// app/routes.tsx
// ═════════════════════════════════════════════════════════════

// Mounted as high as the siblings that share the state, and no higher.
export const ProductsRoute = () => (
  <ProductsProvider>
    <ProductsPage />
  </ProductsProvider>
);
