/**
 * 用户认证状态管理
 * 创建日期: 2025-01-08
 * 用途: 管理用户登录状态、权限和用户信息
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: number;
  username: string;
  email: string;
  phone?: string;
  avatar?: string;
  role: string;
  is_active: boolean;
  points?: number;
  created_at: string;
}

interface MenuNode {
  id: number;
  name: string;
  path?: string;
  icon?: string;
  children?: MenuNode[];
}

interface AuthState {
  token: string | null;
  user: User | null;
  permissions: string[];
  menus: MenuNode[];
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // 方法
  setToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  setPermissions: (permissions: string[]) => void;
  setMenus: (menus: MenuNode[]) => void;
  login: (token: string, user: User) => void;
  logout: () => void;
  updateUserPoints: (points: number) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      permissions: [],
      menus: [],
      isAuthenticated: false,
      isLoading: false,
      
      setToken: (token) => {
        set({ token });
        if (token) {
          localStorage.setItem('token', token);
        } else {
          localStorage.removeItem('token');
        }
      },
      
      setUser: (user) => {
        set({ user, isAuthenticated: !!user });
      },
      
      setPermissions: (permissions) => {
        set({ permissions });
      },
      
      setMenus: (menus) => {
        set({ menus });
      },
      
      login: (token, user) => {
        set({
          token,
          user,
          isAuthenticated: true,
          isLoading: false
        });
        localStorage.setItem('token', token);
      },
      
      logout: () => {
        set({
          token: null,
          user: null,
          permissions: [],
          menus: [],
          isAuthenticated: false,
          isLoading: false
        });
        localStorage.removeItem('token');
      },
      
      updateUserPoints: (points) => {
        const { user } = get();
        if (user) {
          set({
            user: {
              ...user,
              points: points
            }
          });
        }
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        permissions: state.permissions,
        menus: state.menus,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
);
