# Daily Tech Research · 每日 Agent 技术研究

用一个可维护的仓库持续积累 **AI Agent 技术拆解**，而不是每天堆新闻链接。

- **运行**：GitHub Actions，每天北京时间 **07:15**（UTC 23:15），也可手动触发。
- **范围**：Agent Harness / Runtime、工具调用、上下文与记忆、checkpoint、长任务恢复、工作流与评测。
- **产出**：每天最多 2 个主题，中文拆解 + 原始来源 + 固定版本源码引用 + 证据记录。
- **边界**：首版监控 4 个上游仓库的 releases 和 arXiv 标题检索，不是全网搜索；论文仅摘要级分析。

> **启用深度分析还需配置 LLM_API_KEY 和 LLM_MODEL。** 未配置时定时工作流会明确降级为来源雷达，不会冒充完成技术拆解。模型 API 可能产生费用。

## 从这里开始

1. 仓库 **Settings → Secrets and variables → Actions → Secrets** 新增 **LLM_API_KEY**。不要把真实密钥提交进仓库或粘贴进聊天。
2. 在同页面 **Variables** 新增 **LLM_MODEL**，值必须是你的模型供应商允许调用的实际模型/endpoint ID。
3. 如不使用默认 API，再新增 **LLM_BASE_URL**，例如供应商文档给出的 HTTPS OpenAI-compatible `/v1` 基地址。只填写可信服务地址；公开资料会发给该服务。
4. 打开 **Actions → Daily Agent Research → Run workflow**，选择 **full**，验证一次深度分析与自动提交。
5. 检查运行日志、[研究索引](research/README.md) 与 `data/runs/`。仅“Commit generated documents only”步骤成功才算推送成功。

详细配置、错误处理与成本边界见 [配置与运维指南](docs/setup.md)。系统设计见 [架构说明](docs/architecture.md)。

## 每篇拆解写什么

1. 解决什么问题：实际工程痛点。
2. 核心架构：模块、状态和调用关系。
3. 技术机制与源码：基于本次实际抓到的片段，引用固定 commit；覆盖不全则明确指出。
4. 关键执行流程：步骤、分支、失败边界。
5. 技术取舍：事实与研究者推断分开。
6. 复现建议：供后续验证的实验步骤；自动化程序**不会执行下载的代码或模型生成的命令**。
7. 证据边界：哪些只是摘要、哪些没有读到源码、哪些还需人工核验。

每段要求来源编号，并标注 **事实 / 源码推断 / 设计建议 / 待核验**。程序校验引用存在、章节齐全、长度和输出格式，但这些结构检查**不能证明所有结论正确**。

## 数据流

GitHub releases / arXiv → 时间过滤与排序 → 历史去重 → 最多 2 个选题 → tag 对应源码证据 → 模型中文分析 → 引用与结构校验 → Markdown / JSON → 自动 Git 提交。

默认回看 72 小时，重复发布时间窗口通过状态去重。同一天重复运行幂等跳过；当天 collect 文档可升级为 full 文档。无新候选时如实记录，不用旧内容伪装“最新”。

## 目录

- `.github/workflows/daily-research.yml`：定时与手动运行。
- `.github/workflows/ci.yml`：不接触模型密钥的离线测试。
- `src/research.py`：纯 Python 标准库实现。
- `config/research.json`：仓库列表、关键字、回看窗口与规模限制。
- `research/YYYY/MM/YYYY-MM-DD.md`：日报。
- `data/runs/YYYY-MM-DD.json`：本次证据片段、版本、分析、token usage 与覆盖警告。
- `data/state.json`：已完成深度分析的来源去重状态。
- `tests/`：离线单元测试。

## 本地运行

Python 3.11+，无第三方运行时依赖。在仓库根目录执行：

```bash
python -m unittest discover -s tests -v
python src/research.py --mode collect
# 在本地安全注入环境变量 LLM_API_KEY / LLM_MODEL 后：
python src/research.py --mode full
```

脚本不会自动加载 `.env`；请通过进程环境安全注入。不要把密钥放在命令参数或公共日志中。

## 注意

- cron 使用默认 UTC，`15 23 * * *` 对应北京时间 07:15；Actions 定时可能排队延迟，不是精确时钟。
- 仅默认分支上的 workflow 会定时运行。公开仓库长期无活动可能被 GitHub 停用定时任务。
- GitHub 自动提供工作流 GITHUB_TOKEN，不需要额外创建长期 GitHub PAT；写权限只用于当前仓库研究文件。
- 网络/模型失败或输出校验失败时终止任务，不静默发布不完整拆解，不强推覆盖冲突。
- 模型调用最多 2 个主题/日；HTTP 部分错误有有界重试，仍可能额外计费。请在供应商侧设置预算限额。
- 不使用企业内部资料，不读取个人账号其他仓库；公开提交前仍建议人工复核。

## 官方参考

- [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [GitHub schedule events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
- [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat)
- [arXiv API 用户手册](https://info.arxiv.org/help/api/user-manual.html)

项目原创代码采用 MIT 许可；引用的上游代码和文字保留其原作者权利与原许可，不因本项目 LICENSE 改变。
