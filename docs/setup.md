# 配置与运维指南

## 配置项

| 类型 | 名称 | 必需 | 用途 |
| --- | --- | --- | --- |
| Repository secret | LLM_API_KEY | 深度分析必需 | 模型服务 API key。仅在分析步骤注入进程环境。 |
| Repository variable | LLM_MODEL | 深度分析必需 | 供应商实际可用的模型 ID 或 endpoint ID，不填臆测值。 |
| Repository variable | LLM_BASE_URL | 可选 | 默认 `https://api.openai.com/v1`。可替换为可信 OpenAI Chat Completions 兼容 API。 |
| Repository variable | LLM_JSON_MODE | 可选 | 默认 `true`。供应商不支持 `response_format` 时可设 `false`；程序仍会解析和校验 JSON。 |
| Actions built-in | GITHUB_TOKEN | 自动提供 | 读取公开上游、提交当前仓库研究文件。无需设置 PAT。 |

本工具没有配置任何真实模型凭证；不会假定你已有 API 额度。API 必须兼容 `/chat/completions`、messages、max_tokens，JSON 模式可关闭。若模型仅支持其他协议，需修改适配层后使用，不宣称兼容所有模型。

## 手动运行

1. 设置 Secret 和 Variables。
2. Actions → Daily Agent Research → Run workflow。
3. **auto**：有 key 和 model 时 full，否则 collect。
4. **full**：缺 key/model 就失败，不降级。
5. **collect**：只整理来源清单，不调用模型，不消耗深度分析去重项。
6. 检查绿色状态以及新提交。当天 collect 可升级为 full；已有 full 日报不重复调用模型。

## 时间与权限

每日 `15 23 * * *` 按默认 UTC 运行，转换为北京时间次日 07:15。日报按 Asia/Shanghai 本地日期命名。排队或平台繁忙可能延迟，不承诺精确秒级执行。

工作流声明 `contents: write`，提交范围固定为 `research/` 和 `data/`。主分支保护规则、组织策略或 Actions 禁用可能仍阻止推送。程序不绕过保护、不自动调宽权限；应由仓库所有者按实际政策配置。

若工作流因修改 `.github/workflows` 的授权范围被阻止，需要在 GitHub 重新授权相关范围或由所有者手动添加工作流；不能用长期明文 token 绕过。

## 首版收集范围

- 配置的 4 个 GitHub 仓库 releases：每仓库最多读取 5 页，每页 20 条。
- arXiv 标题查询：最多 30 条，按 submittedDate 排序，只保留发布时间在回看窗口内的论文。
- 默认回看 72 小时，去重通过来源 URL 的稳定哈希。
- 短期没有版本更新的仓库不会仅因 commit 活跃而入选。
- 不包含全网新闻、博客、所有新仓库、论文 PDF 全文，也不支持自动发现所有热门项目；可后续添加明确来源适配器。

## 源码与输出

版本 tag 解析到 commit，再读取该 commit 的 Git tree 与 README / 最多 4 个相关源码文件。每文件最多 180KB，提供给模型的编号片段最多 9000 字符；源码选择按路径关键字启发式，未保证命中该版本每个变更点。JSON 中保留输入片段方便复核。

不安装、运行上游仓库代码，不执行模型给出的 shell。原始资料不是指令。模型无法取得系统工具，仅接受证据包并输出受校验的纯文本 JSON。

## 失败诊断

- **未配置模型**：auto 明确降级 collect。要做深度分析必须配置 key 和 model。
- **HTTP 401/403**：检查模型凭证、可用模型与供应商权限；GitHub API 可能存在额度/仓库策略问题。
- **HTTP 429/5xx**：有界重试，最多 3 次，等待不超过 30 秒/次；不能保证成功。
- **网络超时**：读取请求可重试；模型 POST 网络超时不重放，避免无谓重复费用。
- **ValueError**：可能是无效配置、JSON 格式、章节/引用缺失、过短正文、未完成响应等。程序只打印安全错误类型，不输出服务端响应或 key。
- **来源部分失败**：日报和 evidence JSON 标明覆盖不全。全部失败则退出，不声称“没有新技术”。
- **git push 被拒绝**：查看分支保护规则。仅尝试 rebase，无 force push。
- **长期没有自动运行**：检查 Actions 是否启用、默认分支 workflow、定时停用状态。GitHub 公开仓库长期无活动可能自动停用 schedule。

## 成本与维护

每日默认最多 2 个模型分析请求，每个请求输出最多 7000 tokens；输入含发布说明及有界源码片段。重试可能增加请求计费；总费用取决于实际模型、上下文长度和定价。供应商侧设置支出上限，必要时降低 max_daily_topics / source_excerpt_chars / max_output_tokens。

公开仓库任何有写权限的维护者可以修改 workflow 并影响 Secrets 使用。只授予可信维护者写权限，审查 workflow 变更，必要时使用受保护环境和批准规则。证据片段、报告正文与 token usage 会公开提交；不提交任何 key、cookie 或个人/企业内部资料。

## 参考

- https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- https://platform.openai.com/docs/api-reference/chat
