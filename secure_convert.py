#!/usr/bin/env python3
"""
安全的文章转换脚本 - 添加路径验证
"""
import os
import re
from pathlib import Path
from datetime import datetime

def is_safe_path(file_path, base_obsidian_path):
    """检查文件路径是否在obsidian目录范围内"""
    try:
        # 解析实际路径
        resolved_path = Path(file_path).resolve()
        base_path = Path(base_obsidian_path).resolve()

        # 检查是否在基础目录内
        return str(resolved_path).startswith(str(base_path))
    except Exception:
        return False

def convert_with_security_check(source_file, target_dir, base_obsidian_path):
    """带安全检查的转换函数"""

    # 如果是软链接，获取真实路径
    if os.path.islink(source_file):
        real_path = os.path.realpath(source_file)
        print(f"🔗 软链接: {source_file} -> {real_path}")

        # 安全检查
        if not is_safe_path(real_path, base_obsidian_path):
            print(f"⚠️  警告: {real_path} 超出obsidian目录范围，跳过")
            return None

        source_file = real_path

    # 检查文件是否存在
    if not os.path.exists(source_file):
        print(f"❌ 文件不存在: {source_file}")
        return None

    # 读取文件内容（使用原有逻辑）
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 其他转换逻辑保持不变...
    # [这里复制原来的转换逻辑]

    return f"✅ 安全转换: {os.path.basename(source_file)}"

def main():
    """主函数"""
    obsidian_public_dir = "../public"
    hexo_posts_dir = "source/_posts"
    base_obsidian_path = "../.."  # obsidian根目录

    print("🔒 开始安全转换检查...")

    # 检查public目录中的所有链接
    for md_file in Path(obsidian_public_dir).glob("*.md"):
        if os.path.islink(md_file):
            real_path = os.path.realpath(md_file)
            is_safe = is_safe_path(real_path, base_obsidian_path)

            print(f"{'✅' if is_safe else '❌'} {md_file.name} -> {real_path}")

            if not is_safe:
                print(f"   ⚠️  路径超出安全范围！")

if __name__ == "__main__":
    main()