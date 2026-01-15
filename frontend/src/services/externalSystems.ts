/**
 * 外部系统配置API服务
 * 创建日期: 2025-01-08
 * 用途: 处理外部系统配置相关操作
 */

import { http } from '@/utils/request';

export interface ExternalSystem {
  id: number;
  name: string;
  system_type: 'api' | 'page' | 'iframe';
  page_url?: string | null;
  endpoint_url?: string | null;
  api_key?: string | null;
  api_secret?: string | null;
  config?: Record<string, unknown> | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type AccessibleExternalSystem = {
  id: number;
  name: string;
  system_type: 'api' | 'page' | 'iframe';
  page_url?: string | null;
  endpoint_url?: string | null;
  config?: Record<string, unknown> | null;
  is_active?: boolean;
  integration_type?: ExternalSystemIntegrationType;
  description?: string;
  icon?: string;
  is_page_system?: boolean;
  is_api_system?: boolean;
};

export type UserAccessibleExternalSystemsResponse = {
  systems: AccessibleExternalSystem[];
};

export type ExternalSystemAccess = {
  system_id: number;
  user_id: number;
  access_token: string | null;
  expires_at: string | null;
};

export type ExternalSystemIntegrationType = 'iframe' | 'sso' | 'api';

export type ExternalSystemIframeIntegrationConfig = {
  url: string;
  width?: string;
  height?: string;
  allow_fullscreen?: boolean;
  sandbox?: string[];
};

export type ExternalSystemSsoIntegrationConfig = {
  sso_url: string;
  callback_url: string;
  client_id: string;
  client_secret: string;
  scope: string;
};

export type ExternalSystemIntegrationConfigResponse = {
  system_id: number;
  name: string;
  system_type: 'api' | 'page' | 'iframe';
  integration_type: ExternalSystemIntegrationType;
  page_url?: string | null;
  endpoint_url?: string | null;
  config: Record<string, unknown>;
  iframe_config?: ExternalSystemIframeIntegrationConfig;
  sso_config?: ExternalSystemSsoIntegrationConfig;
};

export interface ExternalSystemListResponse {
  items: ExternalSystem[];
  total: number;
  page: number;
  size: number;
}

export interface CreateExternalSystemParams {
  name: string;
  system_type: 'api' | 'page' | 'iframe';
  page_url?: string;
  endpoint_url?: string;
  api_key?: string;
  api_secret?: string;
  config?: Record<string, unknown>;
  is_active?: boolean;
}

export interface UpdateExternalSystemParams {
  name?: string;
  system_type?: 'api' | 'page' | 'iframe';
  page_url?: string | null;
  endpoint_url?: string | null;
  api_key?: string | null;
  api_secret?: string | null;
  config?: Record<string, unknown> | null;
  is_active?: boolean;
}

/**
 * 获取外部系统列表
 */
export const getExternalSystems = async (params: { page?: number; size?: number; search?: string } = {}): Promise<ExternalSystemListResponse> => {
  return http.get('/external-systems/', { params });
};

/**
 * 获取外部系统详情
 */
export const getExternalSystemById = async (id: number): Promise<ExternalSystem> => {
  return http.get(`/external-systems/${id}`);
};

/**
 * 创建外部系统
 */
export const createExternalSystem = async (params: CreateExternalSystemParams): Promise<ExternalSystem> => {
  return http.post('/external-systems/', params);
};

/**
 * 更新外部系统
 */
export const updateExternalSystem = async (id: number, params: UpdateExternalSystemParams): Promise<ExternalSystem> => {
  return http.put(`/external-systems/${id}`, params);
};

/**
 * 删除外部系统
 */
export const deleteExternalSystem = async (id: number): Promise<void> => {
  return http.delete(`/external-systems/${id}`);
};

export const getUserAccessibleExternalSystems = async (): Promise<UserAccessibleExternalSystemsResponse> => {
  return http.get('/external-systems/user/accessible');
};

export const getExternalSystemAccess = async (systemId: number): Promise<ExternalSystemAccess> => {
  return http.get(`/external-systems/${systemId}/access`);
};

export const getExternalSystemIntegrationConfig = async (
  systemId: number,
  integrationType: ExternalSystemIntegrationType
): Promise<ExternalSystemIntegrationConfigResponse> => {
  return http.get(`/external-systems/${systemId}/integration/config`, { params: { integration_type: integrationType } });
};
