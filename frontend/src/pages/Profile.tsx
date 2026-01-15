/**
 * 个人中心页面
 * 创建日期: 2025-01-08
 * 用途: 显示和编辑个人信息
 */

import React from 'react';
import { Card, Descriptions, Avatar, Button, App } from 'antd';
import { UserOutlined, EditOutlined } from '@ant-design/icons';
import MainLayout from '@/layouts/MainLayout';
import { useAuthStore } from '@/stores/auth';

const Profile: React.FC = () => {
  const { user } = useAuthStore();
  const { message } = App.useApp();

  return (
    <MainLayout>
      <div style={{ padding: '24px' }}>
        <h1 style={{ marginBottom: 24 }}>个人中心</h1>
        <Card>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 24 }}>
            <Avatar size={64} icon={<UserOutlined />} src={user?.avatar} />
            <div style={{ marginLeft: 24 }}>
              <h2 style={{ margin: 0 }}>{user?.username}</h2>
              <p style={{ color: '#666', margin: '4px 0 0' }}>{user?.role === 'admin' ? '管理员' : '普通用户'}</p>
            </div>
            <div style={{ marginLeft: 'auto' }}>
              <Button type="primary" icon={<EditOutlined />} onClick={() => message.info('编辑功能开发中')}>
                编辑资料
              </Button>
            </div>
          </div>

          <Descriptions title="基本信息" bordered column={2}>
            <Descriptions.Item label="用户ID">{user?.id}</Descriptions.Item>
            <Descriptions.Item label="用户名">{user?.username}</Descriptions.Item>
            <Descriptions.Item label="邮箱">{user?.email}</Descriptions.Item>
            <Descriptions.Item label="手机号">{user?.phone || '-'}</Descriptions.Item>
            <Descriptions.Item label="注册时间">{new Date(user?.created_at || '').toLocaleString()}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <span style={{ color: user?.is_active ? 'green' : 'red' }}>
                {user?.is_active ? '启用' : '禁用'}
              </span>
            </Descriptions.Item>
          </Descriptions>
        </Card>
      </div>
    </MainLayout>
  );
};

export default Profile;
