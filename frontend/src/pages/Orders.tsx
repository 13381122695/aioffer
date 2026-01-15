/**
 * 订单管理页面
 * 创建日期: 2025-01-08
 * 用途: 管理用户订单，支持创建订单、支付、退款等功能
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Space, Input, Modal, Form, App, Tag, Row, Col, Card, Statistic } from 'antd';
import type { TablePaginationConfig } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { PlusOutlined, SearchOutlined, EyeOutlined, DollarOutlined, ClockCircleOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { getOrderList, createOrder, getOrderStats, Order, CreateOrderParams, OrderListParams } from '@/services/orders';
import MainLayout from '@/layouts/MainLayout';
import PaymentModal from '@/components/PaymentModal';

const { Search } = Input;

type PaginationState = {
  current: number;
  pageSize: number;
  total: number;
};

type CreateOrderFormValues = {
  amount: number;
  points: number;
  payment_method: string;
  description?: string;
};

const Orders: React.FC = () => {
  const { message } = App.useApp();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({
    total_orders: 0,
    total_amount: 0,
    pending_orders: 0,
    completed_orders: 0,
  });
  const [modalVisible, setModalVisible] = useState(false);
  const [paymentModalVisible, setPaymentModalVisible] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [form] = Form.useForm();
  
  const [pagination, setPagination] = useState<PaginationState>({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const { current, pageSize } = pagination;
  
  // 获取订单列表
  const fetchOrders = useCallback(async (params: OrderListParams = {}) => {
    try {
      setLoading(true);
      const page = params.page ?? current;
      const size = params.size ?? pageSize;
      const response = await getOrderList({
        page,
        size,
        ...params,
      });
      
      setOrders(response.items);
      setPagination({
        current: response.page,
        pageSize: response.size,
        total: response.total,
      });
    } catch (error) {
      console.error('获取订单列表失败:', error);
      message.error('获取订单列表失败');
    } finally {
      setLoading(false);
    }
  }, [current, message, pageSize]);

  // 获取订单统计
  const fetchStats = useCallback(async () => {
    try {
      const statsData = await getOrderStats();
      setStats(statsData);
    } catch (error) {
      console.error('获取订单统计失败:', error);
    }
  }, []);

  useEffect(() => {
    fetchOrders();
    fetchStats();
  }, [fetchOrders, fetchStats]);

  /**
   * 处理搜索
   */
  const handleSearch = (value: string) => {
    fetchOrders({ search: value });
  };

  /**
   * 处理分页变化
   */
  const handleTableChange = (newPagination: TablePaginationConfig) => {
    const nextPage = newPagination.current || 1;
    const nextPageSize = newPagination.pageSize || pageSize;

    setPagination(prev => ({
      ...prev,
      current: nextPage,
      pageSize: nextPageSize,
    }));
    fetchOrders({
      page: nextPage,
      size: nextPageSize,
    });
  };

  /**
   * 处理创建订单
   */
  const handleCreateOrder = async (values: CreateOrderFormValues) => {
    try {
      const params: CreateOrderParams = {
        amount: values.amount,
        points: values.points,
        payment_method: values.payment_method,
        description: values.description,
      };
      
      await createOrder(params);
      message.success('订单创建成功');
      setModalVisible(false);
      form.resetFields();
      fetchOrders();
      fetchStats();
    } catch (error) {
      console.error('创建订单失败:', error);
      message.error('创建订单失败');
    }
  };

  /**
   * 处理支付
   */
  const handlePayment = (order: Order) => {
    setSelectedOrder(order);
    setPaymentModalVisible(true);
  };

  /**
   * 支付成功回调
   */
  const handlePaymentSuccess = () => {
    setPaymentModalVisible(false);
    setSelectedOrder(null);
    fetchOrders();
    fetchStats();
  };

  /**
   * 获取状态标签
   */
  const getStatusTag = (status: string) => {
    const statusMap = {
      pending: { color: 'orange', text: '待支付', icon: <ClockCircleOutlined /> },
      paid: { color: 'green', text: '已支付', icon: <CheckCircleOutlined /> },
      cancelled: { color: 'red', text: '已取消', icon: <CloseCircleOutlined /> },
      refunded: { color: 'blue', text: '已退款', icon: <DollarOutlined /> },
    };
    
    const statusInfo = statusMap[status as keyof typeof statusMap];
    return (
      <Tag color={statusInfo.color} icon={statusInfo.icon}>
        {statusInfo.text}
      </Tag>
    );
  };

  const columns: ColumnsType<Order> = [
    {
      title: '订单号',
      dataIndex: 'order_no',
      key: 'order_no',
      width: 180,
    },
    {
      title: '用户',
      dataIndex: 'username',
      key: 'username',
      width: 120,
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 100,
      render: (amount: number) => `¥${amount.toFixed(2)}`,
    },
    {
      title: '点数',
      dataIndex: 'points',
      key: 'points',
      width: 80,
      render: (points: number) => <span style={{ color: '#1890ff' }}>{points}</span>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => getStatusTag(status),
    },
    {
      title: '支付方式',
      dataIndex: 'payment_method',
      key: 'payment_method',
      width: 120,
      render: (method: string) => {
        const methodMap = {
          alipay: '支付宝',
          wechat: '微信支付',
          bank: '银行卡',
        };
        return methodMap[method as keyof typeof methodMap] || method;
      },
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '支付时间',
      dataIndex: 'paid_at',
      key: 'paid_at',
      width: 160,
      render: (date: string) => date ? new Date(date).toLocaleString() : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_text: unknown, record: Order) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EyeOutlined />}
            size="small"
            onClick={() => handlePayment(record)}
          >
            详情
          </Button>
          {record.status === 'pending' && (
            <Button
              type="primary"
              size="small"
              onClick={() => handlePayment(record)}
            >
              支付
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <MainLayout>
      <div style={{ padding: '24px' }}>
        {/* 统计卡片 */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总订单数"
                value={stats.total_orders}
                prefix={<DollarOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总金额"
                value={stats.total_amount}
                precision={2}
                prefix="¥"
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="待支付订单"
                value={stats.pending_orders}
                prefix={<ClockCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="已完成订单"
                value={stats.completed_orders}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
        </Row>

        {/* 操作栏 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={8}>
            <Search
              placeholder="搜索订单号或用户名"
              allowClear
              enterButton={<SearchOutlined />}
              onSearch={handleSearch}
              style={{ width: '100%' }}
            />
          </Col>
          <Col span={16} style={{ textAlign: 'right' }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setModalVisible(true)}
            >
              创建订单
            </Button>
          </Col>
        </Row>

        {/* 订单列表 */}
        <Table
          columns={columns}
          dataSource={orders}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `第 ${range[0]}-${range[1]} 条/总共 ${total} 条`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
        />

        {/* 创建订单模态框 */}
        <Modal
          title="创建订单"
          open={modalVisible}
          onOk={() => form.submit()}
          onCancel={() => setModalVisible(false)}
          width={600}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={handleCreateOrder}
          >
            <Form.Item
              label="金额"
              name="amount"
              rules={[{ required: true, message: '请输入金额' }]}
            >
              <Input type="number" placeholder="请输入金额" min={0.01} step={0.01} />
            </Form.Item>
            <Form.Item
              label="点数"
              name="points"
              rules={[{ required: true, message: '请输入点数' }]}
            >
              <Input type="number" placeholder="请输入点数" min={1} />
            </Form.Item>
            <Form.Item
              label="支付方式"
              name="payment_method"
              rules={[{ required: true, message: '请选择支付方式' }]}
            >
              <select>
                <option value="alipay">支付宝</option>
                <option value="wechat">微信支付</option>
                <option value="bank">银行卡</option>
              </select>
            </Form.Item>
            <Form.Item
              label="描述"
              name="description"
            >
              <Input.TextArea placeholder="请输入订单描述" rows={3} />
            </Form.Item>
          </Form>
        </Modal>

        {/* 支付模态框 */}
        <PaymentModal
          open={paymentModalVisible}
          order={selectedOrder}
          onClose={() => setPaymentModalVisible(false)}
          onSuccess={handlePaymentSuccess}
        />
      </div>
    </MainLayout>
  );
};

export default Orders;
