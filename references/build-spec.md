# 项目构建规格

## V2 主工作流

新运行一律使用`scripts/studio.py`的B/C契约与D编译器。基础规格为`2.0`，Modern Scientific Editorial规格为`2.1-editorial`；现有`build_deck.cjs`均路由到`studio_native.cjs`，保持单一PptxGenJS生产引擎。

每页包含 `id/layout/title/seconds/notes/citations/objects`，对象为 text/image/chart，带英寸位置与字号。源分析、计划和审阅哈希全部绑定。image 带来源 crop 的 SHA-256，chart 的单系列值/类别/单位来自已核验主张。D 预检、E 原生检查、F 实际渲染均依赖此契约；不得手工修改后绕过上游审阅。

编辑设计另支持rect/line/ellipse原生形状、逐对象字体和单页背景。CI端点摘要由C中的角色映射从B获取明确数值；不是新增Excel chart能力。原生检查对照对象ID、位置、文本、图像字节与裁切，chart仍核对数据和类别。详见[编辑设计工作流](editorial-workflow.md)。正式交付可携带实际逐页PNG、设计规范及原生检查记录；不以HTML预检替代PowerPoint渲染。

数据入口及完整字段见 [数据契约](contracts.md)。使用 `studio.py build <RUN>` 才包含前后校验；直接调用底层构建器不代表学术或视觉验收通过。

## 旧烟雾测试规格（保留兼容）

`scripts/build_deck.cjs <spec.json> <output.pptx>` 需要以下结构。文件路径相对于 spec 文件；字体默认 Microsoft YaHei。每页必须有标题与 notes，正文最多四项。图表和图片可选。该构建器提供可验证起点，不覆盖任意学术排版。

```json
{
  "title": "论文标题",
  "slideCount": 14,
  "durationMinutes": 17,
  "slides": [
    {
      "title": "本页主题或有证据支持的结论",
      "bullets": ["简洁要点"],
      "notes": "实际讲述内容、证据与转场",
      "seconds": 60,
      "sources": ["论文图3，第7页"],
      "chart": {
        "labels": ["组甲", "组乙"],
        "values": [12, 18],
        "unit": "真实测量单位",
        "source": "原始数据文件与位置"
      }
    }
  ]
}
```

示例数值仅说明旧 schema，不得复制为科研事实；实际 slides 数组需符合 slideCount。该旧接口只为保留原安装烟雾测试，不走 V2 证据门禁，不能用于宣称新主控验收。误差线、多系列、复杂图/公式在当前 V2 中保留核验原图；以后扩展原生对象须增加契约和实际测试。notes 必须有实际讲述内容。
