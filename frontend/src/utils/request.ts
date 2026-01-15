/**
 * HTTP请求工具
 * 创建日期: 2025-01-08
 * 用途: 基于axios封装的统一HTTP请求工具，支持认证、错误处理等
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores/auth';

type MessageLike = {
  error: (content: unknown) => void;
  success: (content: unknown) => void;
  warning: (content: unknown) => void;
  info: (content: unknown) => void;
};

type ApiResponse<T = unknown> = {
  code: number;
  message?: string;
  data?: T;
  detail?: unknown;
};

type ValidationErrorItem = {
  msg?: string;
  message?: string;
};

const isApiResponse = (value: unknown): value is ApiResponse => {
  if (!value || typeof value !== 'object') return false;
  return 'code' in value;
};

const isValidationErrorItem = (value: unknown): value is ValidationErrorItem => {
  return !!value && typeof value === 'object' && ('msg' in value || 'message' in value);
};

const getValidationErrorMessage = (value: unknown): string | null => {
  if (!value || typeof value !== 'object') return null;
  if (!('detail' in value)) return null;
  const detail = (value as { detail?: unknown }).detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .filter(isValidationErrorItem)
      .map((err) => err.msg || err.message)
      .filter((v): v is string => typeof v === 'string' && v.length > 0);
    return messages.length ? messages.join('\n') : null;
  }
  return null;
};

// 动态消息实例，用于解决 Antd v5 静态方法警告
const silentMessage: MessageLike = {
  error: () => {},
  success: () => {},
  warning: () => {},
  info: () => {},
};

let message: MessageLike = silentMessage;

export const initGlobalMessage = (msgInstance: MessageLike) => {
  message = msgInstance;
};

const normalizeBaseUrl = (url: string) => {
  if (!url) return '';
  return url.endsWith('/') ? url.slice(0, -1) : url;
};

const resolveApiBaseUrl = () => {
  if (import.meta.env.DEV) {
    return '';
  }

  const rawBaseUrl = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL || '');
  const isLocalTarget = rawBaseUrl.includes('localhost') || rawBaseUrl.includes('127.0.0.1');
  const isLocalHost =
    typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

  if (import.meta.env.DEV && isLocalTarget && !isLocalHost) {
    return '';
  }

  return rawBaseUrl;
};

// API基础配置
const API_BASE_URL = resolveApiBaseUrl();

// 创建axios实例
const request: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 添加认证token
    const token = useAuthStore.getState().token;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    // 统一处理响应数据
    const { data } = response;
    
    // 如果后端返回的是标准格式，直接返回data
    if (isApiResponse(data)) {
      if (data.code === 200 || data.code === 0) {
        return data.data;
      } else {
        // 业务错误
        const msg = data.message || '操作失败';
        message.error(msg);
        return Promise.reject(new Error(msg));
      }
    }
    
    return data;
  },
  (error: AxiosError) => {
    const { response } = error;
    
    if (response) {
      const { status, data } = response;
      
      switch (status) {
        case 401:
          // 未授权，清除token并跳转到登录页
          useAuthStore.getState().logout();
          message.error('登录已过期，请重新登录');
          window.location.href = '/login';
          break;
          
        case 403:
          message.error('没有权限访问该资源');
          break;
          
        case 404:
          message.error('请求的资源不存在');
          break;
          
        case 422:
          // 验证错误
          message.error(getValidationErrorMessage(data) || '参数验证失败');
          break;
          
        case 500:
          message.error('服务器内部错误');
          break;
          
        default:
          if (isApiResponse(data) && data.message) {
            message.error(data.message);
          } else {
            message.error('网络错误');
          }
      }
    } else {
      message.error('网络连接失败');
    }
    
    return Promise.reject(error);
  }
);

// 封装请求方法
export const http = {
  get: <T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    return request.get<unknown, T>(url, config);
  },
  
  post: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> => {
    return request.post<unknown, T>(url, data, config);
  },
  
  put: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> => {
    return request.put<unknown, T>(url, data, config);
  },
  
  delete: <T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    return request.delete<unknown, T>(url, config);
  },
  
  patch: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> => {
    return request.patch<unknown, T>(url, data, config);
  },
};

export default request;
