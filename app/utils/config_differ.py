"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: config_differ.py
@DateTime: 2025/07/30
@Docs: 配置差异分析器 - 提供智能的网络设备配置差异对比功能
"""

import re
from dataclasses import dataclass
from difflib import SequenceMatcher, unified_diff
from enum import Enum
from typing import Any

from app.utils.logger import logger


class DiffType(Enum):
    """差异类型枚举"""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    MOVED = "moved"
    UNCHANGED = "unchanged"


class ConfigSection(Enum):
    """配置段落类型"""

    INTERFACE = "interface"
    ROUTING = "routing"
    ACCESS_LIST = "access-list"
    VLAN = "vlan"
    SYSTEM = "system"
    SECURITY = "security"
    QOS = "qos"
    OTHER = "other"


@dataclass
class DiffLine:
    """差异行数据结构"""

    line_number: int
    content: str
    diff_type: DiffType
    section: ConfigSection = ConfigSection.OTHER
    indent_level: int = 0
    is_comment: bool = False
    original_line_number: int | None = None  # 原始行号（用于moved类型）


@dataclass
class ConfigDiffResult:
    """配置差异结果"""

    config1_info: dict[str, Any]
    config2_info: dict[str, Any]
    diff_lines: list[DiffLine]
    summary: dict[str, Any]
    sections_changed: list[ConfigSection]
    unified_diff: str
    side_by_side_diff: list[dict[str, Any]]


class NetworkConfigDiffer:
    """网络设备配置差异分析器"""

    def __init__(self):
        # 网络设备配置段落识别模式
        self.section_patterns = {
            ConfigSection.INTERFACE: [
                r"^interface\s+",
                r"^\s+ip\s+address\s+",
                r"^\s+switchport\s+",
                r"^\s+(no\s+)?shutdown",
                r"^\s+description\s+",
            ],
            ConfigSection.ROUTING: [
                r"^router\s+",
                r"^\s+network\s+",
                r"^\s+neighbor\s+",
                r"^ip\s+route\s+",
                r"^\s+redistribute\s+",
            ],
            ConfigSection.ACCESS_LIST: [r"^(ip\s+)?access-list\s+", r"^\s+(permit|deny)\s+"],
            ConfigSection.VLAN: [r"^vlan\s+", r"^\s+name\s+", r"^vtp\s+"],
            ConfigSection.SYSTEM: [r"^hostname\s+", r"^domain\s+", r"^clock\s+", r"^banner\s+", r"^version\s+"],
            ConfigSection.SECURITY: [r"^username\s+", r"^enable\s+secret\s+", r"^crypto\s+", r"^aaa\s+"],
            ConfigSection.QOS: [r"^class-map\s+", r"^policy-map\s+", r"^\s+bandwidth\s+", r"^\s+priority\s+"],
        }

        # 忽略的差异模式（如时间戳、动态信息等）
        self.ignore_patterns = [
            r"!\s*Last\s+configuration\s+change",  # 配置变更时间
            r"!\s*NVRAM\s+config\s+last\s+updated",  # NVRAM更新时间
            r"!\s*Time:\s+",  # 时间戳
            r"!\s*.*uptime\s+is\s+",  # 设备运行时间
            r"!\s*.*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}",  # 日期时间
        ]

    def identify_section(self, line: str) -> ConfigSection:
        """识别配置行属于哪个段落"""
        line_stripped = line.strip()

        for section, patterns in self.section_patterns.items():
            for pattern in patterns:
                if re.match(pattern, line_stripped, re.IGNORECASE):
                    return section

        return ConfigSection.OTHER

    def get_indent_level(self, line: str) -> int:
        """获取配置行的缩进级别"""
        stripped = line.lstrip()
        if not stripped:
            return 0
        return len(line) - len(stripped)

    def is_comment_line(self, line: str) -> bool:
        """判断是否为注释行"""
        stripped = line.strip()
        return stripped.startswith("!") or stripped.startswith("#")

    def should_ignore_line(self, line: str) -> bool:
        """判断是否应该忽略某行差异"""
        for pattern in self.ignore_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False

    def normalize_config_line(self, line: str) -> str:
        """标准化配置行（移除多余空格、统一格式）"""
        # 移除行尾空格
        line = line.rstrip()

        # 统一多个空格为单个空格（保留缩进）
        if line.strip():
            leading_spaces = len(line) - len(line.lstrip())
            content = re.sub(r"\s+", " ", line.strip())
            line = " " * leading_spaces + content

        return line

    def create_side_by_side_diff(self, lines1: list[str], lines2: list[str]) -> list[dict[str, Any]]:
        """创建并排差异视图"""
        matcher = SequenceMatcher(None, lines1, lines2)
        side_by_side = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                # 相同的行
                for i in range(i1, i2):
                    side_by_side.append(
                        {
                            "left_line_no": i + 1,
                            "right_line_no": j1 + (i - i1) + 1,
                            "left_content": lines1[i],
                            "right_content": lines2[j1 + (i - i1)],
                            "type": "equal",
                        }
                    )
            elif tag == "delete":
                # 左边有，右边没有（删除）
                for i in range(i1, i2):
                    side_by_side.append(
                        {
                            "left_line_no": i + 1,
                            "right_line_no": None,
                            "left_content": lines1[i],
                            "right_content": "",
                            "type": "delete",
                        }
                    )
            elif tag == "insert":
                # 右边有，左边没有（插入）
                for j in range(j1, j2):
                    side_by_side.append(
                        {
                            "left_line_no": None,
                            "right_line_no": j + 1,
                            "left_content": "",
                            "right_content": lines2[j],
                            "type": "insert",
                        }
                    )
            elif tag == "replace":
                # 替换（修改）
                max_lines = max(i2 - i1, j2 - j1)
                for k in range(max_lines):
                    left_line = lines1[i1 + k] if i1 + k < i2 else ""
                    right_line = lines2[j1 + k] if j1 + k < j2 else ""
                    left_line_no = (i1 + k + 1) if i1 + k < i2 else None
                    right_line_no = (j1 + k + 1) if j1 + k < j2 else None

                    side_by_side.append(
                        {
                            "left_line_no": left_line_no,
                            "right_line_no": right_line_no,
                            "left_content": left_line,
                            "right_content": right_line,
                            "type": "replace",
                        }
                    )

        return side_by_side

    def analyze_config_differences(
        self,
        config1_content: str,
        config2_content: str,
        config1_info: dict[str, Any],
        config2_info: dict[str, Any],
        ignore_whitespace: bool = True,
        ignore_comments: bool = False,
        context_lines: int = 3,
    ) -> ConfigDiffResult:
        """分析两个配置之间的差异

        Args:
            config1_content: 第一个配置内容
            config2_content: 第二个配置内容
            config1_info: 第一个配置的元信息
            config2_info: 第二个配置的元信息
            ignore_whitespace: 是否忽略空白字符差异
            ignore_comments: 是否忽略注释行差异
            context_lines: 上下文行数

        Returns:
            配置差异结果
        """
        logger.info("开始分析配置差异")

        # 预处理配置内容
        lines1 = config1_content.splitlines()
        lines2 = config2_content.splitlines()

        if ignore_whitespace:
            lines1 = [self.normalize_config_line(line) for line in lines1]
            lines2 = [self.normalize_config_line(line) for line in lines2]

        # 过滤掉需要忽略的行
        if ignore_comments:
            lines1 = [line for line in lines1 if not self.is_comment_line(line)]
            lines2 = [line for line in lines2 if not self.is_comment_line(line)]

        # 过滤掉时间戳等动态信息
        lines1 = [line for line in lines1 if not self.should_ignore_line(line)]
        lines2 = [line for line in lines2 if not self.should_ignore_line(line)]

        # 创建差异分析
        differ = SequenceMatcher(None, lines1, lines2)
        diff_lines = []
        sections_changed = set()

        # 分析差异
        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            if tag == "equal":
                continue
            elif tag == "delete":
                # 删除的行
                for i in range(i1, i2):
                    line = lines1[i]
                    section = self.identify_section(line)
                    sections_changed.add(section)

                    diff_lines.append(
                        DiffLine(
                            line_number=i + 1,
                            content=line,
                            diff_type=DiffType.REMOVED,
                            section=section,
                            indent_level=self.get_indent_level(line),
                            is_comment=self.is_comment_line(line),
                        )
                    )
            elif tag == "insert":
                # 插入的行
                for j in range(j1, j2):
                    line = lines2[j]
                    section = self.identify_section(line)
                    sections_changed.add(section)

                    diff_lines.append(
                        DiffLine(
                            line_number=j + 1,
                            content=line,
                            diff_type=DiffType.ADDED,
                            section=section,
                            indent_level=self.get_indent_level(line),
                            is_comment=self.is_comment_line(line),
                        )
                    )
            elif tag == "replace":
                # 修改的行
                for i in range(i1, i2):
                    line = lines1[i]
                    section = self.identify_section(line)
                    sections_changed.add(section)

                    diff_lines.append(
                        DiffLine(
                            line_number=i + 1,
                            content=line,
                            diff_type=DiffType.REMOVED,
                            section=section,
                            indent_level=self.get_indent_level(line),
                            is_comment=self.is_comment_line(line),
                        )
                    )

                for j in range(j1, j2):
                    line = lines2[j]
                    section = self.identify_section(line)
                    sections_changed.add(section)

                    diff_lines.append(
                        DiffLine(
                            line_number=j + 1,
                            content=line,
                            diff_type=DiffType.ADDED,
                            section=section,
                            indent_level=self.get_indent_level(line),
                            is_comment=self.is_comment_line(line),
                        )
                    )

        # 生成统一差异格式
        unified_diff_lines = list(
            unified_diff(
                lines1,
                lines2,
                fromfile=f"Config {config1_info.get('id', 'A')}",
                tofile=f"Config {config2_info.get('id', 'B')}",
                n=context_lines,
                lineterm="",
            )
        )
        unified_diff_text = "\n".join(unified_diff_lines)

        # 创建并排差异视图
        side_by_side_diff = self.create_side_by_side_diff(lines1, lines2)

        # 统计信息
        added_count = sum(1 for line in diff_lines if line.diff_type == DiffType.ADDED)
        removed_count = sum(1 for line in diff_lines if line.diff_type == DiffType.REMOVED)
        modified_count = min(added_count, removed_count)  # 近似计算修改行数

        # 按段落统计差异
        section_stats = {}
        for section in ConfigSection:
            section_lines = [line for line in diff_lines if line.section == section]
            if section_lines:
                section_stats[section.value] = {
                    "added": sum(1 for line in section_lines if line.diff_type == DiffType.ADDED),
                    "removed": sum(1 for line in section_lines if line.diff_type == DiffType.REMOVED),
                    "total": len(section_lines),
                }

        summary = {
            "total_differences": len(diff_lines),
            "lines_added": added_count,
            "lines_removed": removed_count,
            "lines_modified": modified_count,
            "sections_affected": len(sections_changed),
            "section_statistics": section_stats,
            "similarity_ratio": differ.ratio(),
            "is_identical": len(diff_lines) == 0,
        }

        logger.info(f"配置差异分析完成，共发现 {len(diff_lines)} 行差异，相似度: {differ.ratio():.2%}")

        return ConfigDiffResult(
            config1_info=config1_info,
            config2_info=config2_info,
            diff_lines=diff_lines,
            summary=summary,
            sections_changed=list(sections_changed),
            unified_diff=unified_diff_text,
            side_by_side_diff=side_by_side_diff,
        )

    def export_diff_to_html(self, diff_result: ConfigDiffResult) -> str:
        """将差异结果导出为HTML格式"""
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>配置差异对比报告</title>
    <style>
        body {{ font-family: 'Courier New', monospace; margin: 20px; background-color: #f5f5f5; }}
        .header {{ background: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .summary {{ background: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .diff-container {{ background: white; border-radius: 5px; overflow: hidden; }}
        .diff-line {{ display: flex; }}
        .line-number {{ width: 60px; padding: 2px 8px; background: #f0f0f0; border-right: 1px solid #ddd; text-align: right; }}
        .line-content {{ flex: 1; padding: 2px 8px; white-space: pre; }}
        .added {{ background-color: #d4edda; }}
        .removed {{ background-color: #f8d7da; }}
        .equal {{ background-color: white; }}
        .replace {{ background-color: #fff3cd; }}
        .section-tag {{ display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 10px; margin-left: 10px; }}
        .interface {{ background: #e3f2fd; }}
        .routing {{ background: #f3e5f5; }}
        .system {{ background: #e8f5e8; }}
        .security {{ background: #ffebee; }}
        .other {{ background: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>配置差异对比报告</h1>
        <p><strong>配置A:</strong> {config1_name} (创建时间: {config1_time})</p>
        <p><strong>配置B:</strong> {config2_name} (创建时间: {config2_time})</p>
    </div>

    <div class="summary">
        <h2>差异摘要</h2>
        <p>总差异行数: <strong>{total_diff}</strong></p>
        <p>新增行数: <span style="color: green;"><strong>{added_count}</strong></span></p>
        <p>删除行数: <span style="color: red;"><strong>{removed_count}</strong></span></p>
        <p>相似度: <strong>{similarity:.1%}</strong></p>
        <p>受影响的配置段落: <strong>{sections_count}</strong></p>
    </div>

    <div class="diff-container">
        <h2>详细差异</h2>
        {diff_content}
    </div>
</body>
</html>
"""

        # 生成差异内容HTML
        diff_html_lines = []
        for diff_item in diff_result.side_by_side_diff:
            diff_type = diff_item["type"]
            css_class = {"equal": "equal", "delete": "removed", "insert": "added", "replace": "replace"}.get(
                diff_type, "equal"
            )

            left_no = diff_item.get("left_line_no", "")
            right_no = diff_item.get("right_line_no", "")
            left_content = diff_item.get("left_content", "")
            right_content = diff_item.get("right_content", "")

            if diff_type == "equal":
                diff_html_lines.append(f"""
                    <div class="diff-line {css_class}">
                        <div class="line-number">{left_no}</div>
                        <div class="line-content">{left_content}</div>
                    </div>
                """)
            else:
                if left_content:
                    diff_html_lines.append(f"""
                        <div class="diff-line removed">
                            <div class="line-number">-{left_no}</div>
                            <div class="line-content">{left_content}</div>
                        </div>
                    """)
                if right_content:
                    diff_html_lines.append(f"""
                        <div class="diff-line added">
                            <div class="line-number">+{right_no}</div>
                            <div class="line-content">{right_content}</div>
                        </div>
                    """)

        diff_content = "".join(diff_html_lines)

        return html_template.format(
            config1_name=diff_result.config1_info.get("id", "Config A"),
            config1_time=diff_result.config1_info.get("created_at", "Unknown"),
            config2_name=diff_result.config2_info.get("id", "Config B"),
            config2_time=diff_result.config2_info.get("created_at", "Unknown"),
            total_diff=diff_result.summary["total_differences"],
            added_count=diff_result.summary["lines_added"],
            removed_count=diff_result.summary["lines_removed"],
            similarity=diff_result.summary["similarity_ratio"],
            sections_count=diff_result.summary["sections_affected"],
            diff_content=diff_content,
        )
