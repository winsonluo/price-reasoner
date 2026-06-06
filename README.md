# Price Reasoner

AI-powered commodity price trend reasoning engine — price stages decomposition, multi-factor attribution, competitor analysis, and monitoring alerts.

## Features

| Module | Description |
|--------|-------------|
| **价格归因分析** | 识别价格阶段（上涨/平台/下跌），归因于宏观/供需/事件因素 |
| **竞品分析** | AI 推荐竞品，构建比价矩阵，生成差异化策略建议 |
| **真实数据源** | 爬取京东/天猫/淘宝/1688 商品价格历史（`scrape` 命令） |
| **飞书文档输出** | 报告一键发布到飞书云文档 |
| **价格监控** | Cron 定时抓取 + 微信告警（变化超阈值自动推送） |

## Setup

```bash
pip install -e .
cp .env.example .env
# Edit .env: add ANTHROPIC_API_KEY
```

Additional dependencies for scraping:
```bash
pip install requests beautifulsoup4
```

## Usage

### 1. 价格归因分析（Mock 数据）

```bash
price-reasoner analyze --commodity 原油 --start 2023-01-01 --end 2024-01-01 --output report.md
```

### 2. 竞品分析

```bash
# AI 自动推荐竞品
price-reasoner competitor -c "Dior S8U 墨镜"

# 指定竞品
price-reasoner competitor -c "Dior S8U" --competitors "Gucci,Prada,Oakley"

# 查看已知竞品列表
price-reasoner competitor -c "Dior S8U" --list
```

### 3. 真实数据抓取（京东/天猫/淘宝/1688）

```bash
# 抓取单个商品价格历史
price-reasoner scrape --url "https://item.jd.com/100012043456.html" -d 90 -o prices.json

# 抓取并直接发布到飞书
price-reasoner scrape --url "https://detail.tmall.com/item.htm?id=..." --feishu
```

支持的平台自动识别：京东（jd.com）、天猫（tmall.com）、淘宝（taobao.com）、1688（1688.com）。

### 4. 输出到飞书文档

```python
from price_reasoner.feishu_output import FeishuReportGenerator
from price_reasoner.competitor_report import CompetitorReportGenerator

gen = FeishuReportGenerator()
doc_url = gen.save_competitor_report(report, title="Dior S8U 竞品分析")
print(doc_url)  # https://ycns9yqtukgu.feishu.cn/docx/xxx
```

### 5. 价格监控（Cron + 微信告警）

将监控 URL 写入配置：
```bash
echo '["https://item.jd.com/100012043456.html", "https://detail.tmall.com/item.htm?id=..."]' \
  > ~/.hermes/price_monitor_urls.json
```

每天 9:00 自动运行，检查价格变化 > 5% 则推送微信通知。

手动触发：
```bash
python ~/.hermes/scripts/price_monitor.py watch --urls "url1,url2" --threshold 5.0
```

## Architecture

```
price_reasoner/
├── models.py              # 数据模型（PriceStage, Factor, CompetitorData...）
├── ai_reasoner.py        # AI 因果推理引擎（阶段识别 + 归因）
├── report.py              # Markdown 报告生成器
├── config.py              # 配置（API Key、目录）
├── cli.py                 # Typer CLI（analyze/competitor/scrape/version）
├── competitor_analyzer.py # 竞品分析 AI 模块
├── competitor_report.py   # 竞品报告 Markdown 生成器
├── feishu_output.py       # 飞书文档输出
└── data_sources/
    ├── __init__.py
    ├── mock.py            # Mock 数据源（开发/测试用）
    ├── competitor_mock.py # 竞品 Mock 数据源
    └── ecommerce.py      # 真实电商爬虫数据源（京东/天猫/1688）
```

## 核心概念

**价格阶段（PriceStage）**
- `rise` / `plateau` / `fall` — 价格上涨、平台、下跌
- 每个阶段有：起止日期、价格区间、成交量、宏观背景

**归因（Factor）**
- `macro` — 宏观因素（利率、CPI、汇率）
- `supply_demand` — 供需驱动（库存、产能）
- `event` — 事件驱动（政策、灾害、展会）

**竞品矩阵（CompetitiveMatrix）**
- 多维度（价格/功能/渠道/品牌力）评分对比
- 识别 gap：你的产品在哪些维度落后/领先

## Environment Variables

```env
ANTHROPIC_API_KEY=sk-ant-...     # Anthropic API Key（AI 推理用）
CLAUDE_MODEL=claude-sonnet-4-20250514  # 模型名称（默认）
OUTPUT_DIR=./output               # 报告输出目录
DATA_DIR=./data                   # 数据缓存目录
```

## Development

```bash
# 运行测试
pytest tests/ -v

# 代码检查
python -m py_compile price_reasoner/
```
