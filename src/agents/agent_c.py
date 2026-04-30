"""
Agent C - 对抗性推理 Agent (Adversarial Challenger)
功能：生成尖锐的认知挑战问题，进行逻辑漏洞测试
"""

import logging
import json
from typing import Dict, Any, List, Optional
from ..core.state import DecisionTree, BiasReport, AdversarialQuestion, SessionState
from ..core.bias_knowledge import BiasKnowledgeBase
from ..utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class AdversarialChallenger:
    """对抗性推理 Agent"""
    
    def __init__(self, llm_client: LLMClient, config: Dict[str, Any]):
        """
        初始化对抗性推理 Agent
        
        Args:
            llm_client: LLM 客户端
            config: Agent 配置
        """
        self.llm_client = llm_client
        self.config = config
        self.bias_knowledge = BiasKnowledgeBase()
        
        # 内置提示词 - 强调尖锐性和逻辑严谨性
        self.system_prompt = """你是一个专业的认知对手，专门挑战决策中的逻辑漏洞和认知偏误。

你的角色定位：
- 尖锐的质疑者，不是友好的助手
- 逻辑严谨的挑战者，不是情绪化的批评者
- 基于证据的诘问者，不是主观的反对者

你的任务是为检测到的认知偏误生成三类挑战问题：
1. 反事实情景 - 假设相反前提推导最坏结果
2. 异见者角色扮演 - 指定利益相关方的尖锐诘问
3. 极端压力测试 - 边界案例和证伪方案要求

所有问题必须：
- 逻辑缜密，基于具体证据
- 针对性强，直指偏误核心
- 挑战性强，能真正暴露逻辑漏洞
- 非情绪化，保持专业客观

严禁生成通用反问或温和建议。"""
        
        self.challenge_prompt = """
基于以下决策树和偏误检测结果，生成尖锐的对抗性问题：

决策树信息：
- 主要结论: {primary_conclusion}
- 检测到的偏误数量: {bias_count}

偏误检测详情：
{bias_details}

决策树结构：
{tree_structure}

请为每个检测到的偏误生成1-2个对抗性问题，确保问题：
1. 直指偏误的逻辑核心
2. 基于具体的节点内容
3. 具有真正的挑战性
4. 要求用户提供证伪方案

问题类型分布：
- 反事实情景: 40%
- 异见者角色扮演: 40%  
- 极端压力测试: 20%

请返回严格的 JSON 格式：
{{
    "adversarial_questions": [
        {{
            "question_type": "counterfactual|stakeholder|stress_test",
            "question_text": "尖锐的问题文本",
            "target_node_id": "相关节点ID",
            "bias_type": "针对的偏误类型",
            "intensity": "mild|moderate|strong",
            "expected_response_type": "期望的回应类型"
        }}
    ]
}}

示例问题风格：
- 反事实: "如果相反的前提成立，你的结论会如何崩塌？请具体描述连锁反应。"
- 异见者: "作为直接受此决策影响的失败者，我要问：你凭什么认为这个假设对所有相关方都公平？"
- 压力测试: "在什么极端条件下，你的整个推理链条会完全失效？请给出具体的证伪条件。"
"""
    
    def run(self, state: SessionState) -> SessionState:
        """
        生成对抗性问题
        
        Args:
            state: 当前会话状态
            
        Returns:
            更新后的会话状态
        """
        logger.info(f"Agent C 开始生成对抗性问题，迭代: {state.iteration_count}")
        
        if not state.decision_tree or not state.bias_report:
            logger.warning("缺少决策树或偏误报告，跳过问题生成")
            return state
        
        adversarial_questions = self._generate_challenges(state.decision_tree, state.bias_report)
        state.adversarial_questions = adversarial_questions
        state.add_message("agent_c", "对抗性问题生成完成", {
            "question_count": len(adversarial_questions),
            "question_types": list(set([q.question_type for q in adversarial_questions]))
        })
        
        logger.info(f"Agent C 完成，生成 {len(adversarial_questions)} 个对抗性问题")
        return state
    
    def _generate_challenges(self, decision_tree: DecisionTree, bias_report: BiasReport) -> List[AdversarialQuestion]:
        """生成对抗性挑战问题"""
        # 准备分析数据
        bias_details = self._prepare_bias_details(bias_report, decision_tree)
        tree_structure = self._prepare_tree_structure(decision_tree)
        
        prompt = self.challenge_prompt.format(
            primary_conclusion=decision_tree.primary_conclusion,
            bias_count=len(bias_report.detected_biases),
            bias_details=bias_details,
            tree_structure=tree_structure
        )
        
        try:
            questions_data = self.llm_client.generate_json(prompt, self.system_prompt)
            return self._validate_and_convert_questions(questions_data, decision_tree)
        except Exception as e:
            logger.error(f"对抗性问题生成失败: {e}")
            return self._create_fallback_questions(bias_report, decision_tree)
    
    def _prepare_bias_details(self, bias_report: BiasReport, decision_tree: DecisionTree) -> str:
        """准备偏误详情信息"""
        details = []
        
        for i, bias in enumerate(bias_report.detected_biases[:5]):  # 限制处理数量
            bias_info = f"偏误 {i+1}:"
            bias_info += f"\n  - 类型: {bias.bias_type}"
            bias_info += f"\n  - 严重程度: {bias.severity}"
            bias_info += f"\n  - 置信度: {bias.confidence}"
            
            if bias.node_id and bias.node_id in decision_tree.nodes:
                node = decision_tree.nodes[bias.node_id]
                bias_info += f"\n  - 相关节点: {node.content[:50]}..."
            
            bias_info += f"\n  - 推理依据: {bias.reasoning[:100]}..."
            
            details.append(bias_info)
        
        return "\n\n".join(details)
    
    def _prepare_tree_structure(self, decision_tree: DecisionTree) -> str:
        """准备决策树结构信息"""
        structure = []
        
        # 获取关键节点路径
        critical_nodes = self._identify_critical_nodes(decision_tree)
        
        for node_id in critical_nodes:
            if node_id in decision_tree.nodes:
                node = decision_tree.nodes[node_id]
                path = decision_tree.get_node_path(node_id)
                
                path_info = " -> ".join([n.content[:20] + "..." for n in path])
                structure.append(f"{node_id}: {path_info}")
        
        return "\n".join(structure[:10])  # 限制输出长度
    
    def _identify_critical_nodes(self, decision_tree: DecisionTree) -> List[str]:
        """识别关键节点"""
        critical_nodes = []
        
        # 根节点
        critical_nodes.append(decision_tree.root_node_id)
        
        # 高置信度假设节点
        for node_id, node in decision_tree.nodes.items():
            if (node.node_type == "premise" and 
                node.premise_type == "assumption" and 
                node.confidence > 0.7):
                critical_nodes.append(node_id)
        
        # 证据强度高的节点
        for node_id, node in decision_tree.nodes.items():
            if (node.node_type == "evidence" and 
                node.evidence_strength and 
                node.evidence_strength > 0.8):
                critical_nodes.append(node_id)
        
        return list(set(critical_nodes))  # 去重
    
    def _validate_and_convert_questions(self, questions_data: Dict[str, Any], decision_tree: DecisionTree) -> List[AdversarialQuestion]:
        """验证并转换问题数据"""
        if "adversarial_questions" not in questions_data:
            raise ValueError("缺失 adversarial_questions 字段")
        
        questions = []
        
        for q_data in questions_data["adversarial_questions"]:
            # 验证必要字段
            required_fields = ["question_type", "question_text", "target_node_id", "bias_type"]
            for field in required_fields:
                if field not in q_data:
                    logger.warning(f"问题数据缺失字段: {field}")
                    continue
            
            # 验证节点存在性
            target_node_id = q_data["target_node_id"]
            if target_node_id and target_node_id not in decision_tree.nodes:
                logger.warning(f"问题引用不存在的节点: {target_node_id}")
                # 不跳过，但记录警告
            
            question = AdversarialQuestion(
                question_type=q_data["question_type"],
                question_text=q_data["question_text"],
                target_node_id=target_node_id,
                bias_type=q_data["bias_type"],
                intensity=q_data.get("intensity", "moderate"),
                expected_response_type=q_data.get("expected_response_type", "detailed")
            )
            questions.append(question)
        
        return questions
    
    def _create_fallback_questions(self, bias_report: BiasReport, decision_tree: DecisionTree) -> List[AdversarialQuestion]:
        """创建回退问题"""
        questions = []
        
        for i, bias in enumerate(bias_report.detected_biases[:3]):  # 限制数量
            # 根据偏误类型生成基础问题
            if bias.bias_type == "confirmation_bias":
                question_text = f"你是否有意寻找过反对你结论的证据？如果没有，为什么？"
                question_type = "counterfactual"
            elif bias.bias_type == "overconfidence_bias":
                question_text = f"你的置信度基于什么具体证据？请列出所有支持和不支持的因素。"
                question_type = "stress_test"
            else:
                question_text = f"这个决策可能对哪些利益相关方造成不公平影响？"
                question_type = "stakeholder"
            
            question = AdversarialQuestion(
                question_type=question_type,
                question_text=question_text,
                target_node_id=bias.node_id,
                bias_type=bias.bias_type,
                intensity="moderate",
                expected_response_type="detailed"
            )
            questions.append(question)
        
        return questions
    
    def enhance_question_quality(self, question: AdversarialQuestion, decision_tree: DecisionTree) -> AdversarialQuestion:
        """增强问题质量"""
        enhanced_text = question.question_text
        
        # 确保问题具体化
        if question.target_node_id and question.target_node_id in decision_tree.nodes:
            node = decision_tree.nodes[question.target_node_id]
            
            # 根据问题类型增强
            if question.question_type == "counterfactual":
                enhanced_text = self._enhance_counterfactual_question(question, node)
            elif question.question_type == "stakeholder":
                enhanced_text = self._enhance_stakeholder_question(question, node)
            elif question.question_type == "stress_test":
                enhanced_text = self._enhance_stress_test_question(question, node)
        
        return AdversarialQuestion(
            question_type=question.question_type,
            question_text=enhanced_text,
            target_node_id=question.target_node_id,
            bias_type=question.bias_type,
            intensity=question.intensity,
            expected_response_type=question.expected_response_type
        )
    
    def _enhance_counterfactual_question(self, question: AdversarialQuestion, node: Any) -> str:
        """增强反事实问题"""
        base_text = question.question_text
        
        if "假设" in node.content or "前提" in node.content:
            return f"如果 {node.content} 完全错误，你的整个决策链条会如何崩塌？请描述具体的连锁反应。"
        
        return base_text
    
    def _enhance_stakeholder_question(self, question: AdversarialQuestion, node: Any) -> str:
        """增强异见者问题"""
        base_text = question.question_text
        
        # 识别可能的利益相关方
        stakeholders = self._identify_stakeholders(node.content)
        if stakeholders:
            stakeholder = stakeholders[0]
            return f"作为受此决策影响的 {stakeholder}，我要问：{base_text}"
        
        return base_text
    
    def _enhance_stress_test_question(self, question: AdversarialQuestion, node: Any) -> str:
        """增强压力测试问题"""
        base_text = question.question_text
        
        if node.node_type == "evidence" and node.evidence_strength:
            return f"在什么极端条件下，你的证据强度会从 {node.evidence_strength} 降到 0.1 以下？请给出具体的证伪方案。"
        
        return base_text
    
    def _identify_stakeholders(self, content: str) -> List[str]:
        """识别利益相关方"""
        stakeholders = []
        content_lower = content.lower()
        
        stakeholder_keywords = {
            "客户": ["客户", "用户", "消费者"],
            "员工": ["员工", "职员", "工作者"],
            "股东": ["股东", "投资者", "持股人"],
            "供应商": ["供应商", "合作伙伴", "承包商"],
            "监管机构": ["监管", "政府", "法规"],
            "社区": ["社区", "公众", "社会"]
        }
        
        for stakeholder, keywords in stakeholder_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                stakeholders.append(stakeholder)
        
        return stakeholders
    
    def evaluate_response_quality(self, response: str, question: AdversarialQuestion) -> Dict[str, Any]:
        """评估回应质量"""
        evaluation = {
            "completeness": 0.0,  # 完整性
            "specificity": 0.0,   # 具体性
            "defensiveness": 0.0, # 防御性
            "bias_acknowledgment": 0.0  # 偏误承认程度
        }
        
        # 简单的内容分析
        response_lower = response.lower()
        
        # 完整性评估
        if len(response.split()) > 20:  # 超过20个词
            evaluation["completeness"] = 0.8
        elif len(response.split()) > 10:
            evaluation["completeness"] = 0.5
        else:
            evaluation["completeness"] = 0.2
        
        # 具体性评估
        specific_indicators = ["具体", "例如", "比如", "数据", "证据"]
        if any(indicator in response_lower for indicator in specific_indicators):
            evaluation["specificity"] = 0.7
        
        # 防御性评估
        defensive_indicators = ["但是", "不过", "然而", "其实", "实际上"]
        defensive_count = sum(1 for indicator in defensive_indicators if indicator in response_lower)
        evaluation["defensiveness"] = min(1.0, defensive_count * 0.3)
        
        # 偏误承认评估
        acknowledgment_indicators = ["可能", "或许", "确实", "承认", "接受"]
        if any(indicator in response_lower for indicator in acknowledgment_indicators):
            evaluation["bias_acknowledgment"] = 0.6
        
        return evaluation
    
    def generate_followup_question(self, original_question: AdversarialQuestion, user_response: str) -> Optional[AdversarialQuestion]:
        """生成跟进问题"""
        evaluation = self.evaluate_response_quality(user_response, original_question)
        
        # 如果回应质量较低，生成跟进问题
        if evaluation["completeness"] < 0.5 or evaluation["specificity"] < 0.3:
            followup_text = f"你的回应似乎不够具体。能否更详细地解释：{original_question.question_text}"
            
            return AdversarialQuestion(
                question_type=original_question.question_type,
                question_text=followup_text,
                target_node_id=original_question.target_node_id,
                bias_type=original_question.bias_type,
                intensity="strong",
                expected_response_type="very_detailed"
            )
        
        return None