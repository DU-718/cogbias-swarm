"""
Agent B - 偏误模式匹配引擎 (Bias Pattern Matcher)
功能：检测决策树中的认知偏误，采用 Chain-of-Thought 推理
"""

import logging
import json
from typing import Dict, Any, List, Optional
from ..core.state import DecisionTree, BiasReport, BiasDetection, SessionState
from ..core.bias_knowledge import BiasKnowledgeBase
from ..utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class BiasPatternMatcher:
    """偏误模式匹配引擎 Agent"""
    
    def __init__(self, llm_client: LLMClient, config: Dict[str, Any]):
        """
        初始化偏误模式匹配引擎
        
        Args:
            llm_client: LLM 客户端
            config: Agent 配置
        """
        self.llm_client = llm_client
        self.config = config
        self.bias_knowledge = BiasKnowledgeBase()
        
        # 内置提示词 - 采用 Chain-of-Thought 推理
        self.system_prompt = """你是一个认知偏误检测专家，采用 Chain-of-Thought 推理方法逐步分析决策树中的偏误。

你的分析步骤：
1. 理解决策树结构和逻辑
2. 逐节点分析潜在的偏误模式
3. 应用偏误知识库进行模式匹配
4. 评估偏误严重程度
5. 生成纠正性问题

请严格按照 JSON 格式输出检测结果。"""
        
        self.analysis_prompt = """
请对以下决策树进行认知偏误检测，采用逐步推理的方法：

决策树信息：
- 主要结论: {primary_conclusion}
- 总节点数: {node_count}
- 节点类型分布: {node_distribution}

决策树节点详情：
{node_details}

偏误知识库参考：
{biases_reference}

请按照以下步骤进行分析：

步骤1: 理解决策逻辑
- 分析决策树的核心推理链条
- 识别关键假设和证据节点
- 评估逻辑一致性

步骤2: 逐节点偏误扫描
- 对每个节点应用偏误检测模式
- 考虑节点类型、内容、上下文
- 记录潜在的偏误信号

步骤3: 复合偏误识别
- 分析偏误之间的关联性
- 识别偏误簇（compound biases）
- 评估系统性风险

步骤4: 严重程度评估
- 基于偏误类型和影响范围评分
- 考虑决策的重要性
- 评估纠正的紧迫性

步骤5: 生成纠正策略
- 为每个检测到的偏误设计针对性问题
- 确保问题能有效挑战偏误逻辑
- 提供建设性的改进方向

请返回严格的 JSON 格式：
{{
    "detected_biases": [
        {{
            "bias_type": "偏误类型",
            "node_id": "相关节点ID",
            "confidence": 0.0-1.0,
            "reasoning": "逐步推理过程",
            "severity": "low|medium|high|critical",
            "correction_question": "纠正性问题",
            "evidence": ["证据1", "证据2"]
        }}
    ],
    "overall_risk_score": 0.0-1.0,
    "risk_heatmap": {{
        "node_id": 风险评分,
        ...
    }},
    "recommendations": ["建议1", "建议2"]
}}
"""
    
    def run(self, state: SessionState) -> SessionState:
        """
        执行偏误检测
        
        Args:
            state: 当前会话状态
            
        Returns:
            更新后的会话状态
        """
        logger.info(f"Agent B 开始偏误检测，迭代: {state.iteration_count}")
        
        if not state.decision_tree:
            logger.warning("没有决策树数据，跳过偏误检测")
            return state
        
        bias_report = self._detect_biases(state.decision_tree)
        state.bias_report = bias_report
        state.add_message("agent_b", "偏误检测完成", {
            "detected_biases_count": len(bias_report.detected_biases),
            "risk_score": bias_report.overall_risk_score
        })
        
        logger.info(f"Agent B 完成，检测到 {len(bias_report.detected_biases)} 个偏误")
        return state
    
    def _detect_biases(self, decision_tree: DecisionTree) -> BiasReport:
        """检测决策树中的偏误"""
        # 准备分析数据
        node_details = self._prepare_node_details(decision_tree)
        biases_reference = self._prepare_biases_reference()
        
        prompt = self.analysis_prompt.format(
            primary_conclusion=decision_tree.primary_conclusion,
            node_count=len(decision_tree.nodes),
            node_distribution=self._get_node_distribution(decision_tree),
            node_details=node_details,
            biases_reference=biases_reference
        )
        
        try:
            report_data = self.llm_client.generate_json(prompt, self.system_prompt)
            return self._validate_and_convert_report(report_data, decision_tree)
        except Exception as e:
            logger.error(f"偏误检测失败: {e}")
            return self._create_fallback_report(decision_tree)
    
    def _prepare_node_details(self, decision_tree: DecisionTree) -> str:
        """准备节点详情信息"""
        details = []
        
        for node_id, node in decision_tree.nodes.items():
            node_info = f"节点 {node_id}:"
            node_info += f"\n  - 类型: {node.node_type}"
            node_info += f"\n  - 内容: {node.content}"
            
            if node.node_type == "premise" and node.premise_type:
                node_info += f"\n  - 前提类型: {node.premise_type}"
            
            if node.node_type == "evidence":
                if node.evidence_strength:
                    node_info += f"\n  - 证据强度: {node.evidence_strength}"
                if node.reasoning_type:
                    node_info += f"\n  - 推理类型: {node.reasoning_type}"
            
            node_info += f"\n  - 置信度: {node.confidence}"
            
            if node.parent_id:
                node_info += f"\n  - 父节点: {node.parent_id}"
            
            if node.children_ids:
                node_info += f"\n  - 子节点: {', '.join(node.children_ids)}"
            
            if node.tags:
                node_info += f"\n  - 标签: {', '.join(node.tags)}"
            
            details.append(node_info)
        
        return "\n\n".join(details)
    
    def _prepare_biases_reference(self) -> str:
        """准备偏误知识库参考"""
        biases = self.bias_knowledge.get_all_biases()
        reference = []
        
        for bias in biases[:10]:  # 限制参考数量
            bias_info = f"{bias['name']} ({bias['category']}):"
            bias_info += f"\n  - 定义: {bias['definition']}"
            bias_info += f"\n  - 严重程度: {bias['severity']}"
            
            triggers = bias.get('triggers', [])
            if triggers:
                bias_info += f"\n  - 触发条件: {', '.join(triggers[:3])}"
            
            reference.append(bias_info)
        
        return "\n\n".join(reference)
    
    def _get_node_distribution(self, decision_tree: DecisionTree) -> str:
        """获取节点类型分布"""
        distribution = {"premise": 0, "evidence": 0, "conclusion": 0}
        
        for node in decision_tree.nodes.values():
            if node.node_type in distribution:
                distribution[node.node_type] += 1
        
        return f"前提: {distribution['premise']}, 证据: {distribution['evidence']}, 结论: {distribution['conclusion']}"
    
    def _validate_and_convert_report(self, report_data: Dict[str, Any], decision_tree: DecisionTree) -> BiasReport:
        """验证并转换偏误报告数据"""
        # 基本验证
        if "detected_biases" not in report_data:
            raise ValueError("缺失 detected_biases 字段")
        
        # 转换偏误检测结果
        detected_biases = []
        for bias_data in report_data["detected_biases"]:
            # 验证节点存在性
            node_id = bias_data.get("node_id")
            if node_id and node_id not in decision_tree.nodes:
                logger.warning(f"偏误检测引用不存在的节点: {node_id}")
                continue
            
            bias = BiasDetection(
                bias_type=bias_data["bias_type"],
                node_id=node_id or "",
                confidence=float(bias_data.get("confidence", 0.5)),
                reasoning=bias_data["reasoning"],
                severity=bias_data.get("severity", "medium"),
                correction_question=bias_data["correction_question"],
                evidence=bias_data.get("evidence", [])
            )
            detected_biases.append(bias)
        
        # 创建偏误报告
        return BiasReport(
            iteration=1,  # 将在工作流中设置正确值
            detected_biases=detected_biases,
            overall_risk_score=float(report_data.get("overall_risk_score", 0.5)),
            risk_heatmap=report_data.get("risk_heatmap", {}),
            recommendations=report_data.get("recommendations", [])
        )
    
    def _create_fallback_report(self, decision_tree: DecisionTree) -> BiasReport:
        """创建回退偏误报告"""
        # 使用简单的规则进行基础检测
        detected_biases = []
        
        # 检查假设性前提
        for node_id, node in decision_tree.nodes.items():
            if (node.node_type == "premise" and 
                node.premise_type == "assumption" and 
                node.confidence > 0.8):
                
                bias = BiasDetection(
                    bias_type="overconfidence_bias",
                    node_id=node_id,
                    confidence=0.6,
                    reasoning="假设性前提置信度过高，可能存在过度自信偏误",
                    severity="medium",
                    correction_question=f"为什么你对假设 '{node.content}' 如此自信？有哪些证据支持这个假设？",
                    evidence=["高置信度假设", "缺乏验证证据"]
                )
                detected_biases.append(bias)
        
        return BiasReport(
            iteration=1,
            detected_biases=detected_biases,
            overall_risk_score=0.3 if detected_biases else 0.1,
            risk_heatmap={},
            recommendations=["建议进行更全面的偏误检测"]
        )
    
    def analyze_bias_patterns(self, decision_tree: DecisionTree) -> Dict[str, Any]:
        """分析偏误模式"""
        patterns = {
            "confirmation_bias_patterns": self._detect_confirmation_bias(decision_tree),
            "overconfidence_patterns": self._detect_overconfidence(decision_tree),
            "anchoring_patterns": self._detect_anchoring(decision_tree),
            "groupthink_patterns": self._detect_groupthink(decision_tree)
        }
        
        return patterns
    
    def _detect_confirmation_bias(self, decision_tree: DecisionTree) -> List[Dict[str, Any]]:
        """检测确认偏误模式"""
        patterns = []
        
        for node_id, node in decision_tree.nodes.items():
            # 检查是否只包含支持性证据
            if node.node_type == "evidence":
                content_lower = node.content.lower()
                supporting_indicators = ["支持", "证实", "有利", "积极"]
                
                if any(indicator in content_lower for indicator in supporting_indicators):
                    # 检查是否有相反证据
                    has_contrary = False
                    for other_node in decision_tree.nodes.values():
                        if (other_node.node_type == "evidence" and 
                            any(word in other_node.content.lower() for word in ["反对", "否定", "不利", "消极"])):
                            has_contrary = True
                            break
                    
                    if not has_contrary:
                        patterns.append({
                            "node_id": node_id,
                            "pattern": "单一方向证据",
                            "confidence": 0.7
                        })
        
        return patterns
    
    def _detect_overconfidence(self, decision_tree: DecisionTree) -> List[Dict[str, Any]]:
        """检测过度自信模式"""
        patterns = []
        
        for node_id, node in decision_tree.nodes.items():
            # 高置信度但缺乏证据支持
            if (node.confidence > 0.8 and 
                node.node_type in ["premise", "conclusion"] and
                not self._has_strong_evidence(decision_tree, node_id)):
                
                patterns.append({
                    "node_id": node_id,
                    "pattern": "高置信度低证据",
                    "confidence": 0.8
                })
        
        return patterns
    
    def _detect_anchoring(self, decision_tree: DecisionTree) -> List[Dict[str, Any]]:
        """检测锚定偏误模式"""
        patterns = []
        
        # 检查是否有明显的初始参考点
        root_node = decision_tree.nodes.get(decision_tree.root_node_id)
        if root_node and "首先" in root_node.content or "初始" in root_node.content:
            patterns.append({
                "node_id": decision_tree.root_node_id,
                "pattern": "初始锚点",
                "confidence": 0.6
            })
        
        return patterns
    
    def _detect_groupthink(self, decision_tree: DecisionTree) -> List[Dict[str, Any]]:
        """检测群体思维模式"""
        patterns = []
        
        # 检查是否有共识性表述
        for node_id, node in decision_tree.nodes.items():
            content_lower = node.content.lower()
            group_indicators = ["大家一致", "普遍认为", "共识", "都同意"]
            
            if any(indicator in content_lower for indicator in group_indicators):
                patterns.append({
                    "node_id": node_id,
                    "pattern": "群体共识表述",
                    "confidence": 0.7
                })
        
        return patterns
    
    def _has_strong_evidence(self, decision_tree: DecisionTree, node_id: str) -> bool:
        """检查节点是否有强证据支持"""
        node = decision_tree.nodes.get(node_id)
        if not node:
            return False
        
        # 检查直接证据
        for child_id in node.children_ids:
            child = decision_tree.nodes.get(child_id)
            if (child and child.node_type == "evidence" and 
                child.evidence_strength and child.evidence_strength > 0.7):
                return True
        
        return False
    
    def generate_risk_heatmap(self, decision_tree: DecisionTree, bias_report: BiasReport) -> Dict[str, float]:
        """生成风险热力图"""
        heatmap = {}
        
        # 初始化所有节点风险为0
        for node_id in decision_tree.nodes:
            heatmap[node_id] = 0.0
        
        # 根据检测到的偏误分配风险分数
        for bias in bias_report.detected_biases:
            if bias.node_id in heatmap:
                # 根据偏误严重程度调整风险分数
                severity_multiplier = {
                    "low": 0.3,
                    "medium": 0.6,
                    "high": 0.8,
                    "critical": 1.0
                }.get(bias.severity, 0.5)
                
                heatmap[bias.node_id] += bias.confidence * severity_multiplier
        
        # 限制风险分数在0-1之间
        for node_id in heatmap:
            heatmap[node_id] = min(1.0, max(0.0, heatmap[node_id]))
        
        return heatmap