#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模糊搜索工具模块
实现基于Jaro-Winkler算法的智能工具名匹配
基于专业研究的阈值和权重配置
"""

import math
from typing import List, Tuple, Dict, Any


class FuzzySearchEngine:
    """
    模糊搜索引擎 - 专为BioNexus工具搜索优化
    
    特性:
    - Jaro-Winkler算法实现
    - 动态阈值（基于工具名长度）
    - 匹配度排序
    - 仅匹配工具名（不匹配描述）
    """
    
    # 实际优化的阈值配置（基于真实用户输入测试）
    THRESHOLD_SHORT = 0.70    # ≤3字符 (BWA)
    THRESHOLD_MEDIUM = 0.55   # 4-6字符 (BLAST, FastQC)  
    THRESHOLD_LONG = 0.55     # ≥7字符 (SAMtools, IQ-TREE)
    
    # Jaro-Winkler参数
    WINKLER_PREFIX_SCALE = 0.1  # 前缀加权因子
    WINKLER_PREFIX_LENGTH = 4   # 最多考虑前4个字符
    
    def __init__(self):
        """初始化模糊搜索引擎"""
        pass
    
    def jaro_similarity(self, s1: str, s2: str) -> float:
        """
        计算两个字符串的Jaro相似度
        
        Args:
            s1, s2: 要比较的字符串
            
        Returns:
            float: Jaro相似度 (0.0-1.0)
        """
        if s1 == s2:
            return 1.0
            
        len1, len2 = len(s1), len(s2)
        
        if len1 == 0 or len2 == 0:
            return 0.0
        
        # 匹配窗口大小
        match_window = max(len1, len2) // 2 - 1
        if match_window < 0:
            match_window = 0
        
        # 标记已匹配的字符
        s1_matches = [False] * len1
        s2_matches = [False] * len2
        
        matches = 0
        transpositions = 0
        
        # 寻找匹配字符
        for i in range(len1):
            start = max(0, i - match_window)
            end = min(i + match_window + 1, len2)
            
            for j in range(start, end):
                if s2_matches[j] or s1[i] != s2[j]:
                    continue
                s1_matches[i] = s2_matches[j] = True
                matches += 1
                break
        
        if matches == 0:
            return 0.0
        
        # 计算换位次数
        k = 0
        for i in range(len1):
            if not s1_matches[i]:
                continue
            while not s2_matches[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1
        
        # Jaro相似度公式
        jaro = (matches / len1 + matches / len2 + 
                (matches - transpositions / 2) / matches) / 3
        
        return jaro
    
    def jaro_winkler_similarity(self, s1: str, s2: str) -> float:
        """
        计算Jaro-Winkler相似度
        给前缀匹配额外加分
        
        Args:
            s1, s2: 要比较的字符串
            
        Returns:
            float: Jaro-Winkler相似度 (0.0-1.0)
        """
        jaro = self.jaro_similarity(s1, s2)
        
        if jaro < 0.7:  # Jaro相似度太低时不加前缀权重
            return jaro
        
        # 计算公共前缀长度
        prefix_length = 0
        for i in range(min(len(s1), len(s2), self.WINKLER_PREFIX_LENGTH)):
            if s1[i].lower() == s2[i].lower():
                prefix_length += 1
            else:
                break
        
        # Jaro-Winkler公式
        jw = jaro + (self.WINKLER_PREFIX_SCALE * prefix_length * (1 - jaro))
        
        return min(jw, 1.0)  # 确保不超过1.0
    
    def get_dynamic_threshold(self, tool_name: str) -> float:
        """
        根据工具名长度返回动态阈值
        基于专业研究的推荐值
        
        Args:
            tool_name: 工具名
            
        Returns:
            float: 推荐阈值
        """
        length = len(tool_name)
        
        if length <= 3:
            return self.THRESHOLD_SHORT
        elif length <= 6:
            return self.THRESHOLD_MEDIUM
        else:
            return self.THRESHOLD_LONG
    
    def abbreviation_match(self, query: str, original_tool_name: str) -> float:
        """
        简写匹配算法
        支持首字母缩写匹配，如 "fq" → "FastQC"
        
        Args:
            query: 搜索查询
            original_tool_name: 工具名（保持原始大小写）
            
        Returns:
            float: 简写匹配分数 (0.0-1.0)
        """
        if len(query) > len(original_tool_name):
            return 0.0
        
        query = query.lower()
        
        # 方法1: 提取驼峰命名的首字母 (如 FastQC → fq)
        first_letters = ""
        for i, char in enumerate(original_tool_name):
            if i == 0 or char.isupper():
                first_letters += char.lower()
        
        if len(first_letters) >= len(query) and first_letters.startswith(query):
            return 0.85 * (len(query) / len(first_letters))
        
        # 方法2: 处理连字符分隔的名称 (如 IQ-TREE → it)
        if '-' in original_tool_name:
            parts = original_tool_name.split('-')
            initials = ''.join(part[0].lower() for part in parts if part)
            
            if len(initials) >= len(query) and initials.startswith(query):
                return 0.85 * (len(query) / len(initials))
        
        # 方法3: 处理数字混合的情况 (如 HISAT2 → h2, hs2)
        letters_only = ''.join(char.lower() for char in original_tool_name if char.isalpha())
        if len(letters_only) >= len(query):
            # 尝试首字母 + 最后字母的组合
            if len(letters_only) >= 2:
                simple_abbr = letters_only[0] + letters_only[-1]
                if simple_abbr.startswith(query) and len(query) <= 2:
                    return 0.75
        
        return 0.0

    def search_tools(self, query: str, tools_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        智能搜索工具
        
        Args:
            query: 搜索查询词
            tools_data: 工具数据列表
            
        Returns:
            List[Dict]: 按匹配度排序的匹配工具列表
                       每个工具包含原数据 + match_score字段
        """
        if not query.strip():
            # 空查询返回所有工具（按字母顺序）
            return sorted(tools_data, key=lambda x: x['name'].lower())
        
        query = query.strip()
        matches = []
        
        for tool in tools_data:
            tool_name = tool['name']
            
            # 1. 精确匹配（不区分大小写）
            if query.lower() == tool_name.lower():
                match_score = 1.0
            else:
                # 2. 前缀匹配（高优先级）
                if tool_name.lower().startswith(query.lower()):
                    match_score = 0.95
                else:
                    # 3. 模糊匹配（Jaro-Winkler）
                    jw_score = self.jaro_winkler_similarity(query, tool_name)
                    
                    # 4. 简写匹配
                    abbr_score = self.abbreviation_match(query, tool_name)
                    
                    # 取最高分
                    match_score = max(jw_score, abbr_score)
            
            # 5. 检查是否达到动态阈值
            threshold = self.get_dynamic_threshold(tool_name)
            
            if match_score >= threshold:
                # 创建匹配结果
                matched_tool = tool.copy()
                matched_tool['match_score'] = round(match_score, 4)
                matches.append(matched_tool)
        
        # 6. 按匹配度排序（降序），匹配度相同按名称排序（升序）
        matches.sort(key=lambda x: (-x['match_score'], x['name'].lower()))
        
        return matches
    
    def highlight_match(self, query: str, tool_name: str) -> str:
        """
        高亮显示匹配部分（未来可用于UI显示）
        
        Args:
            query: 搜索查询
            tool_name: 工具名
            
        Returns:
            str: 带高亮标记的工具名
        """
        # 简单的前缀匹配高亮
        if tool_name.lower().startswith(query.lower()):
            prefix_len = len(query)
            return f"**{tool_name[:prefix_len]}**{tool_name[prefix_len:]}"
        
        return tool_name
    
    def get_search_statistics(self, query: str, tools_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取搜索统计信息（用于调试和优化）
        
        Args:
            query: 搜索查询
            tools_data: 工具数据
            
        Returns:
            Dict: 搜索统计信息
        """
        matches = self.search_tools(query, tools_data)
        
        stats = {
            'query': query,
            'total_tools': len(tools_data),
            'matched_tools': len(matches),
            'match_rate': len(matches) / len(tools_data) if tools_data else 0,
            'top_scores': [tool.get('match_score', 0.0) for tool in matches[:3]],
            'matched_names': [tool['name'] for tool in matches]
        }
        
        return stats


# 全局搜索引擎实例（单例模式）
_search_engine = None

def get_search_engine() -> FuzzySearchEngine:
    """获取全局搜索引擎实例"""
    global _search_engine
    if _search_engine is None:
        _search_engine = FuzzySearchEngine()
    return _search_engine


# 便捷函数
def fuzzy_search_tools(query: str, tools_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    便捷函数：模糊搜索工具
    
    Args:
        query: 搜索查询
        tools_data: 工具数据列表
        
    Returns:
        List[Dict]: 按匹配度排序的工具列表
    """
    engine = get_search_engine()
    return engine.search_tools(query, tools_data)


if __name__ == "__main__":
    # 测试代码
    test_tools = [
        {'name': 'FastQC', 'category': 'quality', 'description': '质量控制工具'},
        {'name': 'BLAST', 'category': 'sequence', 'description': '序列比对工具'},
        {'name': 'BWA', 'category': 'sequence', 'description': '序列比对器'},
        {'name': 'SAMtools', 'category': 'genomics', 'description': '基因组工具'},
        {'name': 'HISAT2', 'category': 'rnaseq', 'description': 'RNA-seq工具'},
        {'name': 'IQ-TREE', 'category': 'phylogeny', 'description': '进化树构建'}
    ]
    
    engine = FuzzySearchEngine()
    
    # 测试各种搜索场景
    test_queries = ['fastqc', 'fasqc', 'fq', 'bwa', 'bla', 'samtools', 'samtool']
    
    for query in test_queries:
        print(f"\n搜索查询: '{query}'")
        results = engine.search_tools(query, test_tools)
        for tool in results:
            print(f"  {tool['name']}: {tool['match_score']:.4f}")
        
        stats = engine.get_search_statistics(query, test_tools)
        print(f"  统计: {stats['matched_tools']}/{stats['total_tools']} 匹配")