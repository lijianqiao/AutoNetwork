"""TextFSM解析器模块

@Author: li
@Email: lijianqiao2906@live.com
@FileName: textfsm_parser.py
@DateTime: 2025/01/27 10:00:00
@Docs: TextFSM解析器 - 实现网络设备命令输出的标准化、结构化解析
"""

import re
from pathlib import Path
from typing import Any

import textfsm
from loguru import logger

from app.core.exceptions import BusinessException


class TextFSMParser:
    """TextFSM解析器 - 网络设备命令输出标准化解析"""

    def __init__(self):
        """初始化TextFSM解析器"""
        self._ntc_templates_path = self._get_ntc_templates_path()
        self._custom_templates_path = Path("templates/custom")
        self._template_cache: dict[str, textfsm.TextFSM] = {}

        # 确保自定义模板目录存在
        self._custom_templates_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"TextFSM解析器初始化完成，ntc-templates路径: {self._ntc_templates_path}")

    def _get_ntc_templates_path(self) -> Path:
        """获取ntc-templates模板路径

        Returns:
            ntc-templates模板目录路径
        """
        try:
            import ntc_templates

            templates_path = Path(ntc_templates.__file__).parent / "templates"
            if not templates_path.exists():
                raise BusinessException(f"ntc-templates路径不存在: {templates_path}")
            return templates_path
        except ImportError as e:
            raise BusinessException("ntc-templates库未安装") from e
        except Exception as e:
            raise BusinessException(f"获取ntc-templates路径失败: {e}") from e

    async def parse_command_output(
        self, command_output: str, platform: str, command: str, custom_template: str | None = None
    ) -> list[dict[str, Any]]:
        """解析命令输出

        Args:
            command_output: 设备命令输出
            platform: 设备平台标识（如cisco_ios, huawei_vrp等）
            command: 执行的命令
            custom_template: 自定义模板名称（可选）

        Returns:
            解析后的结构化数据列表

        Raises:
            BusinessException: 解析失败时抛出
        """
        try:
            logger.debug(f"开始解析命令输出，平台: {platform}，命令: {command}")

            # 获取解析模板
            template = await self._get_template(platform, command, custom_template)
            if not template:
                logger.warning(f"未找到适用的模板，平台: {platform}，命令: {command}")
                return self._fallback_parse(command_output)

            # 执行解析
            template.Reset()
            parsed_data = template.ParseText(command_output)

            # 转换为字典列表
            if not parsed_data:
                logger.warning(f"解析结果为空，平台: {platform}，命令: {command}")
                return []

            # 获取字段名
            header = template.header
            result = []

            for row in parsed_data:
                if len(row) == len(header):
                    result.append(dict(zip(header, row, strict=False)))
                else:
                    logger.warning(f"数据行长度与头部不匹配: {len(row)} vs {len(header)}")

            logger.debug(f"解析完成，结果数量: {len(result)}")
            return result

        except Exception as e:
            logger.error(f"命令输出解析失败: {e}")
            raise BusinessException(f"命令输出解析失败: {e}") from e

    async def _get_template(
        self, platform: str, command: str, custom_template: str | None = None
    ) -> textfsm.TextFSM | None:
        """获取解析模板

        Args:
            platform: 设备平台标识
            command: 执行的命令
            custom_template: 自定义模板名称

        Returns:
            TextFSM模板对象，未找到时返回None
        """
        try:
            # 优先使用自定义模板
            if custom_template:
                template_key = f"custom_{custom_template}"
                if template_key in self._template_cache:
                    return self._template_cache[template_key]

                custom_file = self._custom_templates_path / f"{custom_template}.textfsm"
                if custom_file.exists():
                    template = self._load_template(custom_file)
                    self._template_cache[template_key] = template
                    return template

            # 使用ntc-templates
            template_file = await self._find_template_file(platform, command)
            if not template_file:
                return None

            template_key = f"ntc_{platform}_{command}"
            if template_key in self._template_cache:
                return self._template_cache[template_key]

            template = self._load_template(template_file)
            self._template_cache[template_key] = template
            return template

        except Exception as e:
            logger.error(f"获取模板失败: {e}")
            return None

    async def _find_template_file(self, platform: str, command: str) -> Path | None:
        """查找模板文件

        Args:
            platform: 设备平台标识
            command: 执行的命令

        Returns:
            模板文件路径，未找到时返回None
        """
        try:
            # 标准化命令名称
            normalized_command = self._normalize_command(command)

            # 可能的模板文件名模式
            patterns = [
                f"{platform}_{normalized_command}.textfsm",
                f"{platform}_{normalized_command.replace('_', ' ')}.textfsm",
                f"{platform}_{normalized_command.replace(' ', '_')}.textfsm",
            ]

            # 在ntc-templates目录中查找
            for pattern in patterns:
                template_file = self._ntc_templates_path / pattern
                if template_file.exists():
                    logger.debug(f"找到模板文件: {template_file}")
                    return template_file

            # 尝试模糊匹配
            return self._fuzzy_find_template(platform, normalized_command)

        except Exception as e:
            logger.error(f"查找模板文件失败: {e}")
            return None

    def _normalize_command(self, command: str) -> str:
        """标准化命令名称

        Args:
            command: 原始命令

        Returns:
            标准化后的命令名称
        """
        # 移除常见的命令前缀和参数
        command = command.lower().strip()

        # 移除常见参数
        command = re.sub(r"\s+\|\s+.*", "", command)  # 移除管道及后续内容
        command = re.sub(r"\s+\d+.*", "", command)  # 移除数字参数
        command = re.sub(r"\s+[a-f0-9:.-]+", "", command)  # 移除IP/MAC地址

        # 标准化空格为下划线
        command = re.sub(r"\s+", "_", command)

        # 移除特殊字符
        command = re.sub(r"[^a-z0-9_]", "", command)

        return command

    def _fuzzy_find_template(self, platform: str, command: str) -> Path | None:
        """模糊查找模板文件

        Args:
            platform: 设备平台标识
            command: 标准化后的命令

        Returns:
            模板文件路径，未找到时返回None
        """
        try:
            # 获取平台相关的所有模板文件
            platform_files = list(self._ntc_templates_path.glob(f"{platform}_*.textfsm"))

            # 按命令关键词匹配
            command_keywords = command.split("_")
            best_match = None
            best_score = 0

            for template_file in platform_files:
                template_name = template_file.stem.lower()
                score = 0

                for keyword in command_keywords:
                    if keyword in template_name:
                        score += len(keyword)

                if score > best_score:
                    best_score = score
                    best_match = template_file

            if best_match and best_score > 0:
                logger.debug(f"模糊匹配找到模板: {best_match}，得分: {best_score}")
                return best_match

            return None

        except Exception as e:
            logger.error(f"模糊查找模板失败: {e}")
            return None

    def _load_template(self, template_file: Path) -> textfsm.TextFSM:
        """加载TextFSM模板

        Args:
            template_file: 模板文件路径

        Returns:
            TextFSM模板对象

        Raises:
            BusinessException: 模板加载失败时抛出
        """
        try:
            with open(template_file, encoding="utf-8") as f:
                template = textfsm.TextFSM(f)
            logger.debug(f"模板加载成功: {template_file}")
            return template
        except Exception as e:
            logger.error(f"模板加载失败: {template_file} - {e}")
            raise BusinessException(f"模板加载失败: {e}") from e

    def _fallback_parse(self, command_output: str) -> list[dict[str, Any]]:
        """回退解析方法

        当没有找到合适的模板时，使用简单的文本处理

        Args:
            command_output: 命令输出

        Returns:
            简单解析的结果
        """
        try:
            lines = command_output.strip().split("\n")
            if not lines:
                return []

            # 简单的行解析
            result = []
            for i, line in enumerate(lines):
                if line.strip():
                    result.append({"line_number": i + 1, "content": line.strip(), "raw_output": True})

            return result

        except Exception as e:
            logger.error(f"回退解析失败: {e}")
            return [{"error": str(e), "raw_output": command_output}]

    async def add_custom_template(
        self, template_name: str, template_content: str, description: str | None = None
    ) -> bool:
        """添加自定义模板

        Args:
            template_name: 模板名称
            template_content: 模板内容
            description: 模板描述

        Returns:
            添加是否成功
        """
        try:
            # 验证模板内容
            try:
                import io

                textfsm.TextFSM(io.StringIO(template_content))
            except Exception as e:
                raise BusinessException(f"模板格式验证失败: {e}") from e

            # 保存模板文件
            template_file = self._custom_templates_path / f"{template_name}.textfsm"
            with open(template_file, "w", encoding="utf-8") as f:
                f.write(template_content)

            # 保存描述文件
            if description:
                desc_file = self._custom_templates_path / f"{template_name}.desc"
                with open(desc_file, "w", encoding="utf-8") as f:
                    f.write(description)

            # 清除缓存
            cache_key = f"custom_{template_name}"
            if cache_key in self._template_cache:
                del self._template_cache[cache_key]

            logger.info(f"自定义模板添加成功: {template_name}")
            return True

        except Exception as e:
            logger.error(f"添加自定义模板失败: {e}")
            raise BusinessException(f"添加自定义模板失败: {e}") from e

    async def list_custom_templates(self) -> list[dict[str, Any]]:
        """列出所有自定义模板

        Returns:
            自定义模板列表
        """
        try:
            templates = []

            for template_file in self._custom_templates_path.glob("*.textfsm"):
                template_name = template_file.stem
                desc_file = self._custom_templates_path / f"{template_name}.desc"

                description = ""
                if desc_file.exists():
                    with open(desc_file, encoding="utf-8") as f:
                        description = f.read().strip()

                templates.append(
                    {
                        "name": template_name,
                        "description": description,
                        "file_path": str(template_file),
                        "created_time": template_file.stat().st_ctime,
                        "modified_time": template_file.stat().st_mtime,
                    }
                )

            return sorted(templates, key=lambda x: x["modified_time"], reverse=True)

        except Exception as e:
            logger.error(f"列出自定义模板失败: {e}")
            raise BusinessException(f"列出自定义模板失败: {e}") from e

    async def delete_custom_template(self, template_name: str) -> bool:
        """删除自定义模板

        Args:
            template_name: 模板名称

        Returns:
            删除是否成功
        """
        try:
            template_file = self._custom_templates_path / f"{template_name}.textfsm"
            desc_file = self._custom_templates_path / f"{template_name}.desc"

            if not template_file.exists():
                raise BusinessException(f"模板不存在: {template_name}")

            # 删除文件
            template_file.unlink()
            if desc_file.exists():
                desc_file.unlink()

            # 清除缓存
            cache_key = f"custom_{template_name}"
            if cache_key in self._template_cache:
                del self._template_cache[cache_key]

            logger.info(f"自定义模板删除成功: {template_name}")
            return True

        except Exception as e:
            logger.error(f"删除自定义模板失败: {e}")
            raise BusinessException(f"删除自定义模板失败: {e}") from e

    def get_stats(self) -> dict[str, Any]:
        """获取解析器统计信息

        Returns:
            统计信息字典
        """
        try:
            custom_templates_count = len(list(self._custom_templates_path.glob("*.textfsm")))
            ntc_templates_count = len(list(self._ntc_templates_path.glob("*.textfsm")))

            return {
                "ntc_templates_path": str(self._ntc_templates_path),
                "custom_templates_path": str(self._custom_templates_path),
                "ntc_templates_count": ntc_templates_count,
                "custom_templates_count": custom_templates_count,
                "cached_templates_count": len(self._template_cache),
                "total_templates_count": ntc_templates_count + custom_templates_count,
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {"error": str(e)}
