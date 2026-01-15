/**
 * 外部系统集成页面
 * 创建日期: 2025-01-08
 * 用途: 管理和访问外部系统集成，支持iframe和SSO集成
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, Row, Col, Button, Modal, Spin, App, Empty, Tag, Space, Tooltip } from 'antd';
import { 
  GlobalOutlined, 
  SettingOutlined,
  LoginOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import MainLayout from '@/layouts/MainLayout';
import { useNavigate } from 'react-router-dom';
import {
  getExternalSystemAccess,
  getExternalSystemIntegrationConfig,
  getUserAccessibleExternalSystems,
  type AccessibleExternalSystem
} from '@/services/externalSystems';
import { useAuthStore } from '@/stores/auth';

interface SystemAccess {
  system_id: number;
  user_id: number;
  access_token: string;
  expires_at: string;
}

const ExternalSystems: React.FC = () => {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [systems, setSystems] = useState<AccessibleExternalSystem[]>([]);
  const [loading, setLoading] = useState(false);
  const [accessModalVisible, setAccessModalVisible] = useState(false);
  const [selectedSystem, setSelectedSystem] = useState<AccessibleExternalSystem | null>(null);
  const [systemAccess, setSystemAccess] = useState<SystemAccess | null>(null);
  const [iframeLoading, setIframeLoading] = useState(false);
  const [iframeSrc, setIframeSrc] = useState<string | null>(null);
  const [iframeSandbox, setIframeSandbox] = useState('allow-scripts allow-same-origin allow-forms allow-popups');
  const [iframeAllowFullScreen, setIframeAllowFullScreen] = useState(true);
  const [iframeWidth, setIframeWidth] = useState('100%');
  const [iframeBodyHeight, setIframeBodyHeight] = useState('70vh');
  const [integrationConfigJson, setIntegrationConfigJson] = useState<string | null>(null);
  const [ssoUrl, setSsoUrl] = useState<string | null>(null);
  const [ssoCallbackUrl, setSsoCallbackUrl] = useState<string | null>(null);
  const [ssoClientId, setSsoClientId] = useState<string | null>(null);
  const [ssoScope, setSsoScope] = useState<string | null>(null);

  const isAdmin = user?.role === 'admin';
  const pageTitle = user?.role === 'member' ? '入学评估' : '外部系统集成';
  const systemLabel = user?.role === 'member' ? '入学评估' : '外部系统';

  const getErrorText = (error: unknown) => {
    if (typeof error === 'string' && error.trim()) return error;

    if (error && typeof error === 'object') {
      const err = error as { message?: unknown; response?: { data?: unknown } };
      const data = err.response?.data;

      if (data && typeof data === 'object') {
        const detail = (data as { detail?: unknown }).detail;
        if (typeof detail === 'string' && detail.trim()) return detail;

        const messageText = (data as { message?: unknown }).message;
        if (typeof messageText === 'string' && messageText.trim()) return messageText;
      }

      if (typeof err.message === 'string' && err.message.trim()) return err.message;
    }

    return '操作失败';
  };

  const getIconNode = (icon?: string) => {
    if (!icon) return <GlobalOutlined />;
    if (icon.startsWith('http://') || icon.startsWith('https://')) {
      return <img src={icon} alt="" style={{ width: 48, height: 48, objectFit: 'contain' }} />;
    }
    return <span style={{ fontSize: 40, lineHeight: 1 }}>{icon}</span>;
  };

  const copyText = async (text: string, successText: string) => {
    try {
      await navigator.clipboard.writeText(text);
      message.success(successText);
    } catch (error) {
      console.error('复制失败:', error);
      message.error('复制失败');
    }
  };

  // 获取外部系统列表
  const fetchSystems = useCallback(async () => {
    try {
      setLoading(true);
      const response = await getUserAccessibleExternalSystems();
      setSystems(response.systems || []);
    } catch (error) {
      console.error('获取外部系统列表失败:', error);
      message.error(`获取${systemLabel}列表失败`);
    } finally {
      setLoading(false);
    }
  }, [message, systemLabel]);

  // 获取系统访问权限
  const getSystemAccess = async (system: AccessibleExternalSystem) => {
    try {
      const access = await getExternalSystemAccess(system.id);

      const result: SystemAccess = {
        system_id: system.id,
        user_id: access.user_id,
        access_token: access.access_token || '',
        expires_at: access.expires_at || new Date(Date.now() + 3600000).toISOString(),
      };
      
      setSystemAccess(result);
      return result;
    } catch (error) {
      console.error('获取系统访问权限失败:', error);
      message.error(getErrorText(error));
      throw error;
    }
  };

  // 处理访问系统
  const handleAccessSystem = async (system: AccessibleExternalSystem) => {
    setSelectedSystem(system);
    setIframeLoading(true);
    setIframeSrc(null);
    setIframeSandbox('allow-scripts allow-same-origin allow-forms allow-popups');
    setIframeAllowFullScreen(true);
    setIframeWidth('100%');
    setIframeBodyHeight('70vh');
    setIntegrationConfigJson(null);
    setSsoUrl(null);
    setSsoCallbackUrl(null);
    setSsoClientId(null);
    setSsoScope(null);

    try {
      if (system.is_active === false) {
        message.warning('系统已禁用，无法访问');
        return;
      }

      const integrationType =
        system.integration_type || (system.system_type === 'api' ? 'api' : system.system_type === 'iframe' ? 'iframe' : 'iframe');

      if ((system.system_type === 'iframe' || system.system_type === 'page') && integrationType !== 'sso' && system.page_url) {
        const access = await getSystemAccess(system);
        const targetUrl = new URL(system.page_url);
        if (access.access_token) targetUrl.searchParams.set('access_token', access.access_token);
        targetUrl.searchParams.set('user_id', access.user_id.toString());

        if (system.system_type === 'page') {
          window.open(targetUrl.toString(), '_blank', 'noopener,noreferrer');
          message.success(`已打开${systemLabel}`);
          return;
        }

        try {
          const config = await getExternalSystemIntegrationConfig(system.id, 'iframe');
          const iframeConfig = config.iframe_config;
          if (iframeConfig) {
            if (iframeConfig.width) setIframeWidth(iframeConfig.width);
            if (iframeConfig.height) setIframeBodyHeight(iframeConfig.height);
            if (typeof iframeConfig.allow_fullscreen === 'boolean') setIframeAllowFullScreen(iframeConfig.allow_fullscreen);
            if (Array.isArray(iframeConfig.sandbox) && iframeConfig.sandbox.length > 0) setIframeSandbox(iframeConfig.sandbox.join(' '));
          }
        } catch (error) {
          console.error('获取外部系统集成配置失败:', error);
        }

        setIframeSrc(targetUrl.toString());
        setAccessModalVisible(true);
      } else if (system.system_type === 'api') {
        const access = await getSystemAccess(system);
        try {
          const config = await getExternalSystemIntegrationConfig(system.id, 'api');
          setIntegrationConfigJson(JSON.stringify(config, null, 2));
        } catch (error) {
          console.error('获取外部系统集成配置失败:', error);
        }

        setIframeBodyHeight('70vh');
        setAccessModalVisible(true);
        if (!access.access_token) message.warning('未获取到访问令牌');
      } else if (integrationType === 'sso') {
        const access = await getSystemAccess(system);
        try {
          const config = await getExternalSystemIntegrationConfig(system.id, 'sso');
          setIntegrationConfigJson(JSON.stringify(config, null, 2));
          setSsoUrl(config.sso_config?.sso_url || null);
          setSsoCallbackUrl(config.sso_config?.callback_url || null);
          setSsoClientId(config.sso_config?.client_id || null);
          setSsoScope(config.sso_config?.scope || null);
          setAccessModalVisible(true);
          if (!config.sso_config?.sso_url) message.warning('SSO 配置不完整：缺少 sso_url');
        } catch (error) {
          console.error('获取外部系统集成配置失败:', error);
          message.error(getErrorText(error));
        }
        if (!access.access_token) message.warning('未获取到访问令牌');
      } else {
        message.warning('系统配置不完整，无法访问');
      }
    } catch (error) {
      console.error('访问系统失败:', error);
      message.error(getErrorText(error));
    } finally {
      setIframeLoading(false);
    }
  };

  // 处理重新加载
  const handleReload = () => {
    fetchSystems();
    message.success('系统列表已刷新');
  };

  // 组件加载时获取系统列表
  useEffect(() => {
    fetchSystems();
  }, [fetchSystems]);

  // 系统类型标签颜色映射
  const getSystemTypeColor = (type: string) => {
    const colorMap = {
      iframe: 'blue',
      page: 'green',
      api: 'orange'
    };
    return colorMap[type as keyof typeof colorMap] || 'default';
  };

  // 系统类型文本映射
  const getSystemTypeText = (type: string) => {
    const textMap = {
      iframe: '内嵌页面',
      page: '独立页面',
      api: 'API接口'
    };
    return textMap[type as keyof typeof textMap] || type;
  };

  return (
    <MainLayout>
      <div style={{ padding: '24px' }}>
        {/* 页面标题和操作区 */}
        <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ margin: 0 }}>{pageTitle}</h1>
          <Space>
            <Tooltip title="刷新系统列表">
              <Button 
                icon={<ReloadOutlined />}
                onClick={handleReload}
                loading={loading}
              >
                刷新
              </Button>
            </Tooltip>
          </Space>
        </div>

        {/* 系统卡片网格 */}
        <Row gutter={[16, 16]}>
          {systems.map((system) => (
            <Col key={system.id} xs={24} sm={12} lg={8} xl={6}>
              <Card
                hoverable
                style={{ 
                  height: '200px',
                  display: 'flex',
                  flexDirection: 'column',
                  opacity: system.is_active === false ? 0.6 : 1
                }}
                actions={[
                  <Tooltip title="访问系统">
                    <Button
                      type="primary"
                      icon={<LoginOutlined />}
                      onClick={() => handleAccessSystem(system)}
                      disabled={system.is_active === false}
                      block
                    >
                      访问
                    </Button>
                  </Tooltip>,
                  ...(isAdmin
                    ? [
                        <Tooltip title="系统配置">
                          <Button icon={<SettingOutlined />} onClick={() => navigate('/settings/external-systems')} block>
                            配置
                          </Button>
                        </Tooltip>
                      ]
                    : [])
                ]}
              >
                <div style={{ textAlign: 'center', marginBottom: 16 }}>
                  <div style={{ fontSize: '48px', marginBottom: 8 }}>
                    {getIconNode(system.icon)}
                  </div>
                  <h3 style={{ margin: '8px 0', fontSize: '16px' }}>{system.name}</h3>
                  <Space>
                    <Tag color={getSystemTypeColor(system.system_type)}>
                      {getSystemTypeText(system.system_type)}
                    </Tag>
                    <Tag color={system.is_active === false ? 'red' : 'green'}>{system.is_active === false ? '禁用' : '启用'}</Tag>
                  </Space>
                </div>
                
                {system.description && (
                  <p style={{ 
                    color: '#666', 
                    fontSize: '12px', 
                    textAlign: 'center',
                    margin: '8px 0',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical'
                  }}>
                    {system.description}
                  </p>
                )}
                
                <div style={{ 
                  textAlign: 'center', 
                  fontSize: '12px', 
                  color: '#999',
                  marginTop: 'auto'
                }}>
                  系统ID: {system.id}
                </div>
              </Card>
            </Col>
          ))}
        </Row>

        {/* 空状态 */}
        {systems.length === 0 && (
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <Empty
              description={`暂无${systemLabel}`}
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              <Button type="primary" onClick={handleReload} loading={loading}>
                重新加载
              </Button>
            </Empty>
          </div>
        )}

        {/* 系统访问模态框 */}
        <Modal
          title={`访问 ${selectedSystem?.name}`}
          open={accessModalVisible}
          onCancel={() => {
            setAccessModalVisible(false);
            setIframeSrc(null);
            setIntegrationConfigJson(null);
            setSsoUrl(null);
            setSsoCallbackUrl(null);
            setSsoClientId(null);
            setSsoScope(null);
          }}
          footer={null}
          width="90%"
          style={{ top: 20 }}
          styles={{ body: { height: iframeBodyHeight, padding: 0 } }}
        >
          {selectedSystem && selectedSystem.system_type === 'iframe' && iframeSrc && (
            <div style={{ position: 'relative', height: '100%' }}>
              {iframeLoading && (
                <div style={{ 
                  position: 'absolute', 
                  top: '50%', 
                  left: '50%', 
                  transform: 'translate(-50%, -50%)',
                  zIndex: 1000
                }}>
                  <Spin size="large" tip={`正在加载${systemLabel}...`} />
                </div>
              )}
              
              <iframe
                src={iframeSrc}
                style={{ 
                  width: iframeWidth, 
                  height: '100%', 
                  border: 'none',
                  display: iframeLoading ? 'none' : 'block'
                }}
                onLoad={() => setIframeLoading(false)}
                onError={() => {
                  setIframeLoading(false);
                  message.error(`${systemLabel}加载失败`);
                }}
                sandbox={iframeSandbox}
                allowFullScreen={iframeAllowFullScreen}
                title={selectedSystem.name}
              />
            </div>
          )}
          
          {selectedSystem && selectedSystem.system_type === 'api' && (
            <div style={{ padding: '24px' }}>
              <h3>API系统配置信息</h3>
              <p><strong>系统名称:</strong> {selectedSystem.name}</p>
              <p><strong>API地址:</strong> {selectedSystem.endpoint_url}</p>
              <p><strong>访问令牌:</strong> {systemAccess?.access_token || '-'}</p>
              <p><strong>过期时间:</strong> {systemAccess?.expires_at ? new Date(systemAccess.expires_at).toLocaleString() : '未知'}</p>

              <Space style={{ marginTop: 8 }} wrap>
                <Button
                  onClick={() => systemAccess?.access_token && copyText(systemAccess.access_token, '令牌已复制')}
                  disabled={!systemAccess?.access_token}
                >
                  复制令牌
                </Button>
                <Button
                  onClick={() => selectedSystem.endpoint_url && copyText(selectedSystem.endpoint_url, 'API 地址已复制')}
                  disabled={!selectedSystem.endpoint_url}
                >
                  复制 API 地址
                </Button>
              </Space>
              
              <div style={{ marginTop: 16 }}>
                <h4>集成配置</h4>
                <pre style={{ 
                  background: '#f5f5f5', 
                  padding: '12px', 
                  borderRadius: '4px',
                  overflow: 'auto'
                }}>
                  {integrationConfigJson || JSON.stringify(selectedSystem.config || {}, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {selectedSystem && selectedSystem.integration_type === 'sso' && (
            <div style={{ padding: '24px' }}>
              <h3>SSO 集成信息</h3>
              <p><strong>系统名称:</strong> {selectedSystem.name}</p>
              <p><strong>SSO 地址:</strong> {ssoUrl || '-'}</p>
              <p><strong>回调地址:</strong> {ssoCallbackUrl || '-'}</p>
              <p><strong>Client ID:</strong> {ssoClientId || '-'}</p>
              <p><strong>Scope:</strong> {ssoScope || '-'}</p>

              <Space style={{ marginTop: 8 }} wrap>
                <Button
                  type="primary"
                  disabled={!ssoUrl}
                  onClick={() => {
                    if (!ssoUrl) return;
                    const targetUrl = new URL(ssoUrl);
                    if (systemAccess?.access_token) targetUrl.searchParams.set('access_token', systemAccess.access_token);
                    if (systemAccess?.user_id) targetUrl.searchParams.set('user_id', systemAccess.user_id.toString());
                    window.open(targetUrl.toString(), '_blank', 'noopener,noreferrer');
                  }}
                >
                  打开 SSO 登录
                </Button>
                {ssoUrl ? <Button onClick={() => copyText(ssoUrl, 'SSO 地址已复制')}>复制 SSO 地址</Button> : null}
              </Space>

              {integrationConfigJson && (
                <div style={{ marginTop: 16 }}>
                  <h4>集成配置</h4>
                  <pre
                    style={{
                      background: '#f5f5f5',
                      padding: '12px',
                      borderRadius: '4px',
                      overflow: 'auto'
                    }}
                  >
                    {integrationConfigJson}
                  </pre>
                </div>
              )}
            </div>
          )}
        </Modal>
      </div>
    </MainLayout>
  );
};

export default ExternalSystems;
