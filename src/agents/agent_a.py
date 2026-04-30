"""
Agent A - 决策构建追踪器 (Decision Tree Builder)
功能：解析用户输入的自然语言决策描述，构建结构化决策树
"""

import logging
import json
from typing import Dict, Any, Optional
from ..core.state import DecisionTree, DecisionTreeNode, SessionState
from ..utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class DecisionTreeBuilder:
    """决策构建追踪器 Agent"""
    
    def __init__(self, llm_client: LLMClient, config: Dict[str, Any]):
        """
        初始化决策构建追踪器
        
        Args:
            llm_client: LLM 客户端
            config: Agent 配置
        """
        self.llm_client = llm_client
        self.config = config
        
        # 内置提示词
        self.system_prompt = """你是一个专业的决策分析专家，擅长将自然语言决策描述解析为结构化的决策树。

你的任务是将用户提供的决策问题或描述，分解为清晰的逻辑结构，包括：
1. 前提（Premises） - 区分事实和假设
2. 证据链（Evidence Chain） - 包含推理类型和强度
3. 结论（Conclusions） - 各级结论和最终主要结论

请严格按照 JSON 格式输出，确保逻辑严谨、结构清晰。"""
        
        self.update_prompt = """你是一个决策树更新专家，负责根据用户对对抗性问题的回应来修正决策树。

当前决策树：
{current_tree}

用户回应：
{user_response}

对抗性问题背景：
{question_context}

请分析用户回应，识别需要修正的节点，更新决策树结构，并确保：
1. 保留有效的原有结构
2. 修正被挑战的假设或推理
3. 更新相关节点的置信度
4. 保持逻辑一致性

返回更新后的完整决策树。"""
    
    def run(self, state: SessionState) -> SessionState:
        """
        执行决策树构建或更新
        
        Args:
            state: 当前会话状态
            
        Returns:
            更新后的会话状态
        """
        logger.info(f"Agent A 开始处理，迭代: {state.iteration_count}")
        
        if state.iteration_count == 0:
            # 初始构建
            decision_tree = self._build_initial_tree(state.user_input)
        else:
            # 增量更新
            decision_tree = self._update_tree(state)
        
        state.decision_tree = decision_tree
        state.iteration_count += 1
        state.add_message("agent_a", "决策树构建完成", {"version": decision_tree.version})
        
        logger.info(f"Agent A 完成，决策树版本: {decision_tree.version}")
        return state
    
    def _build_initial_tree(self, user_input: str) -> DecisionTree:
        """构建初始决策树"""
        prompt = f"""
请将以下决策描述解析为结构化的决策树：

用户输入：{user_input}

请返回严格的 JSON 格式，包含以下结构：
{{
    "version": 1,
    "root_node_id": "根节点ID",
    "primary_conclusion": "主要结论",
    "nodes": {{
        "node_id": {{
            "node_type": "premise|evidence|conclusion",
            "content": "节点内容",
            "premise_type": "fact|assumption" (仅 premise 类型需要),
            "evidence_strength": 0.0-1.0 (仅 evidence 类型需要),
            "reasoning_type": "deductive|inductive|abductive" (仅 evidence 类型需要),
            "parent_id": "父节点ID",
            "children_ids": ["子节点ID列表"],
            "confidence": 0.0-1.0,
            "tags": ["标签列表"]
        }}
    }}
}}

要求：
1. 根节点应为最高层级的结论
2. 每个前提节点必须标注是事实还是假设
3. 证据节点必须包含推理类型和强度评估
4. 保持逻辑层次清晰"""
        
        try:
            tree_data = self.llm_client.generate_json(prompt, self.system_prompt)
            return self._validate_and_convert_tree(tree_data)
        except Exception as e:
            logger.error(f"初始决策树构建失败: {e}")
            # 返回一个基本的决策树结构
            return self._create_fallback_tree(user_input)
    
    def _update_tree(self, state: SessionState) -> DecisionTree:
        """更新决策树"""
        if not state.decision_tree:
            logger.warning("没有现有决策树，进行初始构建")
            return self._build_initial_tree(state.user_input)
        
        latest_response = state.get_latest_user_response()
        if not latest_response:
            logger.warning("没有用户回应，返回原决策树")
            return state.decision_tree
        
        # 找到相关的对抗性问题
        related_question = None
        for question in state.adversarial_questions:
            if question.question_id == latest_response.question_id:
                related_question = question
                break
        
        if not related_question:
            logger.warning("未找到相关问题，返回原决策树")
            return state.decision_tree
        
        prompt = self.update_prompt.format(
            current_tree=state.decision_tree.json(),
            user_response=latest_response.response_text,
            question_context={
                "question_type": related_question.question_type,
                "question_text": related_question.question_text,
                "target_node": related_question.target_node_id,
                "bias_type": related_question.bias_type
            }
        )
        
        try:
            tree_data = self.llm_client.generate_json(prompt, self.system_prompt)
            updated_tree = self._validate_and_convert_tree(tree_data)
            # 更新版本号
            updated_tree.version = state.decision_tree.version + 1
            return updated_tree
        except Exception as e:
            logger.error(f"决策树更新失败: {e}")
            # 更新失败时返回原树
            return state.decision_tree
    
    def _validate_and_convert_tree(self, tree_data: Dict[str, Any]) -> DecisionTree:
        """验证并转换决策树数据"""
        # 基本验证
        required_fields = ["version", "root_node_id", "primary_conclusion", "nodes"]
        for field in required_fields:
            if field not in tree_data:
                raise ValueError(f"缺失必要字段: {field}")
        
        # 转换节点数据
        nodes = {}
        for node_id, node_data in tree_data["nodes"].items():
            # 验证节点数据
            if "node_type" not in node_data or "content" not in node_data:
                raise ValueError(f"节点 {node_id} 数据不完整")
            
            # 创建 DecisionTreeNode
            node = DecisionTreeNode(
                node_id=node_id,
                node_type=node_data["node_type"],
                content=node_data["content"],
                premise_type=node_data.get("premise_type"),
                evidence_strength=node_data.get("evidence_strength"),
                reasoning_type=node_data.get("reasoning_type"),
                parent_id=node_data.get("parent_id"),
                children_ids=node_data.get("children_ids", []),
                confidence=node_data.get("confidence", 1.0),
                tags=node_data.get("tags", [])
            )
            nodes[node_id] = node
        
        # 创建 DecisionTree
        return DecisionTree(
            version=tree_data["version"],
            root_node_id=tree_data["root_node_id"],
            nodes=nodes,
            primary_conclusion=tree_data["primary_conclusion"]
        )
    
    def _create_fallback_tree(self, user_input: str) -> DecisionTree:
        """创建回退决策树"""
        root_node = DecisionTreeNode(
            node_id="root",
            node_type="conclusion",
            content=f"基于输入的决策: {user_input}",
            confidence=0.5
        )
        
        return DecisionTree(
            version=1,
            root_node_id="root",
            nodes={"root": root_node},
            primary_conclusion=user_input
        )
    
    def validate_tree_structure(self, tree: DecisionTree) -> bool:
        """验证决策树结构有效性"""
        if not tree.root_node_id or tree.root_node_id not in tree.nodes:
            return False
        
        # 检查节点连通性
        visited = set()
        
        def traverse(node_id: str):
            if node_id in visited or node_id not in tree.nodes:
                return
            visited.add(node_id)
            node = tree.nodes[node_id]
            for child_id in node.children_ids:
                traverse(child_id)
        
        traverse(tree.root_node_id)
        
        # 所有节点都应该可以从根节点到达
        return len(visited) == len(tree.nodes)
    
    def get_tree_summary(self, tree: DecisionTree) -> Dict[str, Any]:
        """获取决策树摘要"""
        if not tree:
            return {}
        
        node_counts = {"premise": 0, "evidence": 0, "conclusion": 0}
        assumption_count = 0
        avg_confidence = 0.0
        
        for node in tree.nodes.values():
            node_counts[node.node_type] += 1
            if node.node_type == "premise" and node.premise_type == "assumption":
                assumption_count += 1
            avg_confidence += node.confidence
        
        if len(tree.nodes) > 0:
            avg_confidence /= len(tree.nodes)
        
        return {
            "total_nodes": len(tree.nodes),
            "node_type_distribution": node_counts,
            "assumption_count": assumption_count,
            "average_confidence": round(avg_confidence, 2),
            "tree_depth": self._calculate_tree_depth(tree),
            "primary_conclusion": tree.primary_conclusion
        }
    
    def _calculate_tree_depth(self, tree: DecisionTree) -> int:
        """计算决策树深度"""
        if not tree.nodes:
            return 0
        
        def get_depth(node_id: str, current_depth: int) -> int:
            node = tree.nodes[node_id]
            if not node.children_ids:
                return current_depth
            
            max_depth = current_depth
            for child_id in node.children_ids:
                if child_id in tree.nodes:
                    depth = get_depth(child_id, current_depth + 1)
                    max_depth = max(max_depth, depth)
            
            return max_depth
        
        return get_depth(tree.root_node_id, 1)