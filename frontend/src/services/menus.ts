/**
 * 菜单管理API服务
 * 创建日期: 2025-01-08
 * 用途: 处理菜单管理相关操作
 */

import { http } from '@/utils/request';

export interface Menu {
  id: number;
  name: string;
  code: string;
  path: string;
  component: string;
  icon?: string;
  sort: number;
  is_visible: boolean;
  parent_id?: number;
  children?: Menu[];
  permissions?: number[]; // Permission IDs associated with this menu
}

export interface CreateMenuParams {
  name: string;
  code: string;
  path?: string;
  component?: string;
  icon?: string;
  sort?: number;
  is_visible?: boolean;
  parent_id?: number;
}

export interface UpdateMenuParams {
  name?: string;
  code?: string;
  path?: string;
  component?: string;
  icon?: string;
  sort?: number;
  is_visible?: boolean;
  parent_id?: number;
}

/**
 * 获取菜单列表 (树形)
 */
export const getMenus = async (): Promise<Menu[]> => {
  return http.get('/menus/');
};

/**
 * 获取菜单详情
 */
export const getMenuById = async (id: number): Promise<Menu> => {
  return http.get(`/menus/${id}`);
};

/**
 * 创建菜单
 */
export const createMenu = async (params: CreateMenuParams): Promise<Menu> => {
  return http.post('/menus/', params);
};

/**
 * 更新菜单
 */
export const updateMenu = async (id: number, params: UpdateMenuParams): Promise<Menu> => {
  return http.put(`/menus/${id}`, params);
};

/**
 * 删除菜单
 */
export const deleteMenu = async (id: number): Promise<void> => {
  return http.delete(`/menus/${id}`);
};
