/**
 * 会员管理页面
 * 创建日期: 2025-01-08
 * 用途: 管理系统会员用户
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Space, Input, Switch, Modal, Form, Avatar, Popconfirm, Card, App, Descriptions, List, Tag } from 'antd';
import type { TablePaginationConfig } from 'antd';
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined, UserOutlined, DollarOutlined } from '@ant-design/icons';
import { getUserList, getCurrentUser, createUser, updateUser, deleteUser, rechargePoints, User, CreateUserParams, UpdateUserParams } from '@/services/user';
import { getProducts, createAlipayRecharge, Product } from '@/services/orders';
import MainLayout from '@/layouts/MainLayout';
import { useAuthStore } from '@/stores/auth';

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

type MemberFormValues = {
  username: string;
  email: string;
  password?: string;
  phone?: string;
  user_type?: number;
  is_active: boolean;
};

const Members: React.FC = () => {
  const { message } = App.useApp();
  const { user: authUser } = useAuthStore();
  const isMemberMode = authUser?.role === 'member';
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
  const [pointsProducts, setPointsProducts] = useState<Product[]>([]);
  const [subscriptionProducts, setSubscriptionProducts] = useState<Product[]>([]);
  const [loadingProducts, setLoadingProducts] = useState(false);

  // 获取会员列表
  const fetchUsers = useCallback(async (params: { page?: number; size?: number; search?: string } = {}) => {
    try {
      setLoading(true);
      if (isMemberMode) {
        const currentUser = await getCurrentUser();
        setUsers(currentUser ? [currentUser] : []);
        setPagination({
          current: 1,
          pageSize: 1,
          total: currentUser ? 1 : 0,
        });
        return;
      }

      const response = await getUserList({
        page: params.page || current,
        size: params.size || pageSize,
        search: params.search !== undefined ? params.search : searchText,
        user_type: 2,
      });

      setUsers(response.items);
      setPagination({
        current: response.page,
        pageSize: response.size,
        total: response.total,
      });
    } catch (error) {
      console.error('获取会员列表失败:', error);
      message.error('获取会员列表失败');
    } finally {
      setLoading(false);
    }
  }, [current, isMemberMode, message, pageSize, searchText]);

  // 组件加载时获取用户列表
  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  useEffect(() => {
    const loadProducts = async () => {
      if (!isMemberMode) {
        return;
      }
      try {
        setLoadingProducts(true);
        const products = await getProducts();
        setPointsProducts(products.filter((p) => p.type === 'points'));
        setSubscriptionProducts(products.filter((p) => p.type === 'subscription'));
      } catch (error) {
        console.error('获取充值套餐失败:', error);
        message.error('获取充值套餐失败');
      } finally {
        setLoadingProducts(false);
      }
    };

    void loadProducts();
  }, [isMemberMode, message]);

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

  const handleAlipayRecharge = async (product: Product) => {
    try {
      const resp = await createAlipayRecharge({
        product_id: product.id,
        amount: product.price,
        client_type: 'h5',
      });
      const targetUrl = resp.alipay_scheme || resp.pay_url;
      if (targetUrl) {
        window.location.href = targetUrl;
      } else {
        message.error('未获取到支付链接');
      }
    } catch (error) {
      console.error('发起支付宝充值失败:', error);
      message.error('发起支付宝充值失败');
    }
  };

  /**
   * 处理表格分页变化
   */
  const handleTableChange = (newPagination: TablePaginationConfig) => {
    const nextPage = newPagination.current || 1;
    const nextPageSize = newPagination.pageSize || pageSize;

    setPagination(prev => ({
      ...prev,
      current: nextPage,
      pageSize: nextPageSize,
    }));
    fetchUsers({
      page: nextPage,
      size: nextPageSize,
    });
  };

  /**
   * 显示创建用户模态框
   */
  const showCreateModal = () => {
    setEditingUser(null);
    form.resetFields();
    // 默认设置为会员
    form.setFieldValue('role', 'member');
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
      user_type: 2,
      is_active: user.status === 1,
    });
    setModalVisible(true);
  };

  /**
   * 处理创建或更新用户
   */
  const handleSubmit = async (values: MemberFormValues) => {
    try {
      // 映射 role 到 user_type (这里简化处理，实际应该在 request 或 service 层处理)
      // 但 CreateUserParams 还没更新 user_type 类型定义，所以暂时依赖后端默认或后续修改
      // 实际上后端 create_user 目前默认 user_type=1。
      // 我们需要修改 service/user.ts 和调用处来支持 user_type。
      // 暂时先这样，创建出来的可能是普通用户。
      
      if (editingUser) {
        // 编辑用户
        const updateData: UpdateUserParams = {
          email: values.email,
          phone: values.phone,
          user_type: 2,
          is_active: values.is_active,
        };
        
        await updateUser(editingUser.id, updateData);
        message.success('会员更新成功');
      } else {
        // 创建用户
        const createData: CreateUserParams = {
          username: values.username,
          email: values.email,
          password: values.password,
          phone: values.phone,
          user_type: 2,
          is_active: values.is_active,
        };
        
        await createUser(createData);
        message.success('会员创建成功');
      }
      
      setModalVisible(false);
      fetchUsers();
    } catch (error) {
      console.error('保存会员失败:', error);
      message.error('保存会员失败');
    }
  };

  /**
   * 处理删除用户
   */
  const handleDelete = async (userId: number) => {
    try {
      await deleteUser(userId);
      message.success('会员删除成功');
      fetchUsers();
    } catch (error) {
      console.error('删除会员失败:', error);
      message.error('删除会员失败');
    }
  };

  /**
   * 处理用户状态切换
   */
  const handleStatusChange = async (userId: number, isActive: boolean) => {
    try {
      await updateUser(userId, { is_active: isActive });
      message.success('会员状态更新成功');
      fetchUsers();
    } catch (error) {
      console.error('更新会员状态失败:', error);
      message.error('更新会员状态失败');
    }
  };

  // 表格列配置
  const columns = [
    {
      title: '会员ID',
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
      render: (_text: unknown, record: User) => (
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
            title="确定要删除这个会员吗？"
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

  const currentAccount = users[0];

  return (
    <MainLayout>
      <div style={{ padding: '24px' }}>
        {/* 页面标题和操作区 */}
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ margin: 0 }}>{isMemberMode ? '我的账户' : '会员管理'}</h1>
          {!isMemberMode && (
            <Space>
              <Search
                placeholder="搜索会员..."
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
                新建会员
              </Button>
            </Space>
          )}
        </div>

        {isMemberMode ? (
          <>
            <Card loading={loading} style={{ marginBottom: 24 }}>
              {currentAccount ? (
                <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
                  <Avatar size={72} src={currentAccount.avatar_url} icon={<UserOutlined />} />
                  <Descriptions column={2} bordered size="middle">
                    <Descriptions.Item label="用户ID">{currentAccount.id}</Descriptions.Item>
                    <Descriptions.Item label="用户名">{currentAccount.username}</Descriptions.Item>
                    <Descriptions.Item label="邮箱">{currentAccount.email || '-'}</Descriptions.Item>
                    <Descriptions.Item label="手机号">{currentAccount.phone || '-'}</Descriptions.Item>
                    <Descriptions.Item label="点数">{authUser?.points ?? currentAccount.points ?? 0}</Descriptions.Item>
                  <Descriptions.Item label="会员到期">
                    {currentAccount.member?.expired_at
                      ? new Date(currentAccount.member.expired_at).toLocaleString()
                      : '-'}
                  </Descriptions.Item>
                    <Descriptions.Item label="注册时间">
                      {currentAccount.created_at ? new Date(currentAccount.created_at).toLocaleString() : '-'}
                    </Descriptions.Item>
                  </Descriptions>
                </div>
              ) : (
                <div>暂无账户信息</div>
              )}
            </Card>

            <Card
              title="点数充值"
              loading={loadingProducts}
            >
              {pointsProducts.length === 0 ? (
                <div>暂无可用的充值套餐，请稍后再试。</div>
              ) : (
                <List
                  dataSource={pointsProducts}
                  renderItem={(item) => (
                    <List.Item
                      actions={[
                        <Button
                          key="pay"
                          type="primary"
                          onClick={() => handleAlipayRecharge(item)}
                        >
                          支付宝支付
                        </Button>,
                      ]}
                    >
                      <List.Item.Meta
                        title={
                          <Space>
                            <span>{item.name}</span>
                            <Tag color="blue">{item.points ?? 0} 点</Tag>
                          </Space>
                        }
                        description={item.description || ''}
                      />
                      <div style={{ fontSize: 16, fontWeight: 'bold', color: '#fa541c' }}>
                        ¥{item.price.toFixed(2)}
                      </div>
                    </List.Item>
                  )}
                />
              )}
            </Card>

            <Card
              title="时长套餐"
              loading={loadingProducts}
              style={{ marginTop: 24 }}
            >
              {subscriptionProducts.length === 0 ? (
                <div>暂无可用的时长套餐，请稍后再试。</div>
              ) : (
                <List
                  dataSource={subscriptionProducts}
                  renderItem={(item) => (
                    <List.Item
                      actions={[
                        <Button
                          key="pay"
                          type="primary"
                          onClick={() => handleAlipayRecharge(item)}
                        >
                          支付宝支付
                        </Button>,
                      ]}
                    >
                      <List.Item.Meta
                        title={
                          <Space>
                            <span>{item.name}</span>
                            <Tag color="purple">{item.duration ?? 0} 天</Tag>
                          </Space>
                        }
                        description={item.description || ''}
                      />
                      <div style={{ fontSize: 16, fontWeight: 'bold', color: '#fa541c' }}>
                        ¥{item.price.toFixed(2)}
                      </div>
                    </List.Item>
                  )}
                />
              )}
            </Card>
          </>
        ) : (
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
        )}

        {!isMemberMode && (
          <>
            {/* 创建/编辑用户模态框 */}
            <Modal
              title={editingUser ? '编辑会员' : '创建会员'}
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
              initialValue={2}
              hidden
            >
              <Input />
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
          </>
        )}
      </div>
    </MainLayout>
  );
};

export default Members;
