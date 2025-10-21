#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ts_to_qm_compiler.py - Pure Python implementation of .ts to .qm compiler

这是一个纯Python实现的Qt翻译文件编译器
将XML格式的.ts文件编译为二进制的.qm文件

参考: Qt的.qm文件格式规范
"""

import struct
import hashlib
from pathlib import Path
from xml.etree import ElementTree as ET


class QMCompiler:
    """Qt .qm文件编译器"""

    # .qm文件魔数
    QM_MAGIC = 0x950412de

    # 消息标签
    TAG_END = 1
    TAG_SOURCE_TEXT = 2
    TAG_TRANSLATION = 3
    TAG_CONTEXT = 4
    TAG_OBSOLETE = 5
    TAG_SOURCE_TEXT_PLURAL = 6
    TAG_COMMENT = 7
    TAG_DEPENDENCIES = 8

    def __init__(self):
        self.messages = []
        self.contexts = {}

    def parse_ts_file(self, ts_file):
        """解析.ts XML文件"""
        try:
            tree = ET.parse(ts_file)
            root = tree.getroot()

            for context in root.findall('context'):
                context_name = context.find('name')
                if context_name is None:
                    continue

                context_name = context_name.text or ""

                for message in context.findall('message'):
                    source = message.find('source')
                    translation = message.find('translation')

                    if source is None:
                        continue

                    source_text = source.text or ""

                    # 跳过空源文本
                    if not source_text:
                        continue

                    # 获取翻译文本
                    if translation is not None:
                        trans_type = translation.get('type', '')
                        # 跳过未完成的翻译
                        if trans_type == 'unfinished':
                            trans_text = ""
                        else:
                            trans_text = translation.text or ""
                    else:
                        trans_text = ""

                    self.messages.append({
                        'context': context_name,
                        'source': source_text,
                        'translation': trans_text
                    })

        except Exception as e:
            raise Exception(f"解析.ts文件失败: {e}")

    def write_byte(self, data, value):
        """写入单字节"""
        data.append(struct.pack('B', value & 0xFF))

    def write_uint32(self, data, value):
        """写入32位无符号整数(大端序)"""
        data.append(struct.pack('>I', value))

    def write_string(self, data, text):
        """写入字符串"""
        if not text:
            return
        encoded = text.encode('utf-8')
        for byte in encoded:
            self.write_byte(data, byte)

    def write_uint_array(self, data, values):
        """写入uint数组"""
        for value in values:
            self.write_uint32(data, value)

    def compile_to_qm(self, output_file):
        """编译为.qm文件"""
        data = []

        # 写入魔数
        self.write_uint32(data, self.QM_MAGIC)

        # 按context分组消息
        contexts = {}
        for msg in self.messages:
            ctx = msg['context']
            if ctx not in contexts:
                contexts[ctx] = []
            contexts[ctx].append(msg)

        # 写入每个context
        for context_name, messages in sorted(contexts.items()):
            # Context标签
            self.write_byte(data, self.TAG_CONTEXT)

            # Context名称 (作为字符串)
            context_bytes = context_name.encode('utf-8')
            self.write_uint32(data, len(context_bytes))
            for byte in context_bytes:
                self.write_byte(data, byte)

            # 写入这个context的所有消息
            for msg in messages:
                # Source text标签
                self.write_byte(data, self.TAG_SOURCE_TEXT)
                source_bytes = msg['source'].encode('utf-8')
                self.write_uint32(data, len(source_bytes))
                for byte in source_bytes:
                    self.write_byte(data, byte)

                # Translation标签
                if msg['translation']:
                    self.write_byte(data, self.TAG_TRANSLATION)
                    trans_bytes = msg['translation'].encode('utf-8')
                    self.write_uint32(data, len(trans_bytes))
                    for byte in trans_bytes:
                        self.write_byte(data, byte)

                # 消息结束
                self.write_byte(data, self.TAG_END)

        # 文件结束
        self.write_byte(data, self.TAG_END)

        # 写入文件
        with open(output_file, 'wb') as f:
            for chunk in data:
                f.write(chunk)

    @staticmethod
    def compile_file(ts_file, qm_file):
        """编译单个文件的便捷方法"""
        compiler = QMCompiler()
        compiler.parse_ts_file(ts_file)
        compiler.compile_to_qm(qm_file)
        return len(compiler.messages)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("用法: python ts_to_qm_compiler.py input.ts output.qm")
        sys.exit(1)

    ts_file = sys.argv[1]
    qm_file = sys.argv[2]

    try:
        count = QMCompiler.compile_file(ts_file, qm_file)
        print(f"✓ 编译成功: {count} 条消息")
    except Exception as e:
        print(f"✗ 编译失败: {e}")
        sys.exit(1)
