/**
 * 认证相关API服务
 * 创建日期: 2025-01-08
 * 用途: 处理用户登录、注册、刷新token等认证相关操作
 */

import { http } from '@/utils/request';

export interface LoginParams {
  auth_type: 'email' | 'username';
  email?: string;
  username?: string;
  password?: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: number;
    username: string;
    email: string;
    phone?: string;
    avatar?: string;
    role: string;
    is_active: boolean;
    points?: number;
    created_at: string;
  };
}

export interface RegisterParams {
  username: string;
  email: string;
  email_code?: string;
  password: string;
  phone?: string;
  nickname?: string;
  auth_type?: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  expires_in: number;
}

/**
 * 用户登录
 */
export const login = async (params: LoginParams): Promise<LoginResponse> => {
  return http.post('/auth/login', params);
};

/**
 * 用户注册
 */
export const register = async (params: RegisterParams): Promise<LoginResponse> => {
  return http.post('/auth/register', params);
};

/**
 * 刷新访问令牌
 */
export const refreshToken = async (): Promise<RefreshTokenResponse> => {
  return http.post('/auth/refresh');
};

/**
 * 获取用户信息
 */
export const getUserInfo = async (): Promise<LoginResponse['user']> => {
  const profile = await http.get<{
    id: number;
    username: string;
    email: string;
    phone?: string;
    avatar_url?: string;
    is_active: boolean;
    is_admin?: boolean;
    is_member?: boolean;
    created_at: string;
  }>('/auth/profile');

  const role = profile.is_admin ? 'admin' : profile.is_member ? 'member' : 'user';

  return {
    id: profile.id,
    username: profile.username,
    email: profile.email,
    phone: profile.phone,
    avatar: profile.avatar_url,
    role,
    is_active: profile.is_active,
    created_at: profile.created_at,
  };
};

/**
 * 修改密码
 */
export const changePassword = async (params: {
  old_password: string;
  new_password: string;
}): Promise<void> => {
  return http.post('/auth/change-password', params);
};

/**
 * 发送邮箱验证码
 */
export const sendEmailCode = async (email: string): Promise<void> => {
  return http.post('/auth/send-email-code', { email });
};
