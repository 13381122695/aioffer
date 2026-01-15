/**
 * 仪表盘页面
 * 创建日期: 2025-01-08
 * 用途: 显示系统概览、统计数据和快捷操作
 */

import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Progress, Table, Tag, Button, Space } from 'antd';
import {
  UserOutlined,
  ShoppingCartOutlined,
  DollarOutlined,
  ArrowUpOutlined,
  EyeOutlined,
  SettingOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { getAllTransactions, getUserStats } from '@/services/user';
import { getOrderList, getOrderStats } from '@/services/orders';
import MainLayout from '@/layouts/MainLayout';

type DashboardOrder = {
  id: number;
  order_no: string;
  user_id: number;
  username?: string | null;
  amount: number;
  status: number;
  status_text: string;
  created_at: string;
};

type DashboardTransaction = {
  id: number;
  user_id: number;
  username?: string | null;
  type: number;
  type_text: string;
  points: number;
  amount?: number | null;
  created_at: string;
};

const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  const [userStats, setUserStats] = useState({
    total_users: 0,
    active_users: 0,
    new_users_today: 0,
    total_points: 0,
  });

  const [orderStats, setOrderStats] = useState({
    total_orders: 0,
    total_amount: 0,
    pending_orders: 0,
    completed_orders: 0,
  });

  const [recentOrders, setRecentOrders] = useState<DashboardOrder[]>([]);
  const [recentTransactions, setRecentTransactions] = useState<DashboardTransaction[]>([]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [userStatsData, orderStatsData, ordersData, transactionsData] = await Promise.all([
          getUserStats(),
          getOrderStats(),
          getOrderList({ page: 1, size: 6 }) as unknown as Promise<{ items: DashboardOrder[] }>,
          getAllTransactions({ page: 1, size: 6 }) as unknown as Promise<{ items: DashboardTransaction[] }>,
        ]);

        setUserStats(userStatsData);
        setOrderStats(orderStatsData);
        setRecentOrders(ordersData.items || []);
        setRecentTransactions(transactionsData.items || []);
      } catch (error) {
        console.error('获取仪表盘数据失败:', error);
      }
    };

    fetchDashboardData();
  }, []);

  const completedRate = orderStats.total_orders > 0
    ? Math.round((orderStats.completed_orders / orderStats.total_orders) * 1000) / 10
    : 0;

  const formatDateTime = (value: unknown) => {
    if (!value) return '-';
    const date = new Date(String(value));
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleString();
  };

  // 订单表格列配置
  const orderColumns = [
    {
      title: '订单号',
      dataIndex: 'order_no',
      key: 'order_no',
      width: 160,
    },
    {
      title: '用户',
      dataIndex: 'username',
      key: 'username',
      width: 120,
      render: (username: unknown, record: DashboardOrder) => (username ? String(username) : `用户#${record.user_id}`),
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 100,
      render: (amount: number) => `¥${Number(amount).toFixed(2)}`,
    },
    {
      title: '状态',
      dataIndex: 'status_text',
      key: 'status_text',
      width: 100,
      render: (statusText: string, record: DashboardOrder) => {
        const colorMap: Record<number, string> = {
          1: 'orange',
          2: 'green',
          3: 'default',
          4: 'red',
        };
        return <Tag color={colorMap[record.status] || 'default'}>{statusText || '未知'}</Tag>;
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (value: unknown) => formatDateTime(value),
    },
    {
      title: '操作',
      key: 'action',
      width: 90,
      render: () => (
        <Space size="small">
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => navigate('/orders')}>
            查看
          </Button>
        </Space>
      ),
    },
  ];

  // 交易记录表格列配置
  const transactionColumns = [
    {
      title: '交易ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '用户',
      dataIndex: 'username',
      key: 'username',
      width: 120,
      render: (username: unknown, record: DashboardTransaction) => (username ? String(username) : `用户#${record.user_id}`),
    },
    {
      title: '类型',
      dataIndex: 'type_text',
      key: 'type_text',
      width: 90,
      render: (typeText: string, record: DashboardTransaction) => {
        const colorMap: Record<number, string> = {
          1: 'green',
          2: 'blue',
          3: 'orange',
        };
        return <Tag color={colorMap[record.type] || 'default'}>{typeText || '未知'}</Tag>;
      },
    },
    {
      title: '点数',
      dataIndex: 'points',
      key: 'points',
      width: 90,
      render: (points: number) => (
        <span style={{ color: points > 0 ? 'green' : 'red' }}>
          {points > 0 ? '+' : ''}
          {points}
        </span>
      ),
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 100,
      render: (amount: number | null | undefined) => (amount ? `¥${Number(amount).toFixed(2)}` : '-'),
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (value: unknown) => formatDateTime(value),
    },
  ];

  return (
    <MainLayout>
      <div style={{ padding: '24px' }}>
        {/* 统计卡片 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="总用户数"
                value={userStats.total_users}
                prefix={<UserOutlined />}
                valueStyle={{ color: '#3f8600' }}
                suffix={<ArrowUpOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="活跃用户"
                value={userStats.active_users}
                prefix={<UserOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="今日新增"
                value={userStats.new_users_today}
                prefix={<UserOutlined />}
                valueStyle={{ color: '#52c41a' }}
                suffix={<ArrowUpOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="总点数"
                value={userStats.total_points}
                prefix={<DollarOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 业务统计 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} lg={8}>
            <Card title="总收入" extra={<SettingOutlined />}>
              <Statistic
                value={orderStats.total_amount}
                precision={2}
                prefix="¥"
                valueStyle={{ color: '#3f8600' }}
                suffix={<ArrowUpOutlined />}
              />
              <div style={{ marginTop: 16 }}>
                <Progress percent={completedRate} strokeColor="#52c41a" />
                <p style={{ color: '#999', fontSize: '12px', marginTop: 8 }}>
                  已完成订单占比 {completedRate}%
                </p>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8}>
            <Card title="总订单数" extra={<ShoppingCartOutlined />}>
              <Statistic
                value={orderStats.total_orders}
                valueStyle={{ color: '#1890ff' }}
                suffix={<ArrowUpOutlined />}
              />
              <div style={{ marginTop: 16 }}>
                <Progress percent={completedRate} strokeColor="#1890ff" />
                <p style={{ color: '#999', fontSize: '12px', marginTop: 8 }}>
                  已完成 {orderStats.completed_orders} / 待支付 {orderStats.pending_orders}
                </p>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8}>
            <Card title="系统状态" extra={<SettingOutlined />}>
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>服务器状态</span>
                  <Tag color="green">正常</Tag>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>数据库连接</span>
                  <Tag color="green">正常</Tag>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>外部系统</span>
                  <Tag color="green">正常</Tag>
                </div>
              </div>
            </Card>
          </Col>
        </Row>

        {/* 数据表格 */}
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card 
              title="最近订单" 
              extra={
                <Button type="link" onClick={() => navigate('/orders')}>
                  查看更多
                </Button>
              }
            >
              <Table
                columns={orderColumns}
                dataSource={recentOrders}
                pagination={false}
                size="small"
                rowKey="id"
              />
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card 
              title="最近交易" 
              extra={
                <Button type="link" onClick={() => navigate('/transactions')}>
                  查看更多
                </Button>
              }
            >
              <Table
                columns={transactionColumns}
                dataSource={recentTransactions}
                pagination={false}
                size="small"
                rowKey="id"
              />
            </Card>
          </Col>
        </Row>
      </div>
    </MainLayout>
  );
};

export default Dashboard;