# 发行组件与边界

实际路由见config/component-routing.json，固定版本见Python哈希锁及package-lock.json。

- Docling native：模型免下载的PDF文本层与原生对象解析；不认证阅读顺序、表格或OCR。
- Baoyu：third_party/baoyu-design内的MIT设计指导与真实deck-stage.js；Chromium本地预检。可选独立gen-pptx导出探针不随包提供，不能冒充正式生成器。
- K-Dense：MIT科学审读/演示指导与本地palette CLI；不执行付费生成器，不默认安装Matplotlib、Seaborn、Beamer或其他合集工具。
- PptxGenJS：唯一正式生成引擎，原生文字/形状和适合的简单chart；复杂图件保持原件。
- PowerPoint：用户预装的Windows桌面软件，COM真实PDF/PNG导出；缺失时最终验收阻断。LibreOffice及其他平台未验证。
- MinerU：独立可选本地适配，不打包、不自动下载模型；本候选未重新验收，历史表格列保真失败保留。
- Guizang/academic-pptx/JetBrains辅助资产：非本包必要项，不再分发或默认调用；academic-pptx许可冲突不因本包MIT而解决。

当前能力以release-validation-report.md为准。所有第三方指导只是参考，不能授权论文上传、付费服务或更改系统设置。软件和论文许可分开处理。
