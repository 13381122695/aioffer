/**
 * 支付模态框组件
 * 创建日期: 2025-01-08
 * 用途: 处理订单支付流程
 */

import React, { useState, useEffect } from 'react';
import { Modal, Button, Space, QRCode, App, Card, Typography, Badge } from 'antd';
import { QrcodeOutlined, AlipayOutlined, WechatOutlined, CreditCardOutlined } from '@ant-design/icons';
import { initiatePayment, confirmPayment, PaymentParams, PaymentResponse, Order } from '@/services/orders';

const { Title, Text } = Typography;

interface PaymentModalProps {
  open: boolean;
  order: Order | null;
  onClose: () => void;
  onSuccess: () => void;
}

const PaymentModal: React.FC<PaymentModalProps> = ({ open, order, onClose, onSuccess }) => {
  const { message } = App.useApp();
  const [loading, setLoading] = useState(false);
  const [paymentInfo, setPaymentInfo] = useState<PaymentResponse | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<string>('alipay');
  const [checkingPayment, setCheckingPayment] = useState(false);

  useEffect(() => {
    if (open && order) {
      // 重置状态
      setPaymentInfo(null);
      setCheckingPayment(false);
    }
  }, [open, order]);

  /**
   * 发起支付
   */
  const handleInitiatePayment = async (method: string) => {
    if (!order) return;

    try {
      setLoading(true);
      setPaymentMethod(method);
      
      const params: PaymentParams = {
        order_id: order.id,
        payment_method: method,
      };
      
      const response = await initiatePayment(params);
      setPaymentInfo(response);
      
      // 如果是扫码支付，开始轮询检查支付状态
      if (method === 'alipay' || method === 'wechat') {
        startPaymentCheck(response.payment_id);
      }
    } catch (error) {
      console.error('发起支付失败:', error);
      message.error('发起支付失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 开始检查支付状态
   */
  const startPaymentCheck = (paymentId: string) => {
    setCheckingPayment(true);
    
    const checkInterval = setInterval(async () => {
      try {
        const result = await confirmPayment(paymentId);
        if (result.status === 'paid') {
          clearInterval(checkInterval);
          setCheckingPayment(false);
          message.success('支付成功！');
          onSuccess();
        }
      } catch (error) {
        void error;
      }
    }, 2000);

    // 5分钟后停止检查
    setTimeout(() => {
      clearInterval(checkInterval);
      setCheckingPayment(false);
    }, 300000);
  };

  /**
   * 手动确认支付
   */
  const handleManualConfirm = async () => {
    if (!paymentInfo) return;

    try {
      setCheckingPayment(true);
      await confirmPayment(paymentInfo.payment_id);
      message.success('支付确认成功！');
      onSuccess();
    } catch {
      message.error('支付确认失败，请稍后重试');
    } finally {
      setCheckingPayment(false);
    }
  };

  /**
   * 获取支付方式图标
   */
  const getPaymentIcon = (method: string) => {
    switch (method) {
      case 'alipay':
        return <AlipayOutlined style={{ fontSize: '24px', color: '#1677FF' }} />;
      case 'wechat':
        return <WechatOutlined style={{ fontSize: '24px', color: '#52C41A' }} />;
      case 'bank':
        return <CreditCardOutlined style={{ fontSize: '24px', color: '#FA8C16' }} />;
      default:
        return <QrcodeOutlined style={{ fontSize: '24px' }} />;
    }
  };

  /**
   * 获取支付方式名称
   */
  const getPaymentName = (method: string) => {
    switch (method) {
      case 'alipay':
        return '支付宝';
      case 'wechat':
        return '微信支付';
      case 'bank':
        return '银行卡';
      default:
        return '扫码支付';
    }
  };

  return (
    <Modal
      title="订单支付"
      open={open}
      onCancel={onClose}
      footer={null}
      width={500}
    >
      {order && (
        <div>
          {/* 订单信息 */}
          <Card size="small" style={{ marginBottom: 16 }}>
            <div style={{ textAlign: 'center', marginBottom: 16 }}>
              <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
                ¥{order.amount.toFixed(2)}
              </Title>
              <Text type="secondary">订单号: {order.order_no}</Text>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text>购买点数: <strong>{order.points}</strong></Text>
              <Text>订单状态: <Badge status="processing" text="待支付" /></Text>
            </div>
          </Card>

          {!paymentInfo ? (
            // 选择支付方式
            <div>
              <Title level={4} style={{ marginBottom: 16 }}>选择支付方式</Title>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Button
                  size="large"
                  style={{ width: '100%', height: 60 }}
                  onClick={() => handleInitiatePayment('alipay')}
                  loading={loading}
                >
                  <Space>
                    {getPaymentIcon('alipay')}
                    <span style={{ fontSize: 16 }}>{getPaymentName('alipay')}</span>
                  </Space>
                </Button>
                
                <Button
                  size="large"
                  style={{ width: '100%', height: 60 }}
                  onClick={() => handleInitiatePayment('wechat')}
                  loading={loading}
                >
                  <Space>
                    {getPaymentIcon('wechat')}
                    <span style={{ fontSize: 16 }}>{getPaymentName('wechat')}</span>
                  </Space>
                </Button>
                
                <Button
                  size="large"
                  style={{ width: '100%', height: 60 }}
                  onClick={() => handleInitiatePayment('bank')}
                  loading={loading}
                >
                  <Space>
                    {getPaymentIcon('bank')}
                    <span style={{ fontSize: 16 }}>{getPaymentName('bank')}</span>
                  </Space>
                </Button>
              </Space>
            </div>
          ) : (
            // 支付二维码
            <div style={{ textAlign: 'center' }}>
              <Title level={4} style={{ marginBottom: 16 }}>
                请使用{getPaymentName(paymentMethod)}扫码支付
              </Title>
              <div style={{ marginBottom: 24 }}>
                <QRCode
                  value={paymentInfo.payment_url}
                  size={200}
                />
              </div>
              <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
                支付二维码有效期为5分钟，请及时扫码支付
              </Text>
              
              <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                <Button
                  type="primary"
                  onClick={handleManualConfirm}
                  loading={checkingPayment}
                >
                  我已支付
                </Button>
                <Button onClick={onClose}>
                  取消支付
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </Modal>
  );
};

export default PaymentModal;
