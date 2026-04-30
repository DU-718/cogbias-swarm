"""
Agent B 单元测试
测试偏误模式匹配引擎的功能
"""

import pytest
from unittest.mock import Mock, patch
from src.agents.agent_b import BiasPatternMatcher
from src.core.state import SessionState, DecisionTree, DecisionTreeNode, BiasReport, BiasDetection


class TestBiasPatternMatcher:
    """偏误模式匹配引擎测试类"""
    
    def setup_method(self):
        """测试设置"""
        self.mock_llm_client = Mock()
        self.config = {
            "agents": {
                "agent_b": {
                    "bias_threshold": 0.7,
                    "max_biases_per_node": 3
                }
            }
        }
        self.agent = BiasPatternMatcher(self.mock_llm_client, self.config)
    
    def test_initialization(self):
        """测试初始化"""
        assert self.agent.llm_client == self.mock_llm_client
        assert self.agent.config == self.config
        assert "认知偏误检测专家" in self.agent.system_prompt
        assert self.agent.bias_knowledge is not None
    
    def test_detect_biases_success(self):
        """测试成功检测偏误"""
        # 创建测试决策树
        decision_tree = DecisionTree(
            version=1,
            root_node_id="root",
            nodes={
                "root": DecisionTreeNode(
                    node_id="root",
                    node_type="conclusion",
                    content="投资这个项目会成功",
                    confidence=0.9
                ),
                "premise1": DecisionTreeNode(
                    node_id="premise1",
                    node_type="premise",
                    content="市场前景很好",
                    premise_type="assumption",
                    confidence=0.8,
                    parent_id="root"
                )
            },
            primary_conclusion="投资这个项目会成功"
        )
        
        # 模拟 LLM 响应
        mock_report_data = {
            "detected_biases": [
                {
                    "bias_type": "overconfidence_bias",
                    "node_id": "root",
                    "confidence": 0.8,
                    "reasoning": "置信度过高，缺乏充分证据",
                    "severity": "high",
                    "correction_question": "为什么你对成功如此自信？",
                    "evidence": ["高置信度", "缺乏验证"]
                }
            ],
            "overall_risk_score": 0.7,
            "risk_heatmap": {"root": 0.8, "premise1": 0.3},
            "recommendations": ["建议进行更全面的风险评估"]
        }
        
        self.mock_llm_client.generate_json.return_value = mock_report_data
        
        state = SessionState(user_input="测试输入", decision_tree=decision_tree)
        result_state = self.agent.run(state)
        
        assert result_state.bias_report is not None
        assert len(result_state.bias_report.detected_biases) == 1
        assert result_state.bias_report.detected_biases[0].bias_type == "overconfidence_bias"
        assert result_state.bias_report.overall_risk_score == 0.7
    
    def test_detect_biases_fallback(self):
        """测试检测偏误失败时的回退机制"""
        decision_tree = DecisionTree(
            version=1,
            root_node_id="root",
            nodes={
                "root": DecisionTreeNode(
                    node_id="root",
                    node_type="conclusion",
                    content="测试结论",
                    confidence=0.9
                )
            },
            primary_conclusion="测试结论"
        )
        
        self.mock_llm_client.generate_json.side_effect = Exception("检测失败")
        
        state = SessionState(user_input="测试输入", decision_tree=decision_tree)
        result_state = self.agent.run(state)
        
        # 应该返回回退报告
        assert result_state.bias_report is not None
        assert result_state.bias_report.overall_risk_score >= 0.0
    
    def test_prepare_node_details(self):
        """测试准备节点详情信息"""
        decision_tree = DecisionTree(
            version=1,
            root_node_id="root",
            nodes={
                "root": DecisionTreeNode(
                    node_id="root",
                    node_type="conclusion",
                    content="结论内容",
                    confidence=0.8,
                    children_ids=["premise1"]
                ),
                "premise1": DecisionTreeNode(
                    node_id="premise1",
                    node_type="premise",
                    content="前提内容",
                    premise_type="fact",
                    confidence=0.9,
                    parent_id="root"
                )
            },
            primary_conclusion="主要结论"
        )
        
        details = self.agent._prepare_node_details(decision_tree)
        
        assert "节点 root:" in details
        assert "类型: conclusion" in details
        assert "节点 premise1:" in details
        assert "前提类型: fact" in details
    
    def test_analyze_bias_patterns(self):
        """测试分析偏误模式"""
        decision_tree = DecisionTree(
            version=1,
            root_node_id="root",
            nodes={
                "root": DecisionTreeNode(
                    node_id="root",
                    node_type="conclusion",
                    content="这个决策绝对正确",
                    confidence=0.95
                ),
                "evidence1": DecisionTreeNode(
                    node_id="evidence1",
                    node_type="evidence",
                    content="所有证据都支持这个结论",
                    evidence_strength=0.9,
                    reasoning_type="inductive",
                    parent_id="root"
                )
            },
            primary_conclusion="这个决策绝对正确"
        )
        
        patterns = self.agent.analyze_bias_patterns(decision_tree)
        
        assert "confirmation_bias_patterns" in patterns
        assert "overconfidence_patterns" in patterns
        # 具体模式检测可能因实现而异
    
    def test_generate_risk_heatmap(self):
        """测试生成风险热力图"""
        decision_tree = DecisionTree(
            version=1,
            root_node_id="root",
            nodes={
                "root": DecisionTreeNode(node_id="root", node_type="conclusion", content="结论"),
                "node1": DecisionTreeNode(node_id="node1", node_type="premise", content="前提1"),
                "node2": DecisionTreeNode(node_id="node2", node_type="premise", content="前提2")
            },
            primary_conclusion="结论"
        )
        
        bias_report = BiasReport(
            iteration=1,
            detected_biases=[
                BiasDetection(
                    bias_type="confirmation_bias",
                    node_id="root",
                    confidence=0.8,
                    reasoning="测试",
                    severity="high",
                    correction_question="测试"
                ),
                BiasDetection(
                    bias_type="anchoring_bias",
                    node_id="node1",
                    confidence=0.6,
                    reasoning="测试",
                    severity="medium",
                    correction_question="测试"
                )
            ],
            overall_risk_score=0.7,
            risk_heatmap={},
            recommendations=[]
        )
        
        heatmap = self.agent.generate_risk_heatmap(decision_tree, bias_report)
        
        assert "root" in heatmap
        assert "node1" in heatmap
        assert "node2" in heatmap
        assert 0.0 <= heatmap["root"] <= 1.0
        assert 0.0 <= heatmap["node1"] <= 1.0
        assert heatmap["node2"] == 0.0  # 没有检测到偏误的节点
    
    def test_bias_knowledge_integration(self):
        """测试偏误知识库集成"""
        # 测试知识库的基本功能
        knowledge_base = self.agent.bias_knowledge
        
        # 测试获取偏误信息
        bias_info = knowledge_base.get_bias("confirmation_bias")
        assert bias_info["name"] == "确认偏误"
        assert "category" in bias_info
        
        # 测试按类别获取偏误
        cognitive_biases = knowledge_base.get_biases_by_category("cognitive")
        assert len(cognitive_biases) > 0
        
        # 测试获取所有偏误
        all_biases = knowledge_base.get_all_biases()
        assert len(all_biases) >= 20  # 至少20种偏误
    
    def test_empty_decision_tree_handling(self):
        """测试空决策树处理"""
        state = SessionState(user_input="测试输入")  # 没有决策树
        
        result_state = self.agent.run(state)
        
        # 应该跳过检测，状态不变
        assert result_state.bias_report is None
        
    @patch('src.agents.agent_b.logger')
    def test_invalid_node_reference_handling(self, mock_logger):
        """测试无效节点引用处理"""
        decision_tree = DecisionTree(
            version=1,
            root_node_id="root",
            nodes={
                "root": DecisionTreeNode(
                    node_id="root",
                    node_type="conclusion",
                    content="结论"
                )
            },
            primary_conclusion="结论"
        )
        
        # 模拟包含无效节点引用的报告
        mock_report_data = {
            "detected_biases": [
                {
                    "bias_type": "test_bias",
                    "node_id": "nonexistent_node",  # 不存在的节点
                    "confidence": 0.8,
                    "reasoning": "测试",
                    "severity": "medium",
                    "correction_question": "测试"
                }
            ],
            "overall_risk_score": 0.5,
            "risk_heatmap": {},
            "recommendations": []
        }
        
        self.mock_llm_client.generate_json.return_value = mock_report_data
        
        state = SessionState(user_input="测试输入", decision_tree=decision_tree)
        result_state = self.agent.run(state)
        
        # 应该记录警告但继续处理
        mock_logger.warning.assert_called()
        # 无效节点引用应该被过滤掉
        assert len(result_state.bias_report.detected_biases) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])