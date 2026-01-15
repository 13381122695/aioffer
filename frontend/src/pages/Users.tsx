/**
 * 用户管理页面
 * 创建日期: 2025-01-08
 * 用途: 管理系统用户，包括用户列表、搜索、编辑、删除等功能
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Space, Input, Switch, Modal, Form, Tag, Avatar, Popconfirm, Card, App } from 'antd';
import type { TablePaginationConfig } from 'antd';
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined, UserOutlined, DollarOutlined } from '@ant-design/icons';
import { getUserList, createUser, updateUser, deleteUser, rechargePoints, User, CreateUserParams, UpdateUserParams } from '@/services/user';
import MainLayout from '@/layouts/MainLayout';

const { Search } = Input;

type PaginationState = {
  current: number;
  pageSize: number;
  total: number;
};

type RechargeFormValues = {
  points: number;
  amount: number;
  payment_method: string;
  description?: string;
};

type UserFormValues = {
  username: string;
  email: string;
  password?: string;
  phone?: string;
  user_type: number;
  is_active?: boolean;
};

const Users: React.FC = () => {
  const { message } = App.useApp();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [rechargeModalVisible, setRechargeModalVisible] = useState(false);
  const [rechargingUser, setRechargingUser] = useState<User | null>(null);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [form] = Form.useForm();
  const [rechargeForm] = Form.useForm();
  
  const [pagination, setPagination] = useState<PaginationState>({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const { current, pageSize } = pagination;
  
  const [searchText, setSearchText] = useState('');

  // 获取用户列表
  const fetchUsers = useCallback(async (params: { page?: number; size?: number; search?: string } = {}) => {
    try {
      setLoading(true);
      const response = await getUserList({
        page: params.page || current,
        size: params.size || pageSize,
        search: params.search !== undefined ? params.search : searchText,
      });
      
      setUsers(response.items);
      setPagination({
        current: response.page,
        pageSize: response.size,
        total: response.total,
      });
    } catch (error) {
      console.error('获取用户列表失败:', error);
      message.error('获取用户列表失败');
    } finally {
      setLoading(false);
    }
  }, [current, message, pageSize, searchText]);

  // 组件加载时获取用户列表
  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  /**
   * 处理搜索
   */
  const handleSearch = (value: string) => {
    setSearchText(value);
    setPagination(prev => ({ ...prev, current: 1 }));
    fetchUsers({ search: value, page: 1 });
  };

  /**
   * 显示充值模态框
   */
  const showRechargeModal = (user: User) => {
    setRechargingUser(user);
    setRechargeModalVisible(true);
    rechargeForm.setFieldsValue({
      user_id: user.id,
      username: user.username,
      points: 100,
      amount: 100,
    });
  };

  /**
   * 处理点数充值
   */
  const handleRecharge = async (values: RechargeFormValues) => {
    try {
      await rechargePoints({
        user_id: rechargingUser!.id,
        points: values.points,
        amount: values.amount,
        payment_method: values.payment_method,
        description: values.description,
      });
      message.success('充值成功');
      setRechargeModalVisible(false);
      rechargeForm.resetFields();
      fetchUsers();
    } catch (error) {
      console.error('充值失败:', error);
      message.error('充值失败');
    }
  };

  /**
   * 处理表格分页变化
   */
  const handleTableChange = (newPagination: TablePaginationConfig) => {
    setPagination(prev => ({
      ...prev,
      current: newPagination.current || 1,
      pageSize: newPagination.pageSize || prev.pageSize,
    }));
    fetchUsers({ 
      page: newPagination.current || 1, 
      size: newPagination.pageSize || pageSize 
    });
  };

  /**
   * 显示创建用户模态框
   */
  const showCreateModal = () => {
    setEditingUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  /**
   * 显示编辑用户模态框
   */
  const showEditModal = (user: User) => {
    setEditingUser(user);
    form.setFieldsValue({
      username: user.username,
      email: user.email,
      phone: user.phone,
      user_type: user.user_type,
      is_active: user.status === 1,
    });
    setModalVisible(true);
  };

  /**
   * 处理创建或更新用户
   */
  const handleSubmit = async (values: UserFormValues) => {
    try {
      if (editingUser) {
        // 编辑用户
        const updateData: UpdateUserParams = {
          email: values.email,
          phone: values.phone,
          user_type: values.user_type,
          is_active: values.is_active,
        };
        
        await updateUser(editingUser.id, updateData);
        message.success('用户更新成功');
      } else {
        // 创建用户
        const createData: CreateUserParams = {
          username: values.username,
          email: values.email,
          password: values.password,
          phone: values.phone,
          user_type: values.user_type,
          is_active: values.is_active,
        };
        
        await createUser(createData);
        message.success('用户创建成功');
      }
      
      setModalVisible(false);
      fetchUsers();
    } catch (error) {
      console.error('保存用户失败:', error);
      message.error('保存用户失败');
    }
  };

  /**
   * 处理删除用户
   */
  const handleDelete = async (userId: number) => {
    try {
      await deleteUser(userId);
      message.success('用户删除成功');
      fetchUsers();
    } catch (error) {
      console.error('删除用户失败:', error);
      message.error('删除用户失败');
    }
  };

  /**
   * 处理用户状态切换
   */
  const handleStatusChange = async (userId: number, isActive: boolean) => {
    try {
      await updateUser(userId, { is_active: isActive });
      message.success('用户状态更新成功');
      fetchUsers();
    } catch (error) {
      console.error('更新用户状态失败:', error);
      message.error('更新用户状态失败');
    }
  };

  // 表格列配置
  const columns = [
    {
      title: '用户ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '头像',
      dataIndex: 'avatar',
      key: 'avatar',
      width: 80,
      render: (_avatar: string, record: User) => (
        <Avatar 
          size={40} 
          src={record.avatar_url} 
          icon={<UserOutlined />}
        />
      ),
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      width: 120,
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '手机号',
      dataIndex: 'phone',
      key: 'phone',
      render: (phone: string) => phone || '-',
    },
    {
      title: '类型',
      dataIndex: 'user_type',
      key: 'user_type',
      width: 100,
      render: (userType: number) => {
        const typeMap: Record<number, { color: string; text: string }> = {
          1: { color: 'blue', text: '用户' },
          2: { color: 'green', text: '会员' },
          3: { color: 'red', text: '管理员' },
        };
        const info = typeMap[userType] || { color: 'default', text: String(userType) };
        return <Tag color={info.color}>{info.text}</Tag>;
      },
    },
    {
      title: '点数',
      dataIndex: 'points',
      key: 'points',
      width: 100,
      render: (points: number) => points || 0,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: number, record: User) => (
        <Switch
          checked={status === 1}
          onChange={(checked) => handleStatusChange(record.id, checked)}
        />
      ),
    },
    {
      title: '注册时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (createdAt: string) => new Date(createdAt).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_value: unknown, record: User) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<DollarOutlined />}
            onClick={() => showRechargeModal(record)}
          >
            充值
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => showEditModal(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个用户吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              danger
              size="small"
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <MainLayout>
      <div style={{ padding: '24px' }}>
        {/* 页面标题和操作区 */}
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ margin: 0 }}>用户管理</h1>
          <Space>
            <Search
              placeholder="搜索用户名、邮箱或手机号"
              allowClear
              enterButton={<SearchOutlined />}
              onSearch={handleSearch}
              style={{ width: 300 }}
            />
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={showCreateModal}
            >
              新建用户
            </Button>
          </Space>
        </div>

        {/* 用户表格 */}
        <Table
          columns={columns}
          dataSource={users}
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条/共 ${total} 条`,
          }}
          onChange={handleTableChange}
          rowKey="id"
          scroll={{ x: 1000 }}
        />

        {/* 创建/编辑用户模态框 */}
        <Modal
          title={editingUser ? '编辑用户' : '创建用户'}
          open={modalVisible}
          onCancel={() => setModalVisible(false)}
          footer={null}
          width={600}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
          >
            <Form.Item
              label="用户名"
              name="username"
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input placeholder="请输入用户名" />
            </Form.Item>

            <Form.Item
              label="邮箱"
              name="email"
              rules={[
                { required: true, message: '请输入邮箱' },
                { type: 'email', message: '请输入有效的邮箱地址' }
              ]}
            >
              <Input placeholder="请输入邮箱地址" />
            </Form.Item>

            {!editingUser && (
              <Form.Item
                label="密码"
                name="password"
                rules={[{ required: true, message: '请输入密码' }]}
              >
                <Input.Password placeholder="请输入密码" />
              </Form.Item>
            )}

            <Form.Item
              label="手机号"
              name="phone"
            >
              <Input placeholder="请输入手机号（可选）" />
            </Form.Item>

            <Form.Item
              label="用户类型"
              name="user_type"
              rules={[{ required: true, message: '请选择用户类型' }]}
              initialValue={1}
            >
              <select style={{ width: '100%', padding: '8px', border: '1px solid #d9d9d9', borderRadius: '6px' }}>
                <option value={1}>用户</option>
                <option value={2}>会员</option>
                <option value={3}>管理员</option>
              </select>
            </Form.Item>

            <Form.Item
              label="状态"
              name="is_active"
              valuePropName="checked"
              initialValue={true}
            >
              <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0 }}>
              <Space style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button onClick={() => setModalVisible(false)}>
                  取消
                </Button>
                <Button type="primary" htmlType="submit">
                  {editingUser ? '更新' : '创建'}
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Modal>

        {/* 点数充值模态框 */}
        <Modal
          title={`为 ${rechargingUser?.username} 充值点数`}
          open={rechargeModalVisible}
          onCancel={() => setRechargeModalVisible(false)}
          footer={null}
          width={500}
        >
          <Card size="small" style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>当前点数:</span>
              <span style={{ fontSize: '18px', fontWeight: 'bold', color: '#1890ff' }}>
                {rechargingUser?.points || 0}
              </span>
            </div>
          </Card>

          <Form
            form={rechargeForm}
            layout="vertical"
            onFinish={handleRecharge}
          >
            <Form.Item
              label="充值点数"
              name="points"
              rules={[{ required: true, message: '请输入充值点数' }]}
            >
              <Input type="number" placeholder="请输入充值点数" min={1} />
            </Form.Item>

            <Form.Item
              label="金额 (元)"
              name="amount"
              rules={[{ required: true, message: '请输入金额' }]}
            >
              <Input type="number" placeholder="请输入金额" min={0.01} step={0.01} />
            </Form.Item>

            <Form.Item
              label="支付方式"
              name="payment_method"
              rules={[{ required: true, message: '请选择支付方式' }]}
              initialValue="alipay"
            >
              <select style={{ width: '100%', padding: '8px', border: '1px solid #d9d9d9', borderRadius: '6px' }}>
                <option value="alipay">支付宝</option>
                <option value="wechat">微信支付</option>
                <option value="bank">银行卡</option>
              </select>
            </Form.Item>

            <Form.Item
              label="备注"
              name="description"
            >
              <Input.TextArea placeholder="请输入备注信息（可选）" rows={2} />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0 }}>
              <Space style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button onClick={() => setRechargeModalVisible(false)}>
                  取消
                </Button>
                <Button type="primary" htmlType="submit">
                  确认充值
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </MainLayout>
  );
};

export default Users;
