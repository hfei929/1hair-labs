#!/usr/bin/env python3
"""📸 拍摄标记清理 —— 站点仓库构建源专用（macOS/Linux 通用，python3 零依赖）。

覆盖 2026-10-04 线上实测的全部四种形态：
  A. 代码围栏内注释行：  # 📸 查看 kube-dns Service
  B. 代码围栏内裸标记：  📸 确认测试 Service 存在
  C. 引用块指令行：      > 📸 **实践截图①**：...
  D. 行内嵌方括号：      正文。 📸[截图 1：…] / 📸 [截图点：…] 后续正文
规则：A/B/C 整行删（独立指令行，删后折叠多余空行）；D 只删标记段、保正文。
其余内容字节不动；结束时报残留数，非零退出码便于接入构建检查。

用法：
  python3 strip_camera_marks.py <文件或目录>...
示例（站点仓库根目录跑）：
  python3 strip_camera_marks.py docs/
  grep -rn '📸' docs/ && echo "还有残留，人工看" || echo "归零，可构建"
"""
import re
import sys
import pathlib

# 形态 D：emoji 后容忍空格/变体选择符等杂字符再接 [截图…]；也兼容无方括号前缀的行内标记（fallback 仅删到行尾注释段）
INLINE_BRACKET = re.compile(r'[ \t]*📸[^\[\n]{0,12}\[截图[^\]\n]*\][ \t]*')


def clean_text(text: str):
    src = text.split('\n')
    out = []
    fence = False
    removed_lines = 0
    inline_hits = 0
    skip_blank = False  # 刚删过一行，且其前后都是空行 → 吞掉后一个空行

    for line in src:
        if line.lstrip().startswith('```'):
            fence = not fence
            out.append(line)
            skip_blank = False
            continue

        s = line.lstrip()

        # 形态 A/B：围栏内指令行（# 📸 或裸 📸 开头）
        if fence and (s.startswith('📸') or re.match(r'#\s*📸', s)):
            removed_lines += 1
            if out and out[-1].strip() == '':
                skip_blank = True
            continue

        # 形态 C：引用块指令行（整行就是拍摄指令）
        if not fence and re.match(r'>\s*📸', s) and '[' not in line and ']' not in line:
            removed_lines += 1
            if out and out[-1].strip() == '':
                skip_blank = True
            continue
        # 引用块带方括号的（> 📸 [截图…]）走形态 D 替换

        # 形态 D：行内嵌方括号标记
        if '📸' in line:
            new_line = INLINE_BRACKET.sub(' ', line)
            if new_line != line:
                inline_hits += 1
                line = new_line

        if skip_blank and line.strip() == '':
            skip_blank = False
            continue
        skip_blank = False
        out.append(line)

    return '\n'.join(out), removed_lines, inline_hits


def main():
    targets = []
    for arg in sys.argv[1:]:
        p = pathlib.Path(arg)
        if p.is_file():
            targets.append(p)
        elif p.is_dir():
            targets.extend(sorted(p.rglob('*.md')))

    total_removed = 0
    total_inline = 0
    total_left = 0
    dirty_files = []

    for f in targets:
        try:
            text = f.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            print(f"{f}: 跳过（非 UTF-8）")
            continue
        if '📸' not in text:
            continue
        new_text, removed, inline = clean_text(text)
        left = new_text.count('📸')
        total_removed += removed
        total_inline += inline
        total_left += left
        if left:
            dirty_files.append(str(f))
        f.write_text(new_text, encoding='utf-8')
        print(f"{f}: 删指令行 {removed}，行内标记 {inline}，残留 {left}" + ("  ⚠️ 需人工看" if left else "  ✓"))

    print(f"\n合计：整行删 {total_removed}，行内删 {total_inline}，残留 {total_left}")
    if dirty_files:
        print("残留文件（人工处理）：")
        for d in dirty_files:
            print(f"  {d}")
        sys.exit(1)


if __name__ == '__main__':
    main()
