"""Post-generation verification for daily trending report.

Checks structural integrity of the generated markdown to catch LLM truncation
before commit/push. Lightweight: structure only, no content quality check.

Exit code 0 = pass, 1 = fail (caller should retry or abort).
"""
import re
import sys
from pathlib import Path


def verify_report(report_path: Path) -> list[str]:
    """Return list of failure reasons (empty = pass)."""
    failures = []

    if not report_path.exists():
        return [f"报告文件不存在: {report_path}"]

    content = report_path.read_text(encoding="utf-8").strip()
    if not content:
        return [f"报告文件为空: {report_path}"]

    # 1. 趋势观察段必须非空（最常见截断：只剩标题）
    trend_match = re.search(r"^## 趋势观察\s*$", content, re.MULTILINE)
    if not trend_match:
        failures.append("缺少 '## 趋势观察' 小节")
    else:
        after = content[trend_match.end():].strip()
        if not after or len(after) < 50:
            failures.append(
                f"'## 趋势观察' 后内容过短 ({len(after)} 字符)，疑似截断"
            )

    # 2. 代码块必须配对闭合（```mermaid 等）
    fence_count = content.count("```")
    if fence_count % 2 != 0:
        failures.append(f"代码块未闭合（``` 出现 {fence_count} 次，应为偶数）")

    # 3. 每个 repo 小节必须有 summary（> 开头行）
    repo_headers = re.findall(r"^### \[.+\]", content, re.MULTILINE)
    if not repo_headers:
        failures.append("未找到任何项目小节 '### [repo]'")
    else:
        # 抽样检查：至少 80% 的 repo 小节有 summary
        sections = re.split(r"^### \[.+\]", content, flags=re.MULTILINE)[1:]
        missing_summary = sum(
            1 for s in sections if not re.search(r"^>\s+\S", s, re.MULTILINE)
        )
        ratio = missing_summary / len(sections) if sections else 1
        if ratio > 0.2:
            failures.append(
                f"{missing_summary}/{len(sections)} 个项目小节缺 summary，占比 {ratio:.0%}"
            )

    # 4. 结尾必须收束（最后非空行以句号/问号/感叹号/代码块/分割线收尾）
    last_line = ""
    for line in reversed(content.splitlines()):
        if line.strip():
            last_line = line.strip()
            break
    if last_line and not re.search(r"[。？！\.\?!]$", last_line) and last_line != "---":
        failures.append(f"结尾未收束，疑似半句话: ...{last_line[-40:]}")

    return failures


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: python -m scripts.verify_report <report.md>", file=sys.stderr)
        return 1

    report_path = Path(sys.argv[1])
    failures = verify_report(report_path)

    if not failures:
        print(f"[verify] OK: {report_path.name} 结构校验通过")
        return 0

    print(f"[verify] FAIL: {report_path.name} 校验失败:", file=sys.stderr)
    for f in failures:
        print(f"  - {f}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
