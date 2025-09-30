#!/usr/bin/env python3
"""
转换Obsidian文章到Hexo格式
"""
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

def convert_obsidian_to_hexo(source_file, target_dir):
    """转换单个Obsidian文件到Hexo格式"""

    # 读取原文件
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取文件名和标题
    source_path = Path(source_file)
    filename = source_path.stem

    # 处理Obsidian格式
    # 1. 转换双链语法 [[文件名]] -> 普通链接
    content = re.sub(r'\[\[([^\]]+)\]\]', r'[\1](/tags/\1/)', content)

    # 2. 处理图片链接
    content = re.sub(r'!\[\[([^\]]+)\]\]', r'![](/images/\1)', content)

    # 3. 提取或生成标题
    title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else filename

    # 4. 生成Hexo前置matter
    hexo_front_matter = f"""---
title: "{title}"
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
categories:
  - 技术文章
tags:
  - AI架构
  - 技术分享
author: 陈浩
description: "专业技术分享：{title}"
---

"""

    # 5. 清理已有的frontmatter（如果存在）
    if content.startswith('---'):
        # 查找第二个 ---
        end_pos = content.find('---', 3)
        if end_pos != -1:
            content = content[end_pos + 3:].strip()

    # 6. 组合最终内容
    final_content = hexo_front_matter + content

    # 7. 生成目标文件名
    # 使用简化的文件名，避免特殊字符
    safe_filename = re.sub(r'[^\w\-\u4e00-\u9fff]', '-', filename)
    target_filename = f"{safe_filename}.md"

    # 8. 写入目标文件
    target_path = Path(target_dir) / target_filename
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(final_content)

    return target_path, title

def main():
    """主函数"""
    # 定义路径
    obsidian_public_dir = "../public"
    hexo_posts_dir = "source/_posts"

    # 确保目标目录存在
    Path(hexo_posts_dir).mkdir(parents=True, exist_ok=True)

    print("🚀 开始转换文章...")

    # 遍历public目录中的所有markdown文件
    public_path = Path(obsidian_public_dir)

    if not public_path.exists():
        print(f"❌ 错误: {obsidian_public_dir} 目录不存在")
        return

    converted_files = []

    for md_file in public_path.glob("*.md"):
        print(f"📝 转换文件: {md_file.name}")

        try:
            target_path, title = convert_obsidian_to_hexo(md_file, hexo_posts_dir)
            converted_files.append((md_file.name, title))
            print(f"✅ 成功: {title} -> {target_path.name}")

        except Exception as e:
            print(f"❌ 失败: {md_file.name} - {str(e)}")

    print(f"\n🎉 转换完成! 共处理 {len(converted_files)} 个文件:")
    for original, title in converted_files:
        print(f"  • {original} -> {title}")

    print(f"\n📁 文章已保存到: {hexo_posts_dir}")
    print("💡 下一步: 运行 'npx hexo generate' 生成静态文件")

if __name__ == "__main__":
    main()