/**
 * 系统设置页面
 * 创建日期: 2025-01-08
 * 用途: 系统设置入口
 */

import React from 'react';
import { Card, Row, Col } from 'antd';
import { SafetyCertificateOutlined, AppstoreOutlined, ApiOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout';

const Settings: React.FC = () => {
  const navigate = useNavigate();

  const settingsItems = [
    {
      title: '角色权限',
      icon: <SafetyCertificateOutlined />,
      description: '管理系统角色和权限分配',
      path: '/settings/roles',
      color: '#1890ff'
    },
    {
      title: '菜单管理',
      icon: <AppstoreOutlined />,
      description: '配置系统菜单和路由',
      path: '/settings/menus',
      color: '#52c41a'
    },
    {
      title: '外部系统配置',
      icon: <ApiOutlined />,
      description: '配置外部系统集成参数',
      path: '/settings/external-systems',
      color: '#722ed1'
    }
  ];

  return (
    <MainLayout>
      <div style={{ padding: '24px' }}>
        <h1 style={{ marginBottom: 24 }}>系统设置</h1>
        <Row gutter={[16, 16]}>
          {settingsItems.map((item, index) => (
            <Col xs={24} sm={12} md={8} key={index}>
              <Card 
                hoverable 
                onClick={() => navigate(item.path)}
                style={{ cursor: 'pointer' }}
              >
                <Card.Meta
                  avatar={
                    <div style={{ 
                      fontSize: '24px', 
                      color: item.color,
                      background: `${item.color}15`,
                      padding: '12px',
                      borderRadius: '8px'
                    }}>
                      {item.icon}
                    </div>
                  }
                  title={item.title}
                  description={item.description}
                />
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    </MainLayout>
  );
};

export default Settings;
