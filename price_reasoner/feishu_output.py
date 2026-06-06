"""
Feishu/Lark Document Output Module.

将分析报告输出为飞书文档。
使用 lark-cli 工具。

依赖：
    ~/.hermes/node/bin/lark-cli 已配置并绑定

用法：
    feishu = FeishuReportGenerator()
    doc_url = feishu.save_competitor_report(report, title="Dior S8U 竞品分析")
    doc_url = feishu.save_price_report(report, title="原油价格归因报告")
"""

import subprocess
import json
import re
from pathlib import Path
from price_reasoner.models import CompetitorReport, AnalysisReport


class FeishuReportGenerator:
    """
    将报告写入飞书文档。

    文档创建在用户个人云文档空间（--as user），
    之后需要用户手动移动到对应文件夹。
    """

    def __init__(self, lark_cli_path: str = "~/.hermes/node/bin/lark-cli"):
        self.lark_cli = Path(lark_cli_path).expanduser()

    def _run(self, args: list[str], input_text: str = None) -> str:
        """执行 lark-cli 命令。"""
        cmd = [str(self.lark_cli)] + args
        result = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.stdout + result.stderr

    def _ensure_user_bind(self):
        """确保已绑定 user-default 身份（允许创建文档到用户空间）。"""
        # 检查当前绑定状态
        status = self._run(["auth", "status"])
        if "user-default" not in status.lower():
            # 需要切换到 user-default（需要 device code 授权）
            # 这里只打日志，实际授权由用户手动完成
            print("[FeishuReportGenerator] WARNING: not bound to user-default. "
                  "Run: lark-cli config bind --source hermes --identity user-default --force")

    def save_competitor_report(
        self,
        report: CompetitorReport,
        title: str = None,
    ) -> str:
        """
        将竞品分析报告写入飞书文档。

        Returns:
            飞书文档 URL
        """
        self._ensure_user_bind()

        if title is None:
            title = f"竞品分析报告：{report.target_commodity}"

        # 生成本地 markdown 文件
        from price_reasoner.competitor_report import CompetitorReportGenerator
        md_gen = CompetitorReportGenerator()
        tmp_path = Path("/tmp/competitor_report.md")
        md_gen.save(report, str(tmp_path))

        # 调用 lark-cli 创建文档（v1 API，--markdown "@file" 必须用 v1）
        output = self._run([
            "docs", "+create",
            "--title", title,
            "--markdown", "@./competitor_report.md",
            "--doc-format", "markdown",
        ], input_text=tmp_path.read_text(encoding="utf-8"))

        # 解析文档 URL
        doc_url = self._extract_doc_url(output)
        return doc_url

    def save_price_report(
        self,
        report: AnalysisReport,
        title: str = None,
    ) -> str:
        """
        将价格归因分析报告写入飞书文档。
        """
        self._ensure_user_bind()

        if title is None:
            title = f"{report.commodity} 价格走势归因报告"

        from price_reasoner.report import ReportGenerator
        md_gen = ReportGenerator()
        tmp_path = Path("/tmp/price_report.md")
        md_gen.save(report, str(tmp_path))

        output = self._run([
            "docs", "+create",
            "--title", title,
            "--markdown", "@./price_report.md",
            "--doc-format", "markdown",
        ], input_text=tmp_path.read_text(encoding="utf-8"))

        return self._extract_doc_url(output)

    def _extract_doc_url(self, output: str) -> str:
        """从 lark-cli 输出中提取文档 URL。"""
        # 尝试解析 JSON
        try:
            data = json.loads(output)
            doc_url = data.get("data", {}).get("document_id") or data.get("document_id")
            if doc_url:
                return f"https://ycns9yqtukgu.feishu.cn/docx/{doc_url}"
        except Exception:
            pass

        # 兜底：正则匹配 feishu.cn/docx/xxx
        match = re.search(r"(https://[^\s]*feishu\.cn/docx/[a-zA-Z0-9]+)", output)
        if match:
            return match.group(1)

        # 返回原始输出供调试
        return output.strip()
