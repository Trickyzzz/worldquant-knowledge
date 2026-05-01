# worldquant-knowledge

把 WorldQuant 学习资料整理成可导入 NotebookLM 的本地知识库。

[English README](README.md)

`worldquant-knowledge` 会把 WorldQuant 公开页面和 WorldQuant BRAIN 中只读的参考资料导出为结构清晰的 Markdown 文件。目标是把 operators、datasets、fields、公开文章和你的个人笔记放进同一个 NotebookLM notebook，方便检索、引用和总结。

## 会导出什么

- 通过 Firecrawl 抓取 WorldQuant 公开页面
- WorldQuant BRAIN operators
- WorldQuant BRAIN datasets
- WorldQuant BRAIN fields
- 从真实导出资料派生的 alpha pattern 分类
- 可选：`my_notes_input/` 里的本地笔记

这个项目不会抓取登录后的课程全文、论坛/社区帖子、其他用户的 alpha、评论或排名细节。

## 快速开始

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item config.example.yaml config.yaml
New-Item -ItemType Directory -Force secrets
```

放入你的本地凭证：

```text
secrets/firecrawl_apikey.txt
secrets/worldquant_brain_cookie.txt
```

然后运行：

```powershell
.\.venv\Scripts\python sync.py --all
```

## 输出目录

NotebookLM 可导入资料会生成到：

```text
notebooklm_sources/
  00_index.md
  operators/
  datasets_and_fields/
  alpha_patterns/
  public_articles/
  my_notes/
```

只有存在真实输入的分区才会生成。例如，没有真实抓取公开文章时，不会生成 `public_articles/`；没有本地笔记时，不会生成 `my_notes/`。

原始缓存和抓取记录会单独放在：

```text
raw/
crawl_manifest.csv
```

## 输出真实性规则

最终 Markdown 不会填充 demo、fixture、sample 或 placeholder 内容。

- `operators/` 和 `datasets_and_fields/` 来自真实导出的 BRAIN 数据。
- `alpha_patterns/` 从真实导出的 operators、fields、公开文章和本地笔记中派生。
- index 文件是程序生成的目录文件，用于帮助 NotebookLM 理解资料结构。
- 没有真实来源的空分区会被跳过。

## 常用命令

```powershell
.\.venv\Scripts\python sync.py --all
.\.venv\Scripts\python sync.py --public
.\.venv\Scripts\python sync.py --brain
.\.venv\Scripts\python sync.py --notes
.\.venv\Scripts\python sync.py --build
.\.venv\Scripts\python sync.py --all --incremental
```

如果 `raw/` 里已有缓存，只想重新生成 Markdown，可以用 `--build`。

如果想重复运行时优先复用已有 `raw/` 缓存，可以加 `--incremental`。缺失的缓存仍会正常抓取。

## 配置

复制 `config.example.yaml` 为 `config.yaml` 后按需修改。

几个重要默认值：

```yaml
public_crawl:
  max_pages: 1000
  max_depth: 5

brain:
  delay_seconds: 2
  max_requests_per_run: 500
  max_rate_limit_retries: 12
  rate_limit_backoff_seconds: 60
  max_rate_limit_sleep_seconds: 900
```

`config.yaml`、`secrets/`、`raw/` 和 `notebooklm_sources/` 都会被 git 忽略。

## 限流处理

WorldQuant BRAIN 没有公开稳定的内部接口限流数字。程序收到 `429` 后，会优先使用平台返回的 `Retry-After`；如果没有这个字段，则使用指数退避。默认重试策略偏保守，适合长时间无人值守运行。

## 导入 NotebookLM

新建一个 NotebookLM notebook，然后上传 `notebooklm_sources/` 里的 Markdown 文件。相比合并成一个超大 Markdown，按主题拆分通常更利于检索和引用。

## 测试

```powershell
.\.venv\Scripts\python -m pytest -q
```

## 说明

这个项目面向个人学习工作流。请只导出你有权限访问的资料，并保持保守的请求频率。
