/**
 * 交易记录页面
 * 创建日期: 2025-01-08
 * 用途: 查看系统所有交易记录
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Space, Select, Tag, App } from 'antd';
import type { TablePaginationConfig } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { getAllTransactions, Transaction } from '@/services/user';
import MainLayout from '@/layouts/MainLayout';

const { Option } = Select;

const Transactions: React.FC = () => {
  const { message } = App.useApp();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const { current, pageSize } = pagination;
  
  const [filters, setFilters] = useState<{
    user_id?: number;
    type?: number;
  }>({});

  const fetchTransactions = useCallback(async (params: { page?: number; size?: number } = {}) => {
    try {
      setLoading(true);
      const response = await getAllTransactions({
        page: params.page || current,
        size: params.size || pageSize,
        ...filters
      });
      
      setTransactions(response.items);
      setPagination({
        current: response.page,
        pageSize: response.size,
        total: response.total,
      });
    } catch (error) {
      console.error('获取交易记录失败:', error);
      message.error('获取交易记录失败');
    } finally {
      setLoading(false);
    }
  }, [current, filters, message, pageSize]);

  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  const handleTableChange = (newPagination: TablePaginationConfig) => {
    const nextPage = newPagination.current || 1;
    const nextPageSize = newPagination.pageSize || pageSize;

    setPagination(prev => ({
      ...prev,
      current: nextPage,
      pageSize: nextPageSize,
    }));
    fetchTransactions({ 
      page: nextPage, 
      size: nextPageSize 
    });
  };

  const handleTypeChange = (value: number) => {
    setFilters(prev => ({ ...prev, type: value }));
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '用户ID',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 100,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type: number, record: Transaction) => {
        let color = 'default';
        if (type === 1) color = 'green'; // 充值
        if (type === 2) color = 'blue'; // 消费
        if (type === 3) color = 'orange'; // 退款
        return <Tag color={color}>{record.type_text}</Tag>;
      },
    },
    {
      title: '点数变动',
      dataIndex: 'points',
      key: 'points',
      width: 120,
      render: (points: number, record: Transaction) => {
        const isPositive = record.type === 1 || record.type === 3; // 充值或退款增加点数
        // 注意：消费通常是正数显示，但在余额变动中是减少。这里直接显示数值。
        // 如果后端返回的points是绝对值，我们可以根据类型加符号。
        return (
          <span style={{ color: isPositive ? 'green' : 'red', fontWeight: 'bold' }}>
            {isPositive ? '+' : '-'}{points}
          </span>
        );
      },
    },
    {
      title: '交易后余额',
      dataIndex: 'balance_after',
      key: 'balance_after',
      width: 120,
    },
    {
      title: '涉及金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      render: (amount: number) => amount ? `¥${amount.toFixed(2)}` : '-',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '交易时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString(),
    },
  ];

  return (
    <MainLayout>
      <div style={{ padding: '24px' }}>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ margin: 0 }}>交易记录</h1>
          <Space>
            <Select 
              placeholder="交易类型" 
              style={{ width: 120 }} 
              allowClear 
              onChange={handleTypeChange}
            >
              <Option value={1}>充值</Option>
              <Option value={2}>消费</Option>
              <Option value={3}>退款</Option>
            </Select>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => fetchTransactions({ page: 1 })}
            >
              刷新
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={transactions}
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
      </div>
    </MainLayout>
  );
};

export default Transactions;
