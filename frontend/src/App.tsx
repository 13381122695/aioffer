/**
 * 主应用组件
 * 创建日期: 2025-01-08
 * 用途: 配置应用路由和全局状态
 */

import React, { useLayoutEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntdApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { useAuthStore } from '@/stores/auth';
import { initGlobalMessage } from '@/utils/request';

// 页面组件
import Login from '@/pages/Login';
import Register from '@/pages/Register';
import Dashboard from '@/pages/Dashboard';
import Users from '@/pages/Users';
import Members from '@/pages/Members';
import Transactions from '@/pages/Transactions';
import Orders from '@/pages/Orders';
import ExternalSystems from '@/pages/ExternalSystems';
import Profile from '@/pages/Profile';
import Settings from '@/pages/Settings';
import Roles from '@/pages/settings/Roles';
import Menus from '@/pages/settings/Menus';
import ExternalSystemsConfig from '@/pages/settings/ExternalSystemsConfig';

/**
 * 路由守卫组件
 * 检查用户是否已登录，未登录则跳转到登录页
 */
const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

const AuthedRedirect: React.FC = () => {
  const { user } = useAuthStore();
  const to = user?.role === 'member' ? '/external-systems' : '/dashboard';
  return <Navigate to={to} replace />;
};

/**
 * 公共路由组件
 * 已登录用户访问登录页时跳转到仪表盘
 */
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? <AuthedRedirect /> : <>{children}</>;
};

/**
 * 全局消息初始化组件
 * 用于将 Antd App 上下文中的 message 实例注入到 request 工具中
 */
const GlobalMessageInit = () => {
  const { message } = AntdApp.useApp();
  
  useLayoutEffect(() => {
    initGlobalMessage(message);
  }, [message]);
  
  return null;
};

const App: React.FC = () => {
  return (
    <ConfigProvider 
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 6,
        },
      }}
    >
      <AntdApp>
        <GlobalMessageInit />
        <Router>
          <Routes>
            {/* 公共路由 */}
            <Route 
              path="/login" 
              element={
                <PublicRoute>
                  <Login />
                </PublicRoute>
              } 
            />
            
            <Route 
              path="/register" 
              element={
                <PublicRoute>
                  <Register />
                </PublicRoute>
              } 
            />
            
            {/* 私有路由 */}
            <Route 
              path="/" 
              element={
                <PrivateRoute>
                  <AuthedRedirect />
                </PrivateRoute>
              } 
            />
            
            <Route 
              path="/dashboard" 
              element={
                <PrivateRoute>
                  <Dashboard />
                </PrivateRoute>
              } 
            />
            
            <Route 
              path="/users" 
              element={
                <PrivateRoute>
                  <Users />
                </PrivateRoute>
              } 
            />
            
            <Route 
              path="/members" 
              element={
                <PrivateRoute>
                  <Members />
                </PrivateRoute>
              } 
            />
            
            <Route 
              path="/transactions" 
              element={
                <PrivateRoute>
                  <Transactions />
                </PrivateRoute>
              } 
            />
            
            <Route 
              path="/orders" 
              element={
                <PrivateRoute>
                  <Orders />
                </PrivateRoute>
              } 
            />
            
            <Route 
              path="/external-systems" 
              element={
                <PrivateRoute>
                  <ExternalSystems />
                </PrivateRoute>
              } 
            />
            
            <Route 
              path="/profile" 
              element={
                <PrivateRoute>
                  <Profile />
                </PrivateRoute>
              } 
            />
            
            <Route 
              path="/settings" 
              element={
                <PrivateRoute>
                  <Settings />
                </PrivateRoute>
              } 
            />
            
            <Route 
              path="/settings/roles" 
              element={
                <PrivateRoute>
                  <Roles />
                </PrivateRoute>
              } 
            />
            
            <Route 
              path="/settings/menus" 
              element={
                <PrivateRoute>
                  <Menus />
                </PrivateRoute>
              } 
            />
            
            <Route 
              path="/settings/external-systems" 
              element={
                <PrivateRoute>
                  <ExternalSystemsConfig />
                </PrivateRoute>
              } 
            />
            
            {/* 404页面 */}
            <Route path="*" element={<div>404 - 页面未找到</div>} />
          </Routes>
        </Router>
      </AntdApp>
    </ConfigProvider>
  );
};

export default App;
