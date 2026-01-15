/**
 * 用户管理API服务
 * 创建日期: 2025-01-08
 * 用途: 处理用户管理、会员管理、点数充值等相关操作
 */

import { http } from '@/utils/request';

export interface User {
  id: number;
  username: string;
  email?: string;
  full_name?: string;
  phone?: string;
  avatar_url?: string;
  status: number;
  user_type: number;
  points?: number;
  created_at: string;
  updated_at: string;
  member?: {
    id: number;
    member_level: number;
    points: number;
    balance: number;
    expired_at: string;
    is_expired: boolean;
    is_valid_member: boolean;
  };
}

export interface UserListParams {
  page?: number;
  size?: number;
  search?: string;
  status?: number;
  user_type?: number;
}

export interface UserListResponse {
  items: User[];
  total: number;
  page: number;
  size: number;
}

export interface CreateUserParams {
  username: string;
  email: string;
  password: string;
  phone?: string;
  user_type?: number;
  is_active?: boolean;
}

export interface UpdateUserParams {
  username?: string;
  email?: string;
  phone?: string;
  user_type?: number;
  is_active?: boolean;
  avatar_url?: string;
}

export interface RechargePointsParams {
  user_id: number;
  points: number;
  amount: number;
  payment_method: string;
  description?: string;
}

export interface PointTransaction {
  id: number;
  user_id: number;
  points: number;
  type: number;
  type_text: string;
  balance_after: number;
  amount?: number;
  description: string;
  created_at: string;
}

export interface PointTransactionListResponse {
  items: PointTransaction[];
  total: number;
  page: number;
  size: number;
}

/**
 * 获取用户列表
 */
export const getUserList = async (params: UserListParams): Promise<UserListResponse> => {
  return http.get('/users/', { params });
};

/**
 * 获取用户详情
 */
export const getUserById = async (id: number): Promise<User> => {
  return http.get(`/users/${id}`);
};

/**
 * 创建用户
 */
export const createUser = async (params: CreateUserParams): Promise<User> => {
  return http.post('/users/', params);
};

/**
 * 更新用户信息
 */
export const updateUser = async (id: number, params: UpdateUserParams): Promise<User> => {
  return http.put(`/users/${id}`, params);
};

/**
 * 删除用户
 */
export const deleteUser = async (id: number): Promise<void> => {
  return http.delete(`/users/${id}`);
};

/**
 * 用户点数充值
 */
export const rechargePoints = async (params: RechargePointsParams): Promise<void> => {
  return http.post('/users/recharge-points', params);
};

/**
 * 获取用户点数交易记录
 */
export const getPointTransactions = async (
  userId: number,
  params: { page?: number; size?: number }
): Promise<PointTransactionListResponse> => {
  return http.get(`/users/${userId}/points`, { params });
};

/**
 * 获取当前用户信息
 */
export const getCurrentUser = async (): Promise<User> => {
  return http.get('/auth/profile');
};

/**
 * 获取用户统计数据
 */
export const getUserStats = async (): Promise<{
  total_users: number;
  active_users: number;
  new_users_today: number;
  total_points: number;
}> => {
  return http.get('/users/stats');
};

// 新增：交易记录相关

export interface Transaction {
  id: number;
  user_id: number;
  username?: string | null;
  type: number;
  type_text: string;
  points: number;
  balance_after: number;
  amount?: number;
  description?: string;
  created_at: string;
}

export interface TransactionListResponse {
  items: Transaction[];
  total: number;
  page: number;
  size: number;
}

/**
 * 获取所有交易记录
 */
export const getAllTransactions = async (params: { page?: number; size?: number; user_id?: number; type?: number } = {}): Promise<TransactionListResponse> => {
  return http.get('/users/transactions', { params });
};
