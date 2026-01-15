/**
 * 注册页面
 * 创建日期: 2025-01-08
 * 用途: 用户注册
 */

import React, { useEffect, useRef, useState } from 'react';
import { Form, Input, Button, Card, Typography, App, Row, Col } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { useNavigate, Link } from 'react-router-dom';
import { register, sendEmailCode } from '@/services/auth';

const { Title, Text } = Typography;

type RegisterFormValues = {
  username: string;
  email: string;
  email_code: string;
  password: string;
  confirm: string;
};

const Register: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [sendingCode, setSendingCode] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [form] = Form.useForm<RegisterFormValues>();
  const navigate = useNavigate();
  const { message } = App.useApp();

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const handleSendEmailCode = async () => {
    try {
      const email = form.getFieldValue('email');
      if (!email) {
        message.error('请先输入邮箱');
        return;
      }

      setSendingCode(true);
      await sendEmailCode(email);
      message.success('验证码已发送到邮箱');

      setCountdown(60);
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            if (timerRef.current) clearInterval(timerRef.current);
            timerRef.current = null;
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (error) {
      console.error('发送验证码失败:', error);
      message.error('发送验证码失败，请稍后重试');
    } finally {
      setSendingCode(false);
    }
  };

  const onFinish = async (values: RegisterFormValues) => {
    try {
      setLoading(true);
      await register({
        username: values.username,
        email: values.email,
        email_code: values.email_code,
        password: values.password,
        auth_type: 'email'
      });
      message.success('注册成功，请登录');
      navigate('/login');
    } catch (error) {
      console.error('注册失败:', error);
      message.error('注册失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      background: '#f0f2f5'
    }}>
      <Card style={{ width: 400, boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={2}>注册账号</Title>
          <Text type="secondary">加入我们，开始您的体验</Text>
        </div>
        
        <Form
          name="register"
          initialValues={{ remember: true }}
          onFinish={onFinish}
          layout="vertical"
          size="large"
          form={form}
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '请输入用户名!' },
              {
                pattern: /^(?=.*[a-zA-Z])[a-zA-Z0-9]{3,50}$/,
                message: '用户名需为3-50位英文+数字，并至少包含一个英文字符!',
              },
            ]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="用户名（英文+数字）" 
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码!' }]}
          >
            <Input.Password 
              prefix={<LockOutlined />} 
              placeholder="密码" 
            />
          </Form.Item>

          <Form.Item
            name="confirm"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码!' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致!'));
                },
              }),
            ]}
          >
            <Input.Password 
              prefix={<LockOutlined />} 
              placeholder="确认密码" 
            />
          </Form.Item>

          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱!' },
              { type: 'email', message: '请输入有效的邮箱地址!' }
            ]}
          >
            <Input 
              prefix={<MailOutlined />} 
              placeholder="邮箱" 
            />
          </Form.Item>

          <Form.Item
            name="email_code"
            rules={[{ required: true, message: '请输入邮箱验证码!' }]}
          >
            <Row gutter={8}>
              <Col span={16}>
                <Input placeholder="邮箱验证码" />
              </Col>
              <Col span={8}>
                <Button
                  onClick={handleSendEmailCode}
                  disabled={countdown > 0}
                  loading={sendingCode}
                  block
                >
                  {countdown > 0 ? `${countdown}s` : '发送验证码'}
                </Button>
              </Col>
            </Row>
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              注册
            </Button>
          </Form.Item>

          <div style={{ textAlign: 'center' }}>
            <Text>已有账号？ </Text>
            <Link to="/login">立即登录</Link>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default Register;
