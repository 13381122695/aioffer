/**
 * 用户登录页面
 * 创建日期: 2025-01-08
 * 用途: 提供多种登录方式的用户认证界面
 */

import React, { useState } from 'react';
import { Form, Input, Button, Card, Tabs, App, Alert } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '@/stores/auth';
import { login, type LoginParams } from '@/services/auth';

const Login: React.FC = () => {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  
  const navigate = useNavigate();
  const { login: authLogin } = useAuthStore();

  /**
   * 处理登录表单提交
   */
  const handleLogin = async (
    values: Partial<Record<'email' | 'username' | 'password', string>>,
    loginType: LoginParams['auth_type']
  ) => {
    try {
      setLoading(true);
      setSubmitError(null);
      
      const loginParams: LoginParams = {
        auth_type: loginType,
      };

      // 根据登录类型设置参数
      switch (loginType) {
        case 'email':
          loginParams.email = values.email;
          loginParams.password = values.password;
          break;
        case 'username':
          loginParams.username = values.username;
          loginParams.password = values.password;
          break;
      }

      const response = await login(loginParams);
      
      // 保存认证信息
      authLogin(response.access_token, response.user);
      
      message.success('登录成功！');
      navigate(response.user.role === 'member' ? '/external-systems' : '/dashboard');
    } catch (error) {
      const errMsg = error instanceof Error ? error.message : String(error);
      console.error('登录失败:', error);
      setSubmitError(errMsg || '登录失败，请检查用户名和密码');
      message.error(errMsg || '登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 邮箱密码登录表单
   */
  const renderEmailLogin = () => (
    <Form
      form={form}
      name="email_login"
      onFinish={(values) => handleLogin(values, 'email')}
      size="large"
    >
      <Form.Item
        name="email"
        rules={[
          { required: true, message: '请输入邮箱地址' },
          { type: 'email', message: '请输入有效的邮箱地址' }
        ]}
      >
        <Input 
          prefix={<MailOutlined />} 
          placeholder="邮箱地址" 
        />
      </Form.Item>
      
      <Form.Item
        name="password"
        rules={[{ required: true, message: '请输入密码' }]}
      >
        <Input.Password 
          prefix={<LockOutlined />} 
          placeholder="密码" 
        />
      </Form.Item>
      
      <Form.Item>
        <Button 
          type="primary" 
          htmlType="submit" 
          loading={loading} 
          block
          size="large"
        >
          登录
        </Button>
      </Form.Item>
    </Form>
  );

  /**
   * 用户名密码登录表单
   */
  const renderUsernameLogin = () => (
    <Form
      form={form}
      name="username_login"
      onFinish={(values) => handleLogin(values, 'username')}
      size="large"
    >
      <Form.Item
        name="username"
        rules={[{ required: true, message: '请输入用户名' }]}
      >
        <Input 
          prefix={<UserOutlined />} 
          placeholder="用户名" 
        />
      </Form.Item>
      
      <Form.Item
        name="password"
        rules={[{ required: true, message: '请输入密码' }]}
      >
        <Input.Password 
          prefix={<LockOutlined />} 
          placeholder="密码" 
        />
      </Form.Item>
      
      <Form.Item>
        <Button 
          type="primary" 
          htmlType="submit" 
          loading={loading} 
          block
          size="large"
        >
          登录
        </Button>
      </Form.Item>
    </Form>
  );

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <Card 
        style={{ 
          width: 400,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          borderRadius: '12px'
        }}
        styles={{ body: { padding: '40px 30px' } }}
      >
        <div style={{ textAlign: 'center', marginBottom: 30 }}>
          <h1 style={{ color: '#1890ff', fontSize: '28px', marginBottom: 8 }}>
            会员管理
          </h1>
          <p style={{ color: '#666', fontSize: '14px' }}>
            欢迎回来，请登录您的账户
          </p>
        </div>
        
        {submitError ? (
          <div style={{ marginBottom: 16 }}>
            <Alert type="error" message="登录失败" description={submitError} showIcon />
          </div>
        ) : null}

        <Tabs 
          defaultActiveKey="email" 
          centered
          destroyOnHidden
          onChange={() => setSubmitError(null)}
          items={[
            {
              key: 'email',
              label: '邮箱登录',
              children: renderEmailLogin(),
            },
            {
              key: 'username',
              label: '用户名登录',
              children: renderUsernameLogin(),
            },
          ]}
        />
        
        <div style={{ textAlign: 'center', marginTop: 20 }}>
          <p style={{ color: '#999', fontSize: '12px' }}>
            还没有账户？ <Link to="/register" style={{ color: '#1890ff' }}>立即注册</Link>
          </p>
        </div>
      </Card>
    </div>
  );
};

export default Login;
