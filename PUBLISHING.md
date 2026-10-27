# GitHub私有准备与公开停止条件

2026-10-27授权仅限账户`hee902`下的私有仓库`academic-paper-to-ppt`、源码推送、`v0.1.0`标签和Release草稿。**不得公开仓库，不得正式发布Release。** 下列公开步骤只有再次明确授权后才可执行。

只使用本仓库目录，不上传其父目录或私有验证工作区。先查看LICENSE、THIRD_PARTY_NOTICES、release-validation-report和发行SHA256SUMS。

1. 私有准备：创建空的**Private**仓库，不预填重复README/LICENSE，确认owner为hee902；已有仓库先核对身份、可见性与内容，不覆盖无关工作。
2. 在本仓库目录执行`git init`，先用`git status --short`检查文件列表，再提交。按GitHub提供的真实remote URL连接并推送；本文不虚构地址，也不代替授权。
3. 为审查后的提交创建固定tag `v0.1.0`并推送tag。锁文件和清单纳入Git，依赖目录不纳入。
4. 在GitHub Releases创建**草稿**，选择tag，标题标注首个可移植发行候选。附件仅`academic-paper-to-ppt-skill-v0.1.0.zip`和`SHA256SUMS.txt`；验证报告保留在源码中，不上传论文、测试产物或本地审计。
5. 下载GitHub附件并核对哈希，核对远程提交的全部清单文件和根SKILL.md；确认仓库仍为Private、Release仍为Draft。完成即停止，等待所有者下一次明确授权。GitHub自动源码ZIP与发行ZIP的哈希不同，不要混用。
6. 仓库地址确定后可填写真实链接；README或其他清单文件的任何变化都必须重新生成包清单、重新打包/核对SHA并执行受影响验证，再为该确切提交建立tag。不要在测试包与tag之间悄悄改文档。保留验证日期/范围；新增平台必须补实际测试。

GitHub Code ZIP可按INSTALLATION安装；源码新增/修改清单文件后应重新生成验证候选，推荐固定Release。参见[Codex官方Skills说明](https://developers.openai.com/codex/skills/)和[GitHub官方Release文档](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)。

更新先安装到新项目并验证，不覆盖旧Skill或生产输出。保留旧ZIP和校验值作回退。本包不触碰内部双论文基线。
