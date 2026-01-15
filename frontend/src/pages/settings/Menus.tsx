/**
 * 菜单管理页面
 * 创建日期: 2025-01-08
 * 用途: 管理系统菜单
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Space, Input, Modal, Form, App, Popconfirm, Tag, InputNumber, Switch, TreeSelect } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { getMenus, createMenu, updateMenu, deleteMenu, Menu } from '@/services/menus';
import MainLayout from '@/layouts/MainLayout';
import * as AntdIcons from '@ant-design/icons';

type MenuFormValues = {
  name: string;
  code: string;
  path?: string;
  component?: string;
  icon?: string;
  sort?: number;
  is_visible?: boolean;
  parent_id?: number;
};

const Menus: React.FC = () => {
  const { message } = App.useApp();
  const [menus, setMenus] = useState<Menu[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingMenu, setEditingMenu] = useState<Menu | null>(null);
  const [form] = Form.useForm();

  const fetchMenus = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getMenus();
      setMenus(data);
    } catch (error) {
      console.error('获取菜单列表失败:', error);
      message.error('获取菜单列表失败');
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    fetchMenus();
  }, [fetchMenus]);

  const showCreateModal = (parent?: Menu) => {
    setEditingMenu(null);
    form.resetFields();
    if (parent) {
      form.setFieldValue('parent_id', parent.id);
    }
    setModalVisible(true);
  };

  const showEditModal = (menu: Menu) => {
    setEditingMenu(menu);
    form.setFieldsValue({
      name: menu.name,
      code: menu.code,
      path: menu.path,
      component: menu.component,
      icon: menu.icon,
      sort: menu.sort,
      is_visible: menu.is_visible,
      parent_id: menu.parent_id,
    });
    setModalVisible(true);
  };

  const handleSubmit = async (values: MenuFormValues) => {
    try {
      if (editingMenu) {
        await updateMenu(editingMenu.id, values);
        message.success('菜单更新成功');
      } else {
        await createMenu(values);
        message.success('菜单创建成功');
      }
      setModalVisible(false);
      fetchMenus();
    } catch (error) {
      console.error('保存菜单失败:', error);
      message.error('保存菜单失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteMenu(id);
      message.success('菜单删除成功');
      fetchMenus();
    } catch (error) {
      console.error('删除菜单失败:', error);
      message.error('删除菜单失败');
    }
  };

  // Helper to render icon
  const renderIcon = (iconName?: string) => {
    if (!iconName) return null;
    const Icon = (AntdIcons as unknown as Record<string, React.ComponentType>)[iconName];
    return Icon ? <Icon /> : null;
  };

  const columns = [
    {
      title: '菜单名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Menu) => (
        <Space>
          {renderIcon(record.icon)}
          {text}
        </Space>
      ),
    },
    {
      title: '编码',
      dataIndex: 'code',
      key: 'code',
    },
    {
      title: '路径',
      dataIndex: 'path',
      key: 'path',
    },
    {
      title: '组件',
      dataIndex: 'component',
      key: 'component',
    },
    {
      title: '排序',
      dataIndex: 'sort',
      key: 'sort',
      width: 80,
    },
    {
      title: '可见',
      dataIndex: 'is_visible',
      key: 'is_visible',
      width: 80,
      render: (visible: boolean) => (
        <Tag color={visible ? 'green' : 'red'}>
          {visible ? '是' : '否'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_value: unknown, record: Menu) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<PlusOutlined />}
            onClick={() => showCreateModal(record)}
          >
            添加子菜单
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
            title="确定要删除这个菜单吗？"
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
          <h1 style={{ margin: 0 }}>菜单管理</h1>
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={() => showCreateModal()}
          >
            新建菜单
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={menus}
          loading={loading}
          rowKey="id"
          pagination={false}
          defaultExpandAllRows
        />

        <Modal
          title={editingMenu ? '编辑菜单' : '新建菜单'}
          open={modalVisible}
          onOk={() => form.submit()}
          onCancel={() => setModalVisible(false)}
          width={600}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            initialValues={{ sort: 0, is_visible: true }}
          >
            <Form.Item
              label="上级菜单"
              name="parent_id"
            >
              <TreeSelect
                treeData={menus}
                fieldNames={{ label: 'name', value: 'id', children: 'children' }}
                placeholder="选择上级菜单（留空为顶级菜单）"
                allowClear
                treeDefaultExpandAll
              />
            </Form.Item>

            <Form.Item
              label="菜单名称"
              name="name"
              rules={[{ required: true, message: '请输入菜单名称' }]}
            >
              <Input placeholder="请输入菜单名称" />
            </Form.Item>

            <Form.Item
              label="菜单编码"
              name="code"
              rules={[{ required: true, message: '请输入菜单编码' }]}
            >
              <Input placeholder="请输入菜单编码 (唯一标识)" />
            </Form.Item>

            <Form.Item
              label="路由路径"
              name="path"
            >
              <Input placeholder="请输入路由路径 (如 /dashboard)" />
            </Form.Item>

            <Form.Item
              label="组件路径"
              name="component"
            >
              <Input placeholder="请输入组件路径 (如 Layout/MainLayout)" />
            </Form.Item>

            <Form.Item
              label="图标"
              name="icon"
            >
              <Input placeholder="请输入Antd图标名称 (如 UserOutlined)" />
            </Form.Item>

            <Form.Item
              label="排序"
              name="sort"
            >
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              label="是否可见"
              name="is_visible"
              valuePropName="checked"
            >
              <Switch checkedChildren="可见" unCheckedChildren="隐藏" />
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </MainLayout>
  );
};

export default Menus;
