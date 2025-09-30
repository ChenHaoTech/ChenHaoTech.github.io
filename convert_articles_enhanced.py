#!/usr/bin/env python3
"""
增强版文章转换脚本 - 基于ctime/mtime管理Hexo日期
"""
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

def parse_frontmatter_simple(content):
    """简单解析frontmatter，提取时间相关字段"""
    if not content.startswith('---'):
        return {}, content

    end_pos = content.find('---', 3)
    if end_pos == -1:
        return {}, content

    frontmatter_text = content[4:end_pos]
    remaining_content = content[end_pos + 3:]

    metadata = {}

    # 解析各种时间字段
    time_fields = ['ctime', 'mtime', 'created', 'updated', 'date']

    for field in time_fields:
        # 匹配格式: field: 2025-09-26 或 field: 2025-09-26 10:06
        pattern = rf'{field}:\s*([0-9\-\s:]+)'
        match = re.search(pattern, frontmatter_text)
        if match:
            metadata[field] = match.group(1).strip()

    # 解析标签
    tags_match = re.search(r'tags:\s*\n((?:\s+-\s+[^\n]+\n)*)', frontmatter_text)
    if tags_match:
        tags_lines = tags_match.group(1)
        tags = re.findall(r'-\s+([^\n]+)', tags_lines)
        # 清理标签中的引号和#前缀
        clean_tags = []
        for tag in tags:
            tag = tag.strip().strip('"\'').strip('#')
            if tag:
                clean_tags.append(tag)
        metadata['tags'] = clean_tags

    # 解析单行标签格式
    single_tags = re.search(r'tags:\s*\[([^\]]+)\]', frontmatter_text)
    if single_tags and 'tags' not in metadata:
        tags_str = single_tags.group(1)
        tags = [t.strip().strip('"\'').strip('#') for t in tags_str.split(',')]
        metadata['tags'] = [t for t in tags if t]

    # 解析public字段
    public_match = re.search(r'public:\s*\n((?:\s+-\s+\w+\s*\n)*)', frontmatter_text)
    if public_match:
        public_lines = public_match.group(1)
        platforms = re.findall(r'-\s+(\w+)', public_lines)
        metadata['public'] = platforms

    return metadata, remaining_content

def parse_time_string(time_str):
    """解析时间字符串为datetime对象"""
    if not time_str:
        return None

    # 尝试各种时间格式
    formats = [
        '%Y-%m-%d %H:%M:%S',  # 2025-09-26 10:06:30
        '%Y-%m-%d %H:%M',     # 2025-09-26 10:06
        '%Y-%m-%d',           # 2025-09-26
        '%Y/%m/%d %H:%M:%S',  # 2025/09/26 10:06:30
        '%Y/%m/%d %H:%M',     # 2025/09/26 10:06
        '%Y/%m/%d',           # 2025/09/26
    ]

    for fmt in formats:
        try:
            return datetime.strptime(time_str.strip(), fmt)
        except ValueError:
            continue

    return None

def determine_article_date(metadata, file_path):
    """根据元数据确定文章日期"""
    # 优先级：ctime > created > mtime > updated > 文件系统时间

    # 1. 尝试ctime（创建时间）
    if 'ctime' in metadata:
        parsed_time = parse_time_string(metadata['ctime'])
        if parsed_time:
            return parsed_time, 'ctime'

    # 2. 尝试created
    if 'created' in metadata:
        parsed_time = parse_time_string(metadata['created'])
        if parsed_time:
            return parsed_time, 'created'

    # 3. 尝试mtime（修改时间）
    if 'mtime' in metadata:
        parsed_time = parse_time_string(metadata['mtime'])
        if parsed_time:
            return parsed_time, 'mtime'

    # 4. 尝试updated
    if 'updated' in metadata:
        parsed_time = parse_time_string(metadata['updated'])
        if parsed_time:
            return parsed_time, 'updated'

    # 5. 使用文件系统的修改时间
    try:
        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        return file_mtime, 'file_mtime'
    except:
        pass

    # 6. 默认使用当前时间
    return datetime.now(), 'default'

def generate_hexo_permalink(title, date):
    """生成Hexo风格的permalink"""
    # 生成安全的URL slug
    slug = re.sub(r'[^\w\u4e00-\u9fff\s-]', '', title)
    slug = re.sub(r'[-\s]+', '-', slug).strip('-').lower()

    # 限制长度
    if len(slug) > 50:
        slug = slug[:50].rstrip('-')

    return f"/{date.year}/{date.month:02d}/{date.day:02d}/{slug}/"

def determine_categories(metadata, file_path):
    """根据文件路径和标签确定分类"""
    categories = []

    # 基于文件路径确定主分类
    path_parts = Path(file_path).parts

    if 'computer' in path_parts:
        categories.append('技术文章')
        # 子分类
        if 'AI' in path_parts:
            categories.append('人工智能')
        elif '系统设计' in path_parts:
            categories.append('系统架构')
        elif '算法和数据结构' in path_parts:
            categories.append('算法数据结构')
        elif '架构设计' in path_parts:
            categories.append('架构设计')
    elif 'AREA' in path_parts:
        if '创业认知' in path_parts:
            categories.extend(['商业思考', '创业分析'])
        elif '专业力' in path_parts:
            categories.extend(['职业发展', '专业成长'])
        else:
            categories.append('知识管理')
    elif 'Project' in path_parts:
        categories.append('项目实践')
        if 'meituan' in path_parts:
            categories.append('工作项目')
        else:
            categories.append('个人项目')
    else:
        categories.append('其他')

    return categories

def convert_obsidian_to_hexo_enhanced(source_file, target_dir):
    """增强版转换：基于时间元数据管理日期"""

    # 读取原文件
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 解析元数据
    metadata, main_content = parse_frontmatter_simple(content)

    # 确定文章日期
    article_date, date_source = determine_article_date(metadata, source_file)

    # 提取或生成标题
    title_match = re.search(r'^# (.+)$', main_content, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()
    else:
        title = Path(source_file).stem

    # 确定分类
    categories = determine_categories(metadata, source_file)

    # 生成permalink
    permalink = generate_hexo_permalink(title, article_date)

    # 处理标签
    tags = metadata.get('tags', ['技术分享'])
    if not tags:
        tags = ['技术分享']

    # 处理内容中的链接
    # 转换双链语法 [[文件名]] -> 普通链接
    main_content = re.sub(r'\[\[([^\]]+)\]\]', r'[\1](/tags/\1/)', main_content)

    # 处理图片链接
    main_content = re.sub(r'!\[\[([^\]]+)\]\]', r'![](/images/\1)', main_content)

    # 生成Hexo前置matter
    hexo_front_matter = f"""---
title: "{title}"
date: {article_date.strftime('%Y-%m-%d %H:%M:%S')}
updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
categories:"""

    # 添加分类
    for category in categories:
        hexo_front_matter += f"\n  - {category}"

    hexo_front_matter += "\ntags:"
    # 添加标签
    for tag in tags:
        hexo_front_matter += f"\n  - {tag}"

    hexo_front_matter += f"""
permalink: {permalink}
author: 陈浩
description: "{title[:100]}..."
date_source: {date_source}
original_path: "{source_file}"
---

"""

    # 清理已有的frontmatter
    if main_content.startswith('---'):
        end_pos = main_content.find('---', 3)
        if end_pos != -1:
            main_content = main_content[end_pos + 3:].strip()

    # 组合最终内容
    final_content = hexo_front_matter + main_content

    # 生成目标文件名 - 包含日期前缀
    date_prefix = article_date.strftime('%Y-%m-%d')
    safe_filename = re.sub(r'[^\w\-\u4e00-\u9fff]', '-', Path(source_file).stem)
    safe_filename = re.sub(r'-+', '-', safe_filename).strip('-')
    target_filename = f"{date_prefix}-{safe_filename}.md"

    # 写入目标文件
    target_path = Path(target_dir) / target_filename
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(final_content)

    return target_path, title, article_date, date_source

def generate_conversion_report(conversions):
    """生成转换报告"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 按日期排序
    conversions.sort(key=lambda x: x['date'])

    # 统计信息
    total_files = len(conversions)
    date_sources = {}
    categories_count = {}

    for conv in conversions:
        source = conv['date_source']
        date_sources[source] = date_sources.get(source, 0) + 1

        for category in conv['categories']:
            categories_count[category] = categories_count.get(category, 0) + 1

    report_content = f"""# 文章转换报告（增强版）

> 转换时间: {timestamp}

## 📊 转换统计

- **转换文件**: {total_files} 篇
- **时间跨度**: {conversions[0]['date'].strftime('%Y-%m-%d')} 至 {conversions[-1]['date'].strftime('%Y-%m-%d')}

### 📅 日期来源分析

"""

    for source, count in sorted(date_sources.items()):
        source_desc = {
            'ctime': 'frontmatter中的ctime字段',
            'created': 'frontmatter中的created字段',
            'mtime': 'frontmatter中的mtime字段',
            'updated': 'frontmatter中的updated字段',
            'file_mtime': '文件系统修改时间',
            'default': '当前时间（默认）'
        }

        report_content += f"- **{source_desc.get(source, source)}**: {count} 篇文章\n"

    report_content += f"""

### 🏷️ 分类分布

"""

    for category, count in sorted(categories_count.items(), key=lambda x: x[1], reverse=True):
        report_content += f"- **{category}**: {count} 篇文章\n"

    report_content += f"""

## 📝 详细转换记录

| 序号 | 标题 | 日期 | 日期来源 | 分类 |
|------|------|------|----------|------|
"""

    for i, conv in enumerate(conversions, 1):
        categories_str = ' / '.join(conv['categories'])
        report_content += f"| {i} | {conv['title'][:30]}{'...' if len(conv['title']) > 30 else ''} | {conv['date'].strftime('%Y-%m-%d')} | {conv['date_source']} | {categories_str} |\n"

    report_content += f"""

## 🔄 时间线分析

### 按年份分布
"""

    # 按年份分组
    years = {}
    for conv in conversions:
        year = conv['date'].year
        years[year] = years.get(year, 0) + 1

    for year in sorted(years.keys()):
        report_content += f"- **{year}年**: {years[year]} 篇文章\n"

    report_content += f"""

### 按月份分布（最近一年）
"""

    # 按月份分组（最近一年）
    recent_months = {}
    current_year = datetime.now().year

    for conv in conversions:
        if conv['date'].year == current_year:
            month_key = conv['date'].strftime('%Y-%m')
            recent_months[month_key] = recent_months.get(month_key, 0) + 1

    for month in sorted(recent_months.keys()):
        report_content += f"- **{month}**: {recent_months[month]} 篇文章\n"

    report_content += f"""

## 💡 发现和建议

### 内容创作趋势
"""

    if years:
        max_year = max(years.keys())
        max_count = years[max_year]
        report_content += f"- 最活跃年份: {max_year}年 ({max_count} 篇文章)\n"

    if 'ctime' in date_sources and date_sources['ctime'] > total_files * 0.8:
        report_content += "- ✅ 大部分文章都有准确的创建时间记录\n"
    elif 'file_mtime' in date_sources and date_sources['file_mtime'] > total_files * 0.5:
        report_content += "- ⚠️  建议为文章添加ctime字段以获得更准确的时间记录\n"

    report_content += f"""

### 分类建议
"""

    if ' 技术文章' in categories_count and categories_count['技术文章'] > total_files * 0.7:
        report_content += "- 📚 技术内容丰富，建议进一步细分技术子类别\n"

    if len(categories_count) < 5:
        report_content += "- 🔄 内容分类较少，建议增加更多元化的内容类型\n"

    report_content += f"""

---

*此报告由 `enhanced-convert-articles.py` 自动生成*
"""

    return report_content

def main():
    """主函数"""
    print("🚀 增强版文章转换脚本（基于时间元数据）")
    print("="*50)

    # 定义路径
    obsidian_public_dir = "../public"
    hexo_posts_dir = "source/_posts"

    # 确保目标目录存在
    Path(hexo_posts_dir).mkdir(parents=True, exist_ok=True)

    print("📝 开始转换文章...")

    # 遍历public目录中的所有markdown文件
    public_path = Path(obsidian_public_dir)

    if not public_path.exists():
        print(f"❌ 错误: {obsidian_public_dir} 目录不存在")
        return

    conversions = []

    for md_file in public_path.glob("*.md"):
        if md_file.name.startswith('.') or md_file.name in ['README.md']:
            continue

        print(f"📝 处理文件: {md_file.name}")

        try:
            target_path, title, article_date, date_source = convert_obsidian_to_hexo_enhanced(
                md_file, hexo_posts_dir
            )

            # 确定分类（重新调用以获取分类信息）
            if md_file.is_symlink():
                real_path = md_file.resolve()
                categories = determine_categories({}, real_path)
            else:
                categories = determine_categories({}, md_file)

            conversions.append({
                'original': md_file.name,
                'target': target_path.name,
                'title': title,
                'date': article_date,
                'date_source': date_source,
                'categories': categories
            })

            print(f"✅ 成功: {title}")
            print(f"   日期: {article_date.strftime('%Y-%m-%d %H:%M')} (来源: {date_source})")
            print(f"   输出: {target_path.name}")

        except Exception as e:
            print(f"❌ 失败: {md_file.name} - {str(e)}")

    # 生成转换报告
    if conversions:
        report_content = generate_conversion_report(conversions)
        report_file = Path('../文章转换报告.md')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"\n📋 转换报告已生成: {report_file}")

    print(f"\n🎉 转换完成! 共处理 {len(conversions)} 个文件")
    print(f"📁 文章已保存到: {hexo_posts_dir}")
    print("💡 下一步: 运行 'npx hexo generate' 生成静态文件")

if __name__ == "__main__":
    main()