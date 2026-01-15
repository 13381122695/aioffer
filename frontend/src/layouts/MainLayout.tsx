/**
 * 主布局组件
 * 创建日期: 2025-01-08
 * 用途: 会员管理系统主布局，包含侧边栏导航和顶部工具栏
 */

import React, { useMemo, useState, useEffect } from 'react';
import { Layout, Menu, Avatar, Dropdown, Button, App, MenuProps } from 'antd';
import { 
  DashboardOutlined, 
  UserOutlined, 
  TeamOutlined, 
  SettingOutlined, 
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  GlobalOutlined,
  ShoppingCartOutlined,
  TransactionOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/auth';

const { Header, Sider, Content } = Layout;

interface MainLayoutProps {
  children: React.ReactNode;
}

type NavMenuItem = {
  key: string;
  icon?: React.ReactNode;
  label: string;
  path?: string;
  children?: NavMenuItem[];
};

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [openKeys, setOpenKeys] = useState<string[]>([]);
  
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const { message } = App.useApp();

  // 根据当前路径设置选中的菜单项
  useEffect(() => {
    const path = location.pathname;
    const key = path.split('/')[1] || 'dashboard';
    setSelectedKeys([key]);
  }, [location.pathname]);

  /**
   * 菜单项配置
   */
  const menuItems: NavMenuItem[] = useMemo(
    () => [
      {
        key: 'dashboard',
        icon: <DashboardOutlined />,
        label: '仪表盘',
        path: '/dashboard',
      },
      {
        key: 'users',
        icon: <UserOutlined />,
        label: '用户管理',
        path: '/users',
      },
      {
        key: 'members',
        icon: <TeamOutlined />,
        label: '会员管理',
        path: '/members',
      },
      {
        key: 'external-systems',
        icon: <GlobalOutlined />,
        label: '外部系统',
        path: '/external-systems',
      },
      {
        key: 'orders',
        icon: <ShoppingCartOutlined />,
        label: '订单管理',
        path: '/orders',
      },
      {
        key: 'transactions',
        icon: <TransactionOutlined />,
        label: '交易记录',
        path: '/transactions',
      },
      {
        key: 'settings',
        icon: <SettingOutlined />,
        label: '系统设置',
        path: '/settings',
        children: [
          {
            key: 'roles',
            label: '角色权限',
            path: '/settings/roles',
          },
          {
            key: 'menus',
            label: '菜单管理',
            path: '/settings/menus',
          },
          {
            key: 'external-systems-config',
            label: '外部系统配置',
            path: '/settings/external-systems',
          },
        ],
      },
    ],
    []
  );

  const visibleMenuItems: NavMenuItem[] = useMemo(() => {
    if (user?.role === 'member') {
      const allowedKeys = new Set(['members', 'external-systems']);
      return menuItems
        .filter((item) => allowedKeys.has(item.key))
        .map((item) => {
          if (item.key === 'members') return { ...item, label: '我的账户' };
          if (item.key === 'external-systems') return { ...item, label: '入学评估' };
          return item;
        });
    }
    return menuItems;
  }, [menuItems, user?.role]);

  /**
   * 处理菜单点击
   */
  const handleMenuClick = ({ key }: { key: string }) => {
    const menuItem = findMenuItem(visibleMenuItems, key);
    if (menuItem && menuItem.path) {
      navigate(menuItem.path);
    }
  };

  /**
   * 递归查找菜单项
   */
  const findMenuItem = (items: NavMenuItem[], key: string): NavMenuItem | null => {
    for (const item of items) {
      if (item.key === key) {
        return item;
      }
      if (item.children) {
        const found = findMenuItem(item.children, key);
        if (found) return found;
      }
    }
    return null;
  };

  /**
   * 处理用户下拉菜单
   */
  const handleUserMenuClick = ({ key }: { key: string }) => {
    switch (key) {
      case 'profile':
        navigate('/profile');
        break;
      case 'settings':
        navigate('/settings');
        break;
      case 'logout':
        logout();
        message.success('已退出登录');
        navigate('/login');
        break;
    }
  };

  /**
   * 用户下拉菜单项
   */
  const userMenuItems: MenuProps['items'] = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录'
    }
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider 
        trigger={null} 
        collapsible 
        collapsed={collapsed}
        style={{
          boxShadow: '2px 0 6px rgba(0,21,41,.1)',
          background: '#fff'
        }}
      >
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          borderBottom: '1px solid #f0f0f0',
          fontSize: collapsed ? '16px' : '20px',
          fontWeight: 'bold',
          color: '#1890ff'
        }}>
          {collapsed ? '会员' : '会员管理'}
        </div>
        
        <Menu
          mode="inline"
          selectedKeys={selectedKeys}
          openKeys={openKeys}
          onOpenChange={setOpenKeys}
          onClick={handleMenuClick}
          items={visibleMenuItems}
          style={{ border: 'none' }}
        />
      </Sider>
      
      <Layout>
        <Header 
          style={{ 
            padding: '0 24px', 
            background: '#fff', 
            boxShadow: '0 1px 4px rgba(0,21,41,.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >
          <div>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              style={{ fontSize: '16px' }}
            />
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {/* 用户点数显示 */}
            {user?.points !== undefined && (
              <div style={{ 
                background: '#f0f9ff', 
                padding: '4px 12px', 
                borderRadius: '16px',
                fontSize: '12px',
                color: '#1890ff'
              }}>
                点数: {user.points}
              </div>
            )}
            
            {/* 用户头像和下拉菜单 */}
            <Dropdown
              menu={{ items: userMenuItems, onClick: handleUserMenuClick }}
              placement="bottomRight"
              arrow
            >
              <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Avatar 
                  size="small" 
                  icon={<UserOutlined />}
                  src={user?.avatar}
                />
                <span style={{ fontSize: '14px' }}>{user?.username}</span>
              </div>
            </Dropdown>
          </div>
        </Header>
        
        <Content 
          style={{ 
            margin: '24px', 
            padding: '24px', 
            background: '#fff',
            borderRadius: '8px',
            boxShadow: '0 1px 4px rgba(0,21,41,.1)',
            minHeight: 'calc(100vh - 112px)'
          }}
        >
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
