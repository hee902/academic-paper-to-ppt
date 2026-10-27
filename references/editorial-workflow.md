> 此文保留历史编辑配方的兼容字段。新论文以 [研究类型与通用路由](research-routing.md) 为准；历史特定案例的方法/估值配方不进入新来源路由。

# Modern Scientific Editorial 接入

唯一主控与入口不变。根`design-system.md`负责视觉规范，`config/academic-theme.json`负责主题、字体、字阶，`scripts/studio_core/editorial.py`负责注册布局。所有生成仍经同一PptxGenJS与F门禁；不直接改D/E跳过C审阅。

## 选型

| layout | 适用任务与需要的visual.text字段 |
|---|---|
| cover | 论文封面；titleLead/titleMain/english/researchQuestion/authors/affiliations/journal |
| background | 背景论证路径；lead/nature/health/value/boundary |
| question | 研究缺口与新证据；question/previous/new/contribution |
| sample | 试点和正式样本角色；pilotLabel/pilotN/pilotMeaning/formalLabel/park/parkN/parkRole/city/cityN/cityRole/warning |
| measurement | 结果与协变量；outcome/transform/interpretation/exposure/exercise/controls |
| method | 不等宽功能区；pilotLabel/pilotN/pilotMeaning/formalLabel/park/city/measurement/covariates/regression/scopes/averaging/averageMeaning/delta/deltaMeaning/valuation/warning |
| models | 拟合与模型平均的不同角色；scopes/fit/average/boundary；没有数据则不造AIC排名 |
| comparison | 实测与模型情景；premise/observedLabel/observed/counterfactualLabel/counterfactual/aggregate/warning |
| figure | 完整原始图像；assetId及figureGuide |
| finding | 原图+有明确来源的区间摘要；assetId、meanLabel/figureGuide/axisTitle/warning；可选legendPoint |
| interval | 全宽简单点估计比较；context/interpretation/warning；chart沿用B数量单位门禁，不能补造区间 |
| valuation | 经验部分与外部输入；equation/empirical/external/boundary；条件值须明示条件与未核实来源 |
| limitations | 样本/模型/外推边界；limit0/limit1/limit2/future；不要写成三张卡片 |
| references | 两个主要来源及复核边界；reference0/reference1/availability/disclosure，长文献适当增页 |
| conclusion | 受证据约束的结论；takehome/takeaway0/takeaway1/lastline |

每页可选eyebrow作为编辑分类标识，不能加入未审阅的科学数据。visual.text.sourceLabel可给出已核验的作者/年份，引用相应元数据主张；未提供则用当前论文标题，不在通用脚本写死作者。布局选择服从内容，不要求每份汇报用齐所有页类。超出密度/图形能力时先考虑拆页或保留原图，不填假数据适配模板。当前中文14页实际覆盖除figure外的14类；figure额外版式尚待单独PowerPoint视觉验收。

## 计划与统计摘要

`C/plan.json.designSystem`为`modern-scientific-editorial`。每页仍有id/layout/role/title/body/claimIds/seconds/notes，另有`visual.text`字符串字典。其全部科学数字与标题、正文、讲稿一道核验；C审阅绑定整个计划哈希，不能漏审附加版式文字。

`visual.intervalSummary`包含claimId、quantityRoles（point/se/level/lower/upper对应B claim.quantities的索引）、axis和unit。B对应数量须有同名role。编译器读取原文数值，不重新计算CI。轴包括零和全部端点，原图必须同时保留。代码的角色/几何检查不能替代对统计口径和单位的实质判断。

`figure/finding`使用A/assets.json的来源图件；若提取原始PDF内嵌图像，保留页码、原页哈希、原始图像SHA及提取方式，B证据与审阅须关联该资产。不能仅把图像存在当作已核验。

## 执行

`studio.py branch <parent> --purpose production`复用已审阅来源，创建独立任务；随后在新任务审读扩展内容、写B/C并检查。新PDF仍用run。执行`design → build → qa`，实际逐页看PowerPoint图像，写图像绑定的F审阅，最后`finalize`。`resume`可编排相同步骤，但不是独立语义模型。

标准输出保留可编辑文字/简单chart/形状、原始图像、完整备注、逐页高清预览、证据与审阅、设计规范与可重建规格。重建仍依赖本项目已锁定环境；不宣称跨机器自动保真。中文真实14页验收不自动等于英文、任意论文、任意统计图表或会场投影已验收。
