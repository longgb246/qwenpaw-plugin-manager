/**
 * 插件管理器 — 前端
 * 在 QwenPaw Console 侧边栏显示插件管理页面
 *
 * 使用 window.QwenPaw.registerRoutes() + React 组件
 */
(function() {
    'use strict';

    var PLUGIN_ID = 'plugin-manager';
    var API_BASE = 'http://127.0.0.1:39149';
    var React, antd, msg, Table, Button, Tag, Space, Modal, Input, Card, Typography, message;

    // ── 等待宿主模块就绪 ───────────────────────────────
    function waitForHost(cb, retries) {
        retries = retries || 0;
        var w = window.QwenPaw;
        if (w && w.host && w.registerRoutes) {
            React = w.host.React;
            antd = w.host.antd;
            msg = antd.message;
            Table = antd.Table;
            Button = antd.Button;
            Tag = antd.Tag;
            Space = antd.Space;
            Modal = antd.Modal;
            Input = antd.Input;
            Card = antd.Card;
            Typography = antd.Typography;
            message = antd.message;
            cb();
        } else if (retries < 100) {
            setTimeout(function() { waitForHost(cb, retries + 1); }, 200);
        } else {
            console.error('[PluginManager] QwenPaw host 未就绪');
        }
    }

    // ── API 调用 ───────────────────────────────────────
    function api(path, options, ok, err) {
        fetch(API_BASE + path, {
            method: (options && options.method) || 'GET',
            headers: { 'Content-Type': 'application/json' },
            body: options && options.body ? JSON.stringify(options.body) : undefined
        })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.error) { message.error(data.error); if (err) err(data.error); }
                else { ok(data); }
            })
            .catch(function(e) { message.error('API 错误: ' + e.message); if (err) err(e); });
    }

    // ── React 组件：插件管理页面 ────────────────────────
    var PluginManagerPage = function() {
        var _React = React;
        var useState = _React.useState;
        var useEffect = _React.useEffect;
        var createElement = _React.createElement;

        var plugins = useState([]);
        var setPlugins = plugins[1];
        var loading = useState(true);
        var setLoading = loading[1];
        var installUrl = useState('');
        var setInstallUrl = installUrl[1];
        var installing = useState(false);
        var setInstalling = installing[1];
        var detailModal = useState(null);
        var setDetailModal = detailModal[1];

        function loadPlugins() {
            setLoading(true);
            api('/list', null, function(data) {
                setPlugins(data);
                setLoading(false);
            }, function() { setLoading(false); });
        }

        useEffect(function() { loadPlugins(); }, []);

        function doInstall() {
            var url = installUrl[0].trim();
            if (!url) { message.warning('请输入插件地址'); return; }
            setInstalling(true);
            api('/install', { method: 'POST', body: { source: url } }, function(data) {
                message.success(data.message);
                setInstallUrl('');
                setInstalling(false);
                loadPlugins();
            }, function() { setInstalling(false); });
        }

        function doToggle(id, enabled) {
            api('/toggle', { method: 'POST', body: { plugin_id: id, enabled: enabled } }, function(data) {
                message.success(data.message);
                loadPlugins();
            });
        }

        function doUninstall(id, name) {
            Modal.confirm({
                title: '确认卸载',
                content: '确定要卸载插件「' + name + '」吗？此操作不可撤销。',
                okText: '卸载',
                okType: 'danger',
                cancelText: '取消',
                onOk: function() {
                    api('/uninstall', { method: 'POST', body: { plugin_id: id } }, function(data) {
                        message.success(data.message);
                        loadPlugins();
                    });
                }
            });
        }

        function showDetail(id) {
            api('/info/' + id, null, function(data) {
                setDetailModal(data);
            });
        }

        var columns = [
            { title: '插件', dataIndex: 'name', key: 'name', width: 200,
              render: function(text, record) {
                  return createElement(Space, { direction: 'vertical', size: 0 },
                      createElement(Typography.Text, { strong: true }, text),
                      createElement(Typography.Text, { type: 'secondary', style: { fontSize: 12 } },
                          'v' + record.version)
                  );
              }
            },
            { title: '状态', dataIndex: 'enabled', key: 'status', width: 100,
              render: function(enabled, record) {
                  if (record.missing) return createElement(Tag, { color: 'orange' }, '文件丢失');
                  return enabled
                      ? createElement(Tag, { color: 'green' }, '已启用')
                      : createElement(Tag, { color: 'red' }, '已禁用');
              }
            },
            { title: '描述', dataIndex: 'description', key: 'desc', ellipsis: true },
            { title: '操作', key: 'actions', width: 280,
              render: function(_, record) {
                  var isSelf = record.id === PLUGIN_ID;
                  var actions = [];

                  if (!isSelf && !record.missing) {
                      actions.push(
                          createElement(Button, {
                              key: 'toggle', size: 'small',
                              type: record.enabled ? 'default' : 'primary',
                              onClick: function() { doToggle(record.id, !record.enabled); }
                          }, record.enabled ? '禁用' : '启用')
                      );
                  }

                  actions.push(
                      createElement(Button, {
                          key: 'detail', size: 'small',
                          onClick: function() { showDetail(record.id); }
                      }, '详情')
                  );

                  if (!isSelf) {
                      actions.push(
                          createElement(Button, {
                              key: 'uninstall', size: 'small', danger: true,
                              onClick: function() { doUninstall(record.id, record.name); }
                          }, '卸载')
                      );
                  }

                  return createElement(Space, null, actions);
              }
            }
        ];

        // Details modal
        var detailContent = null;
        if (detailModal[0]) {
            var d = detailModal[0];
            var fileItems = (d.files || []).slice(0, 30).map(function(f) {
                return createElement('div', { key: f, style: { fontFamily: 'monospace', fontSize: 12 } }, f);
            });
            detailContent = createElement(Modal, {
                open: true,
                title: d.name + ' v' + d.version,
                footer: createElement(Button, { onClick: function() { setDetailModal(null); } }, '关闭'),
                onCancel: function() { setDetailModal(null); },
                width: 600
            },
                createElement(Typography.Paragraph, null, d.description),
                createElement(Space, { direction: 'vertical', style: { width: '100%' } },
                    createElement(Typography.Text, { type: 'secondary' },
                        '作者: ' + d.author + ' | 许可: ' + d.license),
                    createElement(Typography.Text, { type: 'secondary' },
                        '入口: ' + (d.entry && d.entry.backend || '无') + ' / ' + (d.entry && d.entry.frontend || '无')),
                    createElement(Tag, { color: d.enabled ? 'green' : 'red' }, d.enabled ? '启用' : '禁用'),
                    createElement(Typography.Text, { strong: true, style: { marginTop: 12, display: 'block' } },
                        '文件列表 (' + (d.files ? d.files.length : 0) + ' 个):'),
                    createElement('div', { style: { background: '#fafafa', borderRadius: 6, padding: 12,
                        maxHeight: 200, overflow: 'auto', fontSize: 12, fontFamily: 'monospace' } },
                        fileItems.length ? fileItems : createElement(Typography.Text, { type: 'secondary' }, '无文件'))
                )
            );
        }

        return createElement('div', { style: { padding: 24 } },
            // Header
            createElement(Typography.Title, { level: 4 }, '🔌 插件管理'),
            createElement(Typography.Paragraph, { type: 'secondary' },
                '管理 QwenPaw/CoPaw 插件 — 安装、卸载、启用、禁用（操作后需重启生效）'),

            // Install section
            createElement(Card, { size: 'small', style: { marginBottom: 16 } },
                createElement(Space, { style: { width: '100%' } },
                    createElement(Input, {
                        placeholder: 'GitHub ZIP URL 或本地路径',
                        value: installUrl[0],
                        onChange: function(e) { setInstallUrl(e.target? e.target.value : ''); },
                        style: { flex: 1 },
                        onPressEnter: doInstall
                    }),
                    createElement(Button, {
                        type: 'primary',
                        loading: installing[0],
                        onClick: doInstall
                    }, '安装')
                )
            ),

            // Plugin table
            createElement(Table, {
                dataSource: plugins[0],
                columns: columns,
                rowKey: 'id',
                loading: loading[0],
                pagination: false,
                size: 'middle',
                locale: { emptyText: '暂无插件，使用上方输入框安装新插件' }
            }),

            detailContent
        );
    };

    // ── 注册 ───────────────────────────────────────────
    waitForHost(function() {
        console.log('[PluginManager] 注册侧边栏路由...');
        window.QwenPaw.registerRoutes(PLUGIN_ID, [{
            path: '/plugin-manager',
            label: '插件管理',
            icon: '🔌',
            priority: 90,
            component: PluginManagerPage
        }]);
        console.log('[PluginManager] ✅ 插件管理器已注册');
    });

})();
