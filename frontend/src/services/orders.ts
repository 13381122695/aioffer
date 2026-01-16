/**
 * 订单管理API服务
 * 创建日期: 2025-01-08
 * 用途: 处理订单创建、支付、查询等相关操作
 */

import { http } from '@/utils/request';

export interface Order {
  id: number;
  order_no: string;
  user_id: number;
  username: string;
  amount: number;
  points: number;
  status: 'pending' | 'paid' | 'cancelled' | 'refunded';
  payment_method: string;
  description?: string;
  paid_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateOrderParams {
  amount: number;
  points: number;
  payment_method: string;
  description?: string;
}

export interface OrderListParams {
  page?: number;
  size?: number;
  status?: string;
  user_id?: number;
  start_date?: string;
  end_date?: string;
  search?: string;
}

export interface OrderListResponse {
  items: Order[];
  total: number;
  page: number;
  size: number;
}

export interface PaymentParams {
  order_id: number;
  payment_method: string;
  return_url?: string;
}

export interface PaymentResponse {
  payment_url: string;
  payment_id: string;
}

export interface Product {
  id: number;
  name: string;
  type: string;
  price: number;
  description?: string;
  duration?: number;
  points?: number;
}

export interface AlipayRechargeResponse {
  order_id: number;
  order_no: string;
  pay_url: string;
  alipay_scheme?: string;
}

/**
 * 创建订单
 */
export const createOrder = async (params: CreateOrderParams): Promise<Order> => {
  return http.post('/orders/', params);
};

/**
 * 获取订单列表
 */
export const getOrderList = async (params: OrderListParams = {}): Promise<OrderListResponse> => {
  return http.get('/orders/', { params });
};

/**
 * 获取订单详情
 */
export const getOrderById = async (id: number): Promise<Order> => {
  return http.get(`/orders/${id}`);
};

/**
 * 发起支付
 */
export const initiatePayment = async (params: PaymentParams): Promise<PaymentResponse> => {
  return http.post('/orders/payment', params);
};

/**
 * 确认支付
 */
export const confirmPayment = async (payment_id: string): Promise<Order> => {
  return http.post('/orders/payment/confirm', { payment_id });
};

/**
 * 取消订单
 */
export const cancelOrder = async (id: number): Promise<Order> => {
  return http.post(`/orders/${id}/cancel`);
};

/**
 * 申请退款
 */
export const refundOrder = async (id: number, reason?: string): Promise<Order> => {
  return http.post(`/orders/${id}/refund`, { reason });
};

/**
 * 获取订单统计
 */
export const getOrderStats = async (): Promise<{
  total_orders: number;
  total_amount: number;
  pending_orders: number;
  completed_orders: number;
}> => {
  return http.get('/orders/stats');
};

/**
 * 获取支付配置
 */
export const getPaymentConfig = async (): Promise<{
  enabled_methods: string[];
  config: Record<string, unknown>;
}> => {
  return http.get('/orders/payment-config');
};

export const getProducts = async (): Promise<Product[]> => {
  return http.get('/orders/products/list');
};

export const createAlipayRecharge = async (params: {
  product_id: number;
  amount?: number;
  client_type?: 'pc' | 'h5';
}): Promise<AlipayRechargeResponse> => {
  return http.post('/recharge/alipay/create', params);
};
