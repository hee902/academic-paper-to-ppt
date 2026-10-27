# A–F 数据契约与故障处理

正式化新增字段见[研究类型规范](research-routing.md)，实际质量规则见[质量规则](quality-standards.md)。新run带 `workflowContract: generalized-editorial-v1`；B分类审核、C叙事与路由、F双预览哈希为增量门禁。旧完成运行不迁移、不回填批准。以下来源和哈希契约保留。

本文件对应 `scripts/studio_core` 的实际实现；不是自动批准模板。JSON 必须为 UTF-8、有限数值，不使用 NaN/Infinity。SHA-256 使用文件原始字节计算，修改输入后必须重新审读并更新关联哈希。

## 运行与 A

`run.json` 保存 `version/id/settings/source/status/stages/events`。PDF 快照为 `input/paper.pdf`。每次 `run` 独立目录，默认配置在创建时快照；之后修改项目默认值不会悄悄改变旧任务。

`A/paper.json` 包含 `sourceSha256/pageCount/pages/blocks/parser/allPagesExtracted/limitations/emptyPages`。每页包含 `page/text/textSource/image/imageSha256/width/height`；页码从 1 开始，指 PDF 实际页面，印刷页码可另写 location。Docling 的 `blocks` 含原始 provenance；native 阅读顺序不保证正确。扫描件必须通过本地 OCR 后再逐页核验。

`A/parse-report.json.paperSha256` 绑定 canonical JSON。`A/assets.json` 由 `crop` 生成，键为稳定 ID，值包含 `page/bbox/path/sha256/sourcePageImageSha256`。bbox 为左上原点 `[left,top,right,bottom]`，均在 0–1。不能用外部图片伪造论文来源。

## B/analysis.json

以下为字段示例，尖括号和示例数字不能当成论文事实。`paperTitle` 必须照录论文原始标题，中文演讲标题放 C。

```json
{
  "sourceSha256": "<input/paper.pdf SHA-256>",
  "paperSha256": "<A/paper.json SHA-256>",
  "paperTitle": "<原始论文标题>",
  "sections": {
    "background": {"status": "reported", "claimIds": ["CBackground"]},
    "question": {"status": "reported", "claimIds": ["CQuestion"]},
    "methods": {"status": "reported", "claimIds": ["CMethods"]},
    "model": {"status": "not-reported", "reason": "<原文未使用模型的具体依据>", "claimIds": []},
    "sample": {"status": "reported", "claimIds": ["CSample"]},
    "results": {"status": "reported", "claimIds": ["CResult"]},
    "conclusions": {"status": "reported", "claimIds": ["CConclusion"]},
    "limitations": {"status": "reported", "claimIds": ["CLimit"]}
  },
  "evidence": [
    {"id": "EText", "page": 4, "kind": "text", "location": "Results / paragraph 2", "quote": "<本页中实际存在的原文>"},
    {"id": "ETable", "page": 5, "kind": "table", "location": "Table 2", "assetId": "Table2"}
  ],
  "claims": [
    {"id": "CResult", "type": "observation", "text": "<来源支持的结论>", "evidenceIds": ["EText"],
     "quantities": [{"value": 12.0, "unit": "<真实单位/统计定义>", "evidenceId": "EText"}]}
  ]
}
```

示例 sections 中所有 claimIds 必须在实际 claims 中完整定义；不是可直接提交的研究分析。

- ID 以英文字母开头，后续仅字母、数字、下划线、短横线，且在本数组内唯一。
- `evidence.kind` 为 text/table/formula/figure。text 必须有本页实际引文，至少四个归一化字符；Unicode NFKC、空白与大小写归一化仅用于匹配，不能改变数值含义。原文 OCR 错误不能靠修改 canonical JSON 掩盖。
- 每项 claim 的 `type` 为 observation/interpretation/hypothesis，至少一个已核验证据。假设必须明确是解释或提议，不能变成实证结论。
- `quantities` 每项一个十进制/科学记数数值，正负号保留，单位独立。样本量、年份、阈值、p 值等只要出现在主张或幻灯片中也需来源；没有数值则空数组。数值锚点检查不能代替单位、比较方向及统计含义审读。
- 八个 sections 都必需。reported 要有 claimIds；not-reported 要有具体 reason，不能把“没报告”改为“没做”。

## B/review.json

运行 `review-template --kind science` 后填实际审阅，再另存为 `B/review.json`：

```json
{
  "reviewer": "Codex — <实际审阅范围>",
  "analysisSha256": "<B/analysis.json SHA-256>",
  "pages": [{"page": 1, "imageSha256": "<该页图像 SHA-256>", "status": "reviewed", "notes": "<本页阅读内容、顺序和疑点>"}],
  "evidence": [{"id": "EText", "status": "verified", "rationale": "<原文及上下文核对理由>"}],
  "claims": [{"id": "CResult", "status": "supported", "rationale": "<推断范围核对理由>"}]
}
```

pages 必须覆盖每一页且不重复。每项证据和主张均需对应审阅。table/formula/figure 的证据审阅额外需要 `originalVisualChecked: true`、`assetSha256`；table/formula 还需 `fidelity: "verified"`。从图表读取数值的主张审阅需要 `quantitiesChecked: true`。uncertain/rejected/failed/pending 均阻断；不能修改状态取代真正核验。

通过后输出 `B/paper-structure.json`、`B/evidence-report.json`、`B/evidence-report.md`。后者列出主张、类型、页码、引文/裁图位置、数值、单位及审阅理由。报告状态 `passed-contract-and-recorded-review` 表示契约和记录通过，不表示独立科学认证。

## C/plan.json 与 review

```json
{
  "analysisSha256": "<B/analysis.json SHA-256>",
  "title": "<演讲标题>",
  "language": "zh-CN",
  "slides": [{
    "id": "result-main", "role": "result", "layout": "finding",
    "title": "<有证据支持的结论式标题>",
    "body": ["<简短且有证据的陈述>"],
    "notes": "<实际讲述内容、证据解释、局限与转场>",
    "seconds": 75, "claimIds": ["CResult"], "assetId": "Table2"
  }]
}
```

slides 数量必须等于 run.settings.slideCount。layout 仅 cover/statement/method/chart/finding/references；不是任意 CSS 名。body 最多四条。finding 必须 assetId；chart 必须 chart 对象，当前支持：

```json
{"type":"bar", "labels":["<真实组名>"], "values":[12.0], "unit":"<真实单位>", "uncertainty":"not-reported"}
```

图值和单位必须出自本页 claim 的 quantities，标签/比较方向由叙事审阅核对。只允许单系列、最多八个类别的简单柱图；存在误差线、置信区间、多系列或不支持的类型时，使用核验原图的 finding，不得省略误差。不要用柱图替代论文中本来不适合柱图的数据。

`C/review.json`：`reviewer`、`planSha256`、`slides:[{id,status:"supported",notesChecked:true,rationale}]`。所有标题、正文及讲稿数字必须在本页 claim 中有 quantities。讲述时间必须正整数且总和不超过分配。production 要求至少使用总时间 80%、至少四类版式、不连续三页相同、末页 role=conclusion。计划时间不是实测演讲。

## D/E/F 与最终快照

D 的 `deck-spec.json` 是编译产物，包含 theme/font/objects/notes/seconds 和分析、计划、两次审阅的 SHA-256。不能手工修改后仅改哈希放行。D 的 HTML 和生产 PPTX 从同一规格生成，HTML 只提供预检，不能冒充 PowerPoint 的像素布局。

E 保存 PPTX、build-manifest、native-check；正文是原生文本、简单图表是原生 chart，图片必须保持原始裁图字节。F 每次创建全新 `render/<ID>`，实际 PowerPoint 导出 PDF 和 1600×900 PNG。检查页数、非空白、哈希，再生成待审视觉模板。

`F/visual-review.json` 需要 `reviewer/qaSha256/pptxSha256/slides`。每页包含 `id/imageSha256/status:"passed"/checks/notes`，checks 必须含 layout、legibility、scientific-figures、sources、notes；notes 记录实际检查和发现。未查看的页面保持 pending。

只有 finalize 创建 deliverables，保存 PPTX/PDF、两类报告、讲稿、spec、原图、审计 JSON、重建源及清单。重建在有本项目锁定依赖的环境中执行 `node rebuild.cjs`，不是无依赖独立软件包。新运行用于修订；完成后的 `status` 还会核验交付文件哈希。

## 统计定义扩展

新建原生“均值±离散量”摘要显式提供`B.statisticalDefinitions`，并在`B/review.json.statisticalDefinitions`按ID给出`status: verified`和实质`rationale`；旧完成运行不回填。

定义字段：`id/claimId/kind/unit/comparison/quantityIndices`，kind为`mean-sd`、`mean-se`或`reported-unknown`；两个quantityIndices指向该claim原报告的均值与离散量，单位完全相同。`basis.method`为：

- `explicit-source-definition`：`evidenceId`必须为当前claim已引用、实际写明SD/SE的原文证据；支持s.d./s.e.。
- `checked-csv-recalculation`：仅核验样本SD。提供当前运行内`path/sha256/sourceUrl/sourceMember/rows/differenceColumn/afterColumn/beforeColumn/rationale`及定义的`reportedDecimals`。独立逐行验证差值等于after−before，再验证均值和ddof=1 SD的舍入值；不推导CI、不执行作者代码、不自动认可列的科学语义。
- `unresolved-definition`：仅`reported-unknown`，必须给出原因，保持定义未知。

C在`visual.reportedStatistic.definitionId`引用已核验定义；`visual.text.summaryValue`原样显示原报告数值与±，`summaryDefinition`明确SD/SE/未定义以及对象与比较。该字段不得把离散量称为CI。`STATISTIC_*`门禁阻断来源/复算/单位/摘要不符。元数据为显式扩展，机器不会自动定位所有自由文本±；Skill必须在新增此类摘要时使用契约并审阅其余正文/Notes。

时间扩展：`deliveryTiming.perSlideBuffers`可选，格式为`{页ID: 非负整数秒}`。一旦使用必须覆盖且只包含所有当前页ID，和等于`readingAndTransitionSeconds`；否则`TRANSITION_ALLOCATION`。原声稿`seconds`与缓冲分开统计，不修改默认分钟或冒充试讲。

## 主要阻断码

| 阶段 | 代码示例 | 处理 |
|---|---|---|
| 输入/A | INPUT_PDF / PDF_UNREADABLE / UNREADABLE_PAGES / MINERU_TRUNCATED | 核实本地 PDF；检查解析日志，不能接受残缺页 |
| 来源 | SOURCE_CHANGED / STALE_PARSE / SOURCE_IMAGE_CHANGED | 新运行或重新解析并完整重审，不能只改哈希 |
| B | QUOTE_MISMATCH / QUANTITY_MISMATCH / FIDELITY_BLOCK / UNSUPPORTED_CLAIM | 回原文/原图修复证据或删去不成立的主张 |
| 审阅 | STALE_SCIENTIFIC_REVIEW / STALE_NARRATIVE_REVIEW / PAGE_NOT_REVIEWED | 对当前内容真实重审 |
| C | UNSUPPORTED_SLIDE_NUMBER / CHART_UNSUPPORTED / TIMING / REPEATED_LAYOUT | 修正叙事、使用原图或重新分配时间 |
| D/E | LAYOUT_BLOCKED / STALE_DESIGN / PPTX_CHART_FIDELITY / PPTX_IMAGE_FIDELITY | 修订布局/构建实现，不能降低科学标准 |
| F | COMMAND_FAILED / PDF_EXPORT / RENDER_MISSING / VISUAL_BLOCK | 查真实导出日志、修复后重新导出并逐页查看 |
| 完成 | IMMUTABLE_RUN / DELIVERY_CHANGED | 保留旧快照，创建新运行 |

异常日志保留在对应 A–F 文件夹；退出 2 表示阻断，退出 3 表示需要 Codex 继续工作。不要将它们包装成“全部成功”。
