# 独立安装与依赖

## 已验证平台与前提

本候选安装器只接受Windows x64、Python3.12、Node24。最终渲染需已安装并可在当前桌面会话启动的Microsoft PowerPoint16.0。Codex需支持本地Agent Skills。首次安装需要官方软件源网络连接与目标目录写权限；无需管理员权限或模型API密钥。

这是软件依赖安装，不上传论文。安装器不安装系统Python/Node/Codex/Office、不改PATH/注册表/执行策略、不全局pip/npm安装。所有包/浏览器在Skill的`.runtime`或显式`ACADEMIC_PPT_RUNTIME`。用户预先准备系统软件；安装或许可Office不属于本包操作。

## ZIP安装

1. 核对发布方SHA-256并解压。顶层`academic-paper-to-ppt`就是完整Skill和仓库。
2. 在解压的Skill根目录执行下面命令，将`AcademicWork`改成自己的工作项目。复制前验证全部清单哈希；同名覆盖、向下载目录递归安装及目录链接逃逸均阻断。只读预览加`--dry-run`。
3. `--check`只检查。审查并授权后，最后的安装命令创建非system-site-packages的venv，按哈希锁安装Python包，按package-lock用`npm ci --ignore-scripts`安装Node包，并下载Playwright Chromium。
4. `doctor`检查后，在工作项目打开Codex，输入`$academic-paper-to-ppt`并提供PDF。启动器自动选择隔离Python。没有`py`启动器时使用Python3.12的完整可执行文件路径。

```powershell
$paperProject = Join-Path $HOME 'AcademicWork'
py -3.12 scripts/install_skill.py --project "$paperProject"
$paperSkill = Join-Path $paperProject '.agents/skills/academic-paper-to-ppt'
py -3.12 "$paperSkill/scripts/setup.py" --check
# 审查并授权下载后：
py -3.12 "$paperSkill/scripts/setup.py" --install --allow-downloads
Set-Location -LiteralPath $paperProject
py -3.12 "$paperSkill/scripts/studio.py" doctor
```

无全局npm时安装器从官方registry取得固定npm12.2.1并验证SHA-512，仍只放在本地runtime。可显式`--npm-cli <已审查的npm-cli.js>`。`--resolve`仅供维护者更新候选锁，本版用户应使用随包完整锁；不静默更新上游版本。

GitHub仓库目标：[hee902/academic-paper-to-ppt](https://github.com/hee902/academic-paper-to-ppt)。当前仅准备私有仓库和Release草稿；需要该仓库访问权限。向Codex内置`$skill-installer`提供下列明确参数（只替换工作项目路径）：

```text
--repo hee902/academic-paper-to-ppt --ref v0.1.0 --path . --name academic-paper-to-ppt --dest "<工作项目>/.agents/skills" --method download
```

根目录就是Skill，不是另一个skills子目录。`--name`不能省略，否则`.`会被当作名称而拒绝；`--dest`明确采用项目安装，避免官方安装器默认写入用户级目录。安装后仍需运行本包setup依赖检查。

私有仓库必须先有授权认证：官方下载助手读取已有`GITHUB_TOKEN`或`GH_TOKEN`环境配置；Git模式可使用已有Git凭据。这里不要求创建新Token，也不把任何凭据写入命令示例、源文件、日志或remote URL。浏览器登录与命令行认证相互独立，未配置安装器认证时用登录后的浏览器下载ZIP，再运行本地安装器。

官方安装器的根路径/命名/复制逻辑已经过本地离线适配测试。远程仓库、标签、草稿附件和下载安装的真实结果应以维护者本轮检查记录为准，不能把离线测试改称实时GitHub通过。私有准备阶段不代表已公开发布。

## 数据、缓存与输出

`ACADEMIC_PPT_RUNTIME`指定独立依赖/浏览器缓存；`ACADEMIC_PPT_WORKSPACE`指定工作区（默认当前目录）。生产输出仅在工作区`work/<时间戳-ID>`，完成运行不可原地改写。venv、node_modules、浏览器、日志、工作输出不能加入发布ZIP或Git提交。

## OCR与可选组件

默认Docling native是模型免下载的文本层解析，不是布局/表格/OCR模型。本包不分发或自动安装MinerU/模型。扫描件将明确阻断。若用户已另行审查、授权并准备本地MinerU basic与模型，可设置`ACADEMIC_PPT_ENABLE_MINERU=1`和`ACADEMIC_PPT_MINERU=<本地可执行文件绝对路径>`。这条外部适配本候选未重新验收，历史表格列保真失败仍有效；不得加remote或隐式下载模型。

Guizang为非必要对照且不随包分发；academic-pptx因历史许可冲突继续禁用；JetBrains外部工具不是本包必需项。Baoyu和K-Dense所需MIT资源已在third_party附许可证，仅本地设计/审读/palette能力，付费生成器和其他合集功能不执行。

## Office与错误处理

无PowerPoint时setup/doctor显示缺失，qa不能最终通过；没有LibreOffice自动替代。COM沙箱限制使用平台权限机制运行同一Python导出脚本，不改变系统设置。每次导出要求全新目录，不接受旧PDF。安装/下载/导出失败保留日志，修复后重跑，不标成功。

安装本地依赖不等于科学成稿。Codex必须读取原页、填写真实审阅、实际查看每页PNG再finalize；机器不自动批准论文。跨机字体、现场投影、真人计时和未验证研究类型需要单独验收。

## 可重复技术自检

依赖配置后，在工作项目运行以下命令。测试只生成自有合成PDF，不下载论文、不批准真实科学内容：

```powershell
$paperRuntime = Join-Path $paperSkill '.runtime'
# 若设置了ACADEMIC_PPT_RUNTIME，请改用该目录。
& "$paperRuntime/venv/Scripts/python.exe" -B -m unittest discover -s "$paperSkill/tests" -p 'test_*.py' -v
```

`-B`避免生成包内字节缓存。自检验证清单中每个文件，并对仅含发行清单文件的临时副本执行发布审计；不扫描或删除已安装runtime及用户生产输出。自行修改已列文件会令完整性检查失败，宜保留修改并另用新解压副本检查。
