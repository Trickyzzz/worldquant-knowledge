# worldquant-knowledge

一个用于 NotebookLM 的 WorldQuant 学习资料导出工具。

它会收集 WorldQuant 公开页面和 WorldQuant BRAIN 中低风险、只读的结构化资料，然后输出成分区 Markdown 文件，方便导入 NotebookLM 做检索、总结和学习。

## 你需要准备什么

- Firecrawl API Key 文件：`secrets/firecrawl_apikey.txt`
- WorldQuant BRAIN 已登录 cookie/session 文件：`secrets/worldquant_brain_cookie.txt`
- 可选个人笔记：放到 `my_notes_input/` 下，支持 Markdown 或 txt

你不需要提供 WorldQuant 密码、NotebookLM 账号、Google 账号，也不需要手动整理完整 URL 列表。

## 边界说明

这个项目不是全平台爬虫。它不会导出登录后的课程全文、论坛/社区帖子、其他用户的 alpha、评论或排名细节。

它只做：

- 公开 WorldQuant 页面抓取
- WorldQuant BRAIN operators 导出
- WorldQuant BRAIN datasets 导出
- WorldQuant BRAIN fields 导出
- 本地个人笔记整理

所有 BRAIN 请求都是只读请求，并带有限速与自动退避处理。`secrets/`、`config.yaml`、`raw/`、`notebooklm_sources/` 都不会被 git 提交。

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item config.example.yaml config.yaml
New-Item -ItemType Directory -Force secrets
```

然后放入两个本地密钥文件：

```text
secrets/firecrawl_apikey.txt
secrets/worldquant_brain_cookie.txt
```

## 运行

```powershell
.\.venv\Scripts\python sync.py --all
```

也可以分开运行：

```powershell
.\.venv\Scripts\python sync.py --public
.\.venv\Scripts\python sync.py --brain
.\.venv\Scripts\python sync.py --notes
.\.venv\Scripts\python sync.py --build
```

## 输出

程序会生成：

```text
notebooklm_sources/
  00_index.md
  operators/
  datasets_and_fields/
  alpha_patterns/
  public_articles/
  my_notes/
```

辅助文件：

```text
raw/
crawl_manifest.csv
```

`notebooklm_sources/` 里的 Markdown 文件可以直接导入一个 NotebookLM notebook。

## 默认抓取范围

公开资料默认从这些入口开始：

```text
https://www.worldquant.com/
https://www.worldquant.com/brain/
https://www.worldquant.com/learn2quant/
https://www.worldquant.com/ideas/
https://www.worldquant.com/brain/iqc/
https://www.worldquant.com/brain/iqc-guidelines/
```

BRAIN 默认导出：

```text
operators: true
datasets: true
fields: true
my_alphas: false
simulations: false
courses: false
forum_posts: false
```

## 限流处理

WorldQuant BRAIN 没有公开稳定的接口限流数字。程序会自动处理 `429`：

- 如果平台返回 `Retry-After`，优先按它等待。
- 如果没有 `Retry-After`，使用指数退避。
- 默认最多重试 12 次。
- 默认单次等待最多 15 分钟。

相关配置在 `config.yaml`：

```yaml
max_rate_limit_retries: 12
rate_limit_backoff_seconds: 60
max_rate_limit_sleep_seconds: 900
```

## 导入 NotebookLM

打开 NotebookLM，新建一个 notebook，然后上传 `notebooklm_sources/` 里的 Markdown 文件。

建议导入多个分区文件，而不是合并成一个超大 Markdown。这样 NotebookLM 的检索和引用效果更好。

## 输出真实性规则

最终生成到 `notebooklm_sources/` 的文件不会包含 demo、fixture、sample 或 placeholder 内容。

- `operators/` 和 `datasets_and_fields/` 来自 WorldQuant BRAIN 真实导出的数据。
- `alpha_patterns/` 是从真实导出的 operators、fields、公开文章、本地笔记中派生分类出来的内容。
- 没有真实来源的分区不会生成。例如没有真实抓取公开文章时，不会生成 `public_articles/` 空目录。
- index 文件是程序生成的目录文件，用于帮助 NotebookLM 理解资料结构。

## 个人笔记

把你自己的 `.md` 或 `.txt` 文件放到：

```text
my_notes_input/
```

重新运行：

```powershell
.\.venv\Scripts\python sync.py --notes --build
```

程序会把个人笔记整理到：

```text
notebooklm_sources/my_notes/
```

## 测试

```powershell
.\.venv\Scripts\python -m pytest -q
```

## 维护

- 如果 Firecrawl 抓取范围太大，可以调低 `public_crawl.max_pages`。
- 如果 BRAIN 频繁限流，可以调大 `brain.delay_seconds`。
- 如果 BRAIN 前端内部接口变化，需要更新 `worldquant_knowledge/brain_client.py`。
