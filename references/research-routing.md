# 研究类型、叙事与通用版式

用于新 `generalized-editorial-v1` 运行。七类是审读入口，不是自动认证或固定目录；允许主/次类型组合。Codex依据全文识别，脚本只验证覆盖、来源和审核哈希。

## B：分类与边界

`researchDesign` 包含 `primaryType/secondaryTypes/inferenceScope/rationale/evidenceIds/checks`。类型和检查键见 `config/research-profiles.json`。每项check填 `status: reported/not-reported/not-applicable` 与 `reason`；reported另带当前B的evidenceIds。B审核需 `researchDesignReviewed:true`。未报告不补齐，不适用不能掩盖缺失。

| 类型 | 必审问题及叙事重点 |
|---|---|
| experimental | 分配/对照、实验单位/重复、时点、脱落及不确定性 |
| cross-sectional | 抽样/分母、测量/缺失、混杂/模型、关联边界 |
| structural-equation | 构念/观测量、效度、识别/拟合、路径不确定性 |
| spatial-gis | 单元/投影/尺度、覆盖/分辨率、空间依赖、可变单元 |
| qualitative | 招募/情境、编码/反身性、主题/反例、引文上下文 |
| systematic-review-meta | 检索日期/资格、纳入/偏倚、效应量/汇总、异质性 |
| theoretical-methodological | 问题/假设、推导/命题、验证/反例、适用域 |

推断范围：`descriptive/associational/causal-identification-claimed/predictive/qualitative/evidence-synthesis/theoretical`。作者宣称因果不代表识别成立；审核保留假设与质疑。理论/定性不强制样本统计、P值或估值。地图/SEM/森林图/复杂公式保持原件。

## C：内容驱动路由

`analysisSha256`、`researchDesignSha256` 均绑定当前B文件；`narrative.audience/centralQuestion/rationale` 说明受众、科学问题及排序。详细模型、参考和补充验证留备注或允许的附录，不删除证据。14页只是默认预算。

每页 `layout:auto` + `visual.task`，或直接指定下表通用layout；另填 `layoutRationale`。路由记录在 `C/layout-routing.json`。脚本不自行决定哪项科学结果最重要。

| task | layout | visual.text必需字段 |
|---|---|---|
| process | research-flow | lead, stageA/detailA, stageB/detailB, stageC/detailC, edgeAB, edgeBC, boundary；可选stageD/detailD/edgeCD须成组 |
| study-overview | study-overview | context, materialLabel/material, analysisLabel/analysis, boundary |
| evidence-matrix | evidence-matrix | row1Label/row1Text, row2Label/row2Text；可选第3/4行；boundary |
| argument | argument | lead, premiseLabel/premise, reasoningLabel/reasoning, implication |
| statistical-interval | statistical-interval | estimateLabel, intervalLabel, axisTitle, interpretation, boundary；另需assetId、statisticalInterval |
| original-figure | figure | figureGuide；另需来源绑定assetId |
| simple-comparison | interval | context, interpretation, warning；另需通过数值/单位门禁的简单bar chart |
| cover | cover | journal, titleLead, titleMain, english, researchQuestion, authors, affiliations |
| conclusion | conclusion | takehome, takeaway0, takeaway1, lastline |

可见字串进入 `visual.text` 与同一数值门禁。edge说明真实数据流/处理/科学关系，不暗示未经支持的因果。不同学科自主选择原图、主题证据行、论证、流程、材料说明等；不强制同样目录、图形或结果形式。长方法拆页，不强塞四步。

## 单位安全的区间摘要

`visual.statisticalInterval`：claimId、quantityRoles（point/lower/upper/level及可选se，对应B数量数组索引）、unit、kind（confidence/credible/prediction）、axis（显式上下限）、scale（linear/log）、axisRationale。B quantity.role同名；点/端点/SE同单位，level单位单独为%。不重算端点、不补SE、不混淆百分点/百分比/比值。未定义范围不能写CI。对数轴须正值，全部报告端点可见。摘要保留原件且形状可编辑，不是Excel联动chart。

## 兼容与边界

旧完成运行保留原契约，不回填虚假分类；新branch补充分类审核后继续。引擎保留的历史兼容配方不进入新论文路由。发行包不含历史案例、论文、图件或批准；不能复制其他来源的科学内容。

七类契约测试不等于七类真实论文验收。新学科先全文审读和三页视觉试点，再完整生产。既有失败与许可限制仍有效。
