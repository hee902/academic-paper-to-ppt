# Academic Paper to PPT

将完整学术论文转为有证据索引、自然讲稿和实际渲染审阅的可编辑学术汇报。主要设计体系为 **Modern Scientific Editorial**，默认中文、约17分钟、约14页、16:9；按论文内容组织，不套固定目录。

**v0.1.0** 是首个独立稳定发行版本，来自已完成双论文验收的内部V2.2基线，版本号表示首次独立安装包，不代表核心功能降级。实际验证范围、失败修复和未测试项目以有日期的[发行验证报告](release-validation-report.md)及Release验收记录为准；内部两篇验收不能替代新环境测试。

官方仓库：[hee902/academic-paper-to-ppt](https://github.com/hee902/academic-paper-to-ppt)。固定版本从[v0.1.0 Release](https://github.com/hee902/academic-paper-to-ppt/releases/tag/v0.1.0)下载；正式发布的公开附件无需GitHub登录。请同时下载Skill ZIP和SHA256SUMS.txt，并核对SHA-256；GitHub自动生成的Source code ZIP与发行附件不是同一文件。

## 能做什么

- 本地Docling原生PDF解析、全文原页快照、来源SHA和逐项科学证据审核。
- 研究类型驱动的叙事、差异化布局、完整Speaker Notes及时间预算。
- 已许可的Baoyu deck-stage设计预览；PptxGenJS原生文字、形状和适合的简单chart；复杂科研图保留原件。
- Windows PowerPoint实际PDF/高清PNG，百分号/单位/来源/字体/布局筛查与逐页成对视觉审阅。
- 无证据、审核过期、原图改变、导出失败或视觉未完成时阻断交付。

Codex在调用会话中完成科学理解和视觉判断；这是可执行工具与Agent流程，不是脱离Codex的自动论文写作API。两类已验收内部工作流为调查/回归/外部估值和空间物种分布/情景预测；SEM、Meta、定性等仍无完整真实论文验收。工程契约不代表科学领域通用认证。

## 系统要求

已测试目标：Windows 11 x64、Python3.12、Node24、桌面Microsoft PowerPoint16.0、Codex本地Skills。准备可写工作目录、网络用于首次安装软件依赖。字体为Microsoft YaHei/Arial，缺字体需要重新渲染核对。其他Windows/Office版本、macOS/Linux、LibreOffice尚未验证。

Python/Node/Codex/Office由用户预先准备，本包不下载安装这些系统软件。无PowerPoint时可构建PPTX，但不能完成本包的最终PDF/PNG验收。无需付费API密钥，不默认上传论文。

## 安装

完整步骤与授权边界见[INSTALLATION.md](INSTALLATION.md)。从正式Release下载`academic-paper-to-ppt-skill-v0.1.0.zip`和`SHA256SUMS.txt`，核对SHA-256后解压。发行ZIP内的顶层`academic-paper-to-ppt`目录包含完整Skill；维护中的main不代替固定版本。

在解压后包含`SKILL.md`的`academic-paper-to-ppt`目录运行（将项目路径换成自己的目录）：

```powershell
$paperProject = Join-Path $HOME 'AcademicWork'
py -3.12 scripts/install_skill.py --project "$paperProject"
$paperSkill = Join-Path $paperProject '.agents/skills/academic-paper-to-ppt'
py -3.12 "$paperSkill/scripts/setup.py" --check
py -3.12 "$paperSkill/scripts/setup.py" --install --allow-downloads
```

最后一条会下载固定Python/npm依赖和Chromium，只安装到Skill的`.runtime`，不改全局环境。将`AcademicWork`换成自己的工作项目，先审查脚本和说明；不希望下载时只执行`--check`。已有同名Skill拒绝覆盖，先保留旧版本并选择新的测试项目。没有`py`启动器时，使用已安装Python3.12可执行文件的完整路径。

手动方式：将完整`academic-paper-to-ppt`文件夹复制到工作项目`.agents/skills/`，保留SKILL.md、scripts、config、references、third_party及锁文件，再配置运行时。用户级安装须显式使用`--user`，它写入用户的`.agents/skills`；默认不进行用户级安装。[Codex官方说明](https://developers.openai.com/codex/skills/)介绍Skills发现和调用。

也可让`$skill-installer`使用`--repo hee902/academic-paper-to-ppt --ref v0.1.0 --path . --name academic-paper-to-ppt --dest "<工作项目>/.agents/skills" --method download`，然后执行本包依赖检查。`--name`不可省略：根路径`.`不能自动推导合法Skill名。公开下载不要求创建Token；遇到网络或请求额度问题时优先改用正式Release ZIP。只有另行访问私有仓库或需要认证额度时才使用已有授权凭据，不把Token写入命令、README或Git remote。

## 一条使用指令

在安装后的工作项目打开Codex并提供PDF：

> `$academic-paper-to-ppt 使用本次上传的完整论文PDF，制作中文、约17分钟、约14页的16:9正式学术汇报；全文核验证据，按内容选择Modern Scientific Editorial布局，交付可编辑PPTX、实际PowerPoint PDF/逐页高清PNG、完整讲稿和科学/视觉核验报告。`

用户无需写JSON。首次探索新类型可要求三页原型；完整报告允许12–16页/15–20分钟。执行日志和输出在当前工作目录的`work/<时间戳-ID>`，不写到原开发项目。可用环境变量`ACADEMIC_PPT_WORKSPACE`指定另一工作区，`ACADEMIC_PPT_RUNTIME`指定独立运行时目录。

## 编辑能力与科学边界

文字、简单形状/流程及适合的简单chart可编辑；区间摘要为原生形状时没有Excel联动。复杂原图内部不可逐点编辑；原生OMML公式未实现。不能从图片外观反推未知数据，不能删误差或把关联当因果。原论文/图件版权和共享许可由用户在交付或公开前核验，软件MIT许可证不会授权第三方论文内容。

逐页PNG必须实际查看，自动检查不能证明审美、科学结论或现场投影质量。时间是预算，非真人试讲。OCR/表格恢复、跨机器字体、全部研究类型和原始科学模型复现不作保证。详细规则见SKILL.md和references/。

## 常见问题

| 问题 | 处理 |
|---|---|
| Codex找不到Skill | 核对`.agents/skills/academic-paper-to-ppt/SKILL.md`；重新加载/重启Codex；避免同名重复。 |
| Local runtime missing | 用Python3.12运行setup检查/授权本地安装；不要全局pip安装。 |
| Office缺失/COM失败 | 先准备桌面PowerPoint并登录可用会话；沙箱限制走平台权限机制；不更改执行策略。 |
| OCR_NOT_CONFIGURED/UNREADABLE_PAGES | 扫描件需显式配置已有本地OCR，或提供可靠文本层；不静默调用远程服务。 |
| stale/source/quantity/visual阻断 | 回原文修复对应上游并重新审阅/渲染，不改哈希或状态绕过。 |
| npm/浏览器下载失败 | 检查官方包源连通；日志保留在独立runtime；不能拿旧PDF代替本轮导出。 |

## 许可和发布

自有代码/规范采用[MIT](LICENSE)，随包第三方文件按[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)及各自LICENSE。只带必要MIT文件，不带MinerU、Guizang、academic-pptx、Office或论文资源。依赖软件安装后各自许可证仍适用。

正式发行附件只包含Skill ZIP和校验清单。维护者按[PUBLISHING.md](PUBLISHING.md)冻结确切提交、核对完整历史及附件，并在全新项目验证公开安装；任何后续版本或仓库权限变更均需另获所有者授权。稳定发行标签表示软件包的发行状态，不扩大科学、平台和现场演示的实际验证范围。
