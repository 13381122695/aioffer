/**
 * 角色权限管理页面
 * 创建日期: 2025-01-08
 * 用途: 管理系统角色和权限
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Space, Input, Modal, Form, App, Popconfirm, Tag, Transfer } from 'antd';
import type { TablePaginationConfig } from 'antd';
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import { getRoles, createRole, updateRole, deleteRole, getAllPermissions, getRoleById, assignRolePermissions, Role, Permission } from '@/services/roles';
import MainLayout from '@/layouts/MainLayout';

const { Search } = Input;

type RoleFormValues = {
  name: string;
  description?: string;
};

type PaginationState = {
  current: number;
  pageSize: number;
  total: number;
};

const Roles: React.FC = () => {
  const { message } = App.useApp();
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [permissionModalVisible, setPermissionModalVisible] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [allPermissions, setAllPermissions] = useState<Permission[]>([]);
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]); // Transfer uses string keys
  
  const [form] = Form.useForm();
  
  const [pagination, setPagination] = useState<PaginationState>({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const { current, pageSize } = pagination;
  
  const [searchText, setSearchText] = useState('');

  const fetchRoles = useCallback(async (params: { page?: number; size?: number; search?: string } = {}) => {
    try {
      setLoading(true);
      const response = await getRoles({
        page: params.page || current,
        size: params.size || pageSize,
        search: params.search !== undefined ? params.search : searchText,
      });
      
      setRoles(response.items);
      setPagination({
        current: response.page,
        pageSize: response.size,
        total: response.total,
      });
    } catch (error) {
      console.error('获取角色列表失败:', error);
      message.error('获取角色列表失败');
    } finally {
      setLoading(false);
    }
  }, [current, message, pageSize, searchText]);

  useEffect(() => {
    fetchRoles();
  }, [fetchRoles]);

  const handleSearch = (value: string) => {
    setSearchText(value);
    setPagination(prev => ({ ...prev, current: 1 }));
    fetchRoles({ search: value, page: 1 });
  };

  const handleTableChange = (newPagination: TablePaginationConfig) => {
    setPagination(prev => ({
      ...prev,
      current: newPagination.current || 1,
      pageSize: newPagination.pageSize || prev.pageSize,
    }));
    fetchRoles({ 
      page: newPagination.current || 1, 
      size: newPagination.pageSize || pageSize 
    });
  };

  const showCreateModal = () => {
    setEditingRole(null);
    form.resetFields();
    setModalVisible(true);
  };

  const showEditModal = (role: Role) => {
    setEditingRole(role);
    form.setFieldsValue({
      name: role.name,
      description: role.description,
    });
    setModalVisible(true);
  };

  const handleSubmit = async (values: RoleFormValues) => {
    try {
      if (editingRole) {
        await updateRole(editingRole.id, values);
        message.success('角色更新成功');
      } else {
        await createRole(values);
        message.success('角色创建成功');
      }
      setModalVisible(false);
      fetchRoles();
    } catch (error) {
      console.error('保存角色失败:', error);
      message.error('保存角色失败');
    }
  };

  const handleDelete = async (roleId: number) => {
    try {
      await deleteRole(roleId);
      message.success('角色删除成功');
      fetchRoles();
    } catch (error) {
      console.error('删除角色失败:', error);
      message.error('删除角色失败');
    }
  };

  const showPermissionModal = async (role: Role) => {
    try {
      setEditingRole(role);
      // Fetch all permissions if not already fetched
      if (allPermissions.length === 0) {
        const perms = await getAllPermissions();
        setAllPermissions(perms);
      }
      
      setPermissionModalVisible(true);
      // Reset selection first
      setSelectedPermissions([]);
      
      // Fetch role details (including permissions)
      const roleDetail = await getRoleById(role.id);
      const currentPermIds = roleDetail.permissions?.map(p => p.id.toString()) || [];
      setSelectedPermissions(currentPermIds);
      
    } catch (error) {
      console.error('加载权限数据失败:', error);
      message.error('加载权限数据失败');
    }
  };

  const handlePermissionSubmit = async () => {
    if (!editingRole) return;
    try {
      const permissionIds = selectedPermissions.map(id => parseInt(id));
      await assignRolePermissions(editingRole.id, permissionIds);
      message.success('权限分配成功');
      setPermissionModalVisible(false);
      fetchRoles();
    } catch (error) {
      console.error('分配权限失败:', error);
      message.error('分配权限失败');
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '角色名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '类型',
      dataIndex: 'is_system',
      key: 'is_system',
      width: 100,
      render: (isSystem: boolean) => (
        <Tag color={isSystem ? 'red' : 'blue'}>
          {isSystem ? '系统角色' : '自定义'}
        </Tag>
      ),
    },
    {
      title: '权限数',
      dataIndex: 'permission_count',
      key: 'permission_count',
      width: 100,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 250,
      render: (_value: unknown, record: Role) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<SafetyCertificateOutlined />}
            onClick={() => showPermissionModal(record)}
            disabled={record.is_system} // 系统角色通常不可修改权限? Design doc says "System role not allowed to modify permissions".
          >
            分配权限
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => showEditModal(record)}
            disabled={record.is_system}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个角色吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
            disabled={record.is_system}
          >
            <Button
              type="link"
              danger
              size="small"
              icon={<DeleteOutlined />}
              disabled={record.is_system}
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
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ margin: 0 }}>角色权限</h1>
          <Space>
            <Search
              placeholder="搜索角色..."
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
              新建角色
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={roles}
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
        />

        {/* 创建/编辑角色模态框 */}
        <Modal
          title={editingRole ? '编辑角色' : '新建角色'}
          open={modalVisible}
          onOk={() => form.submit()}
          onCancel={() => setModalVisible(false)}
          width={500}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
          >
            <Form.Item
              label="角色名称"
              name="name"
              rules={[{ required: true, message: '请输入角色名称' }]}
            >
              <Input placeholder="请输入角色名称" />
            </Form.Item>

            <Form.Item
              label="描述"
              name="description"
            >
              <Input.TextArea placeholder="请输入角色描述" rows={3} />
            </Form.Item>
          </Form>
        </Modal>

        {/* 分配权限模态框 */}
        <Modal
          title={`分配权限 - ${editingRole?.name}`}
          open={permissionModalVisible}
          onOk={handlePermissionSubmit}
          onCancel={() => setPermissionModalVisible(false)}
          width={800}
        >
          <Transfer
            dataSource={allPermissions.map(p => ({
              key: p.id.toString(),
              title: `${p.name} (${p.resource}:${p.action})`,
              description: p.description,
            }))}
            titles={['可选权限', '已选权限']}
            targetKeys={selectedPermissions}
            onChange={(nextTargetKeys) => setSelectedPermissions(nextTargetKeys.map(String))}
            render={(item) => item.title}
            listStyle={{
              width: 350,
              height: 400,
            }}
            showSearch
          />
        </Modal>
      </div>
    </MainLayout>
  );
};

export default Roles;
