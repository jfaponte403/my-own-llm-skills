// The HTTP client and the auth config are written once per project.
import { ApiClient, getAuthConfig } from './apiClient';

// ═════════════════════════════════════════════════════════════
// types/product.ts
// ═════════════════════════════════════════════════════════════

// Raw: exactly what the API returns — snake_case, everything may be missing.
export interface IProductRaw {
  product_id?: string;
  name?: string;
  description?: string;
  price?: string;
  image_url?: string;
  created_at?: string;
}

// Domain: what the UI consumes — camelCase, no optionals, ready to render.
export interface IProduct {
  id: string;
  name: string;
  description: string;
  price: number;
  formattedPrice: string;
  imageUrl: string;
  createdAt: string;
}

// Request: body sent to the API on create
export interface ICreateProductRequest {
  name: string;
  description: string;
  price: number;
}

// Request: body sent on update — every field optional, so clients can patch
export type IUpdateProductRequest = Partial<ICreateProductRequest>;

// ═════════════════════════════════════════════════════════════
// services/mappers/product.mapper.ts
// ═════════════════════════════════════════════════════════════

// Built once at module level: rebuilding it per item is expensive.
const priceFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
});

// The single place that absorbs the API shape: renames, missing fields,
// prices that travel as strings, and every derived display value.
export const mapProduct = (raw: IProductRaw): IProduct => {
  const price = parseFloat(raw.price || '0');

  return {
    id: raw.product_id || '',
    name: raw.name || '',
    description: raw.description || '',
    price,
    formattedPrice: priceFormatter.format(price),
    imageUrl: raw.image_url || '',
    createdAt: raw.created_at || '',
  };
};

// The other direction: domain request -> the body the API expects.
export const mapCreateProductRequest = (request: ICreateProductRequest): IProductRaw => ({
  name: request.name,
  description: request.description,
  price: String(request.price),
});

// ═════════════════════════════════════════════════════════════
// services/product.service.ts
// ═════════════════════════════════════════════════════════════

export const ProductService = {
  async list(): Promise<IProduct[]> {
    const response = await ApiClient.get<IProductRaw[]>('/products', getAuthConfig());
    return response.data.map(mapProduct);
  },

  async get(id: string): Promise<IProduct> {
    const response = await ApiClient.get<IProductRaw>(`/products/${id}`, getAuthConfig());
    return mapProduct(response.data);
  },

  async create(request: ICreateProductRequest): Promise<IProduct> {
    const response = await ApiClient.post<IProductRaw>(
      '/products',
      mapCreateProductRequest(request),
      getAuthConfig()
    );
    return mapProduct(response.data);
  },

  async update(id: string, request: IUpdateProductRequest): Promise<IProduct> {
    const response = await ApiClient.put<IProductRaw>(`/products/${id}`, request, getAuthConfig());
    return mapProduct(response.data);
  },

  // Nothing to map: the endpoint answers 204.
  async remove(id: string): Promise<void> {
    await ApiClient.delete(`/products/${id}`, getAuthConfig());
  },
};
