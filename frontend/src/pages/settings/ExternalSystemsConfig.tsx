/**
 * 外部系统配置页面
 * 创建日期: 2025-01-08
 * 用途: 配置外部系统参数
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Space, Input, Modal, Form, App, Popconfirm, Tag, Switch, Select } from 'antd';
import type { TablePaginationConfig } from 'antd';
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { getExternalSystems, createExternalSystem, updateExternalSystem, deleteExternalSystem, ExternalSystem } from '@/services/externalSystems';
import MainLayout from '@/layouts/MainLayout';

const { Search } = Input;
const { Option } = Select;

type ExternalSystemFormValues = {
  name: string;
  system_type: 'api' | 'page' | 'iframe';
  page_url?: string;
  endpoint_url?: string;
  api_key?: string;
  api_secret?: string;
  config?: string;
  is_active?: boolean;
};

type PaginationState = {
  current: number;
  pageSize: number;
  total: number;
};

const ExternalSystemsConfig: React.FC = () => {
  const { message } = App.useApp();
  const [systems, setSystems] = useState<ExternalSystem[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingSystem, setEditingSystem] = useState<ExternalSystem | null>(null);
  const [form] = Form.useForm();
  
  const [pagination, setPagination] = useState<PaginationState>({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const { current, pageSize } = pagination;
  
  const [searchText, setSearchText] = useState('');

  const fetchSystems = useCallback(async (params: { page?: number; size?: number; search?: string } = {}) => {
    try {
      setLoading(true);
      const response = await getExternalSystems({
        page: params.page || current,
        size: params.size || pageSize,
        search: params.search !== undefined ? params.search : searchText,
      });
      
      setSystems(response.items);
      setPagination({
        current: response.page,
        pageSize: response.size,
        total: response.total,
      });
    } catch (error) {
      console.error('获取外部系统列表失败:', error);
      message.error('获取外部系统列表失败');
    } finally {
      setLoading(false);
    }
  }, [current, message, pageSize, searchText]);

  useEffect(() => {
    fetchSystems();
  }, [fetchSystems]);

  const handleSearch = (value: string) => {
    setSearchText(value);
    setPagination(prev => ({ ...prev, current: 1 }));
    fetchSystems({ search: value, page: 1 });
  };

  const handleTableChange = (newPagination: TablePaginationConfig) => {
    setPagination(prev => ({
      ...prev,
      current: newPagination.current || 1,
      pageSize: newPagination.pageSize || prev.pageSize,
    }));
    fetchSystems({ 
      page: newPagination.current || 1, 
      size: newPagination.pageSize || pageSize 
    });
  };

  const showCreateModal = () => {
    setEditingSystem(null);
    form.resetFields();
    setModalVisible(true);
  };

  const showEditModal = (system: ExternalSystem) => {
    setEditingSystem(system);
    form.setFieldsValue({
      name: system.name,
      system_type: system.system_type,
      page_url: system.page_url ?? undefined,
      endpoint_url: system.endpoint_url ?? undefined,
      api_key: undefined,
      api_secret: undefined,
      config: system.config ? JSON.stringify(system.config, null, 2) : '',
      is_active: system.is_active,
    });
    setModalVisible(true);
  };

  const handleSubmit = async (values: ExternalSystemFormValues) => {
    try {
      let config: Record<string, unknown> | undefined;
      const configText = values.config?.trim();
      if (configText) {
        config = JSON.parse(configText) as Record<string, unknown>;
      }

      const apiKey = values.api_key?.trim() || undefined;
      const apiSecret = values.api_secret?.trim() || undefined;
      const pageUrl = values.page_url?.trim() || undefined;
      const endpointUrl = values.endpoint_url?.trim() || undefined;

      const payload = {
        name: values.name,
        system_type: values.system_type,
        page_url: pageUrl,
        endpoint_url: endpointUrl,
        api_key: apiKey,
        api_secret: apiSecret,
        config,
        is_active: values.is_active,
      };

      if (editingSystem) {
        await updateExternalSystem(editingSystem.id, payload);
        message.success('外部系统更新成功');
      } else {
        await createExternalSystem(payload);
        message.success('外部系统创建成功');
      }
      setModalVisible(false);
      fetchSystems();
    } catch (error) {
      if (error instanceof SyntaxError) {
        message.error('配置参数必须是合法 JSON');
        return;
      }
      console.error('保存外部系统失败:', error);
      message.error('保存外部系统失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteExternalSystem(id);
      message.success('外部系统删除成功');
      fetchSystems();
    } catch (error) {
      console.error('删除外部系统失败:', error);
      message.error('删除外部系统失败');
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
      title: '系统名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '类型',
      dataIndex: 'system_type',
      key: 'system_type',
      width: 100,
      render: (systemType: ExternalSystem['system_type']) => {
        const colorMap: Record<ExternalSystem['system_type'], string> = {
          api: 'green',
          page: 'orange',
          iframe: 'blue',
        };
        return <Tag color={colorMap[systemType]}>{systemType}</Tag>;
      },
    },
    {
      title: '页面URL',
      dataIndex: 'page_url',
      key: 'page_url',
      ellipsis: true,
      render: (url: string | null | undefined) => url || '-',
    },
    {
      title: 'API端点',
      dataIndex: 'endpoint_url',
      key: 'endpoint_url',
      ellipsis: true,
      render: (url: string | null | undefined) => url || '-',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (createdAt: string) => new Date(createdAt).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_value: unknown, record: ExternalSystem) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => showEditModal(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个系统吗？"
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
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ margin: 0 }}>外部系统配置</h1>
          <Space>
            <Search
              placeholder="搜索系统..."
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
              新建系统
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={systems}
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

        <Modal
          title={editingSystem ? '编辑系统' : '新建系统'}
          open={modalVisible}
          onOk={() => form.submit()}
          onCancel={() => setModalVisible(false)}
          width={600}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            initialValues={{ is_active: true, system_type: 'iframe' }}
          >
            <Form.Item
              label="系统名称"
              name="name"
              rules={[{ required: true, message: '请输入系统名称' }]}
            >
              <Input placeholder="请输入系统名称" />
            </Form.Item>

            <Form.Item
              label="系统类型"
              name="system_type"
              rules={[{ required: true, message: '请选择系统类型' }]}
            >
              <Select>
                <Option value="iframe">iframe（嵌入）</Option>
                <Option value="page">page（页面）</Option>
                <Option value="api">api（接口）</Option>
              </Select>
            </Form.Item>

            <Form.Item
              label="页面URL"
              name="page_url"
              dependencies={['system_type']}
              rules={[
                ({ getFieldValue }) => ({
                  validator: async (_rule, value) => {
                    const systemType = getFieldValue('system_type') as ExternalSystemFormValues['system_type'] | undefined;
                    if ((systemType === 'iframe' || systemType === 'page') && (!value || !String(value).trim())) {
                      return Promise.reject(new Error('iframe/page 类型必须填写页面URL'));
                    }
                    return Promise.resolve();
                  }
                })
              ]}
            >
              <Input placeholder="iframe/page 类型需要" />
            </Form.Item>

            <Form.Item
              label="API端点"
              name="endpoint_url"
              dependencies={['system_type']}
              rules={[
                ({ getFieldValue }) => ({
                  validator: async (_rule, value) => {
                    const systemType = getFieldValue('system_type') as ExternalSystemFormValues['system_type'] | undefined;
                    if (systemType === 'api' && (!value || !String(value).trim())) {
                      return Promise.reject(new Error('api 类型必须填写 API 端点'));
                    }
                    return Promise.resolve();
                  }
                })
              ]}
            >
              <Input placeholder="api 类型需要" />
            </Form.Item>

            <Form.Item
              label="API Key"
              name="api_key"
            >
              <Input.Password placeholder={editingSystem ? '已保存（不回显），留空表示不修改' : '可选'} />
            </Form.Item>

            <Form.Item
              label="API Secret"
              name="api_secret"
            >
              <Input.Password placeholder={editingSystem ? '已保存（不回显），留空表示不修改' : '可选'} />
            </Form.Item>

            <Form.Item
              label="配置参数 (JSON)"
              name="config"
            >
              <Input.TextArea placeholder='{"key": "value"}' rows={3} />
            </Form.Item>

            <Form.Item
              label="是否启用"
              name="is_active"
              valuePropName="checked"
            >
              <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </MainLayout>
  );
};

export default ExternalSystemsConfig;
