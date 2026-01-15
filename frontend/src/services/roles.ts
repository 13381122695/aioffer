/**
 * 角色权限管理API服务
 * 创建日期: 2025-01-08
 * 用途: 处理角色和权限管理相关操作
 */

import { http } from '@/utils/request';

export interface Permission {
  id: number;
  name: string;
  code: string;
  resource: string;
  action: string;
  description: string;
  full_code?: string;
}

export interface Role {
  id: number;
  name: string;
  description: string;
  is_system: boolean;
  created_at: string;
  permission_count?: number;
  permissions?: Permission[];
}

export interface RoleListResponse {
  items: Role[];
  total: number;
  page: number;
  size: number;
}

export interface CreateRoleParams {
  name: string;
  description?: string;
  permission_ids?: number[];
}

export interface UpdateRoleParams {
  name?: string;
  description?: string;
  permission_ids?: number[];
}

/**
 * 获取角色列表
 */
export const getRoles = async (params: { page?: number; size?: number; search?: string } = {}): Promise<RoleListResponse> => {
  return http.get('/roles/', { params });
};

/**
 * 获取角色详情
 */
export const getRoleById = async (id: number): Promise<Role> => {
  return http.get(`/roles/${id}`);
};

/**
 * 创建角色
 */
export const createRole = async (params: CreateRoleParams): Promise<Role> => {
  return http.post('/roles/', params);
};

/**
 * 更新角色
 */
export const updateRole = async (id: number, params: UpdateRoleParams): Promise<Role> => {
  return http.put(`/roles/${id}`, params);
};

/**
 * 删除角色
 */
export const deleteRole = async (id: number): Promise<void> => {
  return http.delete(`/roles/${id}`);
};

/**
 * 获取所有权限
 */
export const getAllPermissions = async (): Promise<Permission[]> => {
  return http.get('/roles/permissions/all');
};

/**
 * 分配角色权限
 */
export const assignRolePermissions = async (roleId: number, permissionIds: number[]): Promise<void> => {
  return http.post(`/roles/${roleId}/permissions`, { permission_ids: permissionIds });
};
