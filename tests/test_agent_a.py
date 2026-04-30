"""
Agent A 单元测试
测试决策构建追踪器的功能
"""

import pytest
from unittest.mock import Mock, patch
from src.agents.agent_a import DecisionTreeBuilder
from src.core.state import SessionState, DecisionTree, DecisionTreeNode


class TestDecisionTreeBuilder:
    """决策构建追踪器测试类"""
    
    def setup_method(self):
        """测试设置"""
        self.mock_llm_client = Mock()
        self.config = {
            "agents": {
                "agent_a": {
                    "max_iterations": 5,
                    "validation_strictness": "high"
                }
            }
        }
        self.agent = DecisionTreeBuilder(self.mock_llm_client, self.config)
    
    def test_initialization(self):
        """测试初始化"""
        assert self.agent.llm_client == self.mock_llm_client
        assert self.agent.config == self.config
        assert "决策分析专家" in self.agent.system_prompt
    
    def test_build_initial_tree_success(self):
        """测试成功构建初始决策树"""
        # 模拟 LLM 响应
        mock_tree_data = {
            "version": 1,
            "root_node_id": "root",
            "primary_conclusion": "测试结论",
            "nodes": {
                "root": {
                    "node_type": "conclusion",
                    "content": "根节点内容",
                    "confidence": 0.8,
                    "children_ids": ["premise1"]
                },
                "premise1": {
                    "node_type": "premise",
                    "content": "前提内容",
                    "premise_type": "fact",
                    "confidence": 0.9,
                    "parent_id": "root"
                }
            }
        }
        
        self.mock_llm_client.generate_json.return_value = mock_tree_data
        
        user_input = "测试决策描述"
        tree = self.agent._build_initial_tree(user_input)
        
        assert tree.version == 1
        assert tree.primary_conclusion == "测试结论"
        assert "root" in tree.nodes
        assert "premise1" in tree.nodes
        assert tree.nodes["root"].node_type == "conclusion"
    
    def test_build_initial_tree_failure(self):
        """测试构建初始决策树失败情况"""
        self.mock_llm_client.generate_json.side_effect = Exception("LLM 调用失败")
        
        user_input = "测试决策描述"
        tree = self.agent._build_initial_tree(user_input)
        
        # 应该返回回退树
        assert tree.version == 1
        assert tree.primary_conclusion == user_input
        assert "root" in tree.nodes
    
    def test_update_tree_with_user_response(self):
        """测试根据用户回应更新决策树"""
        # 创建初始状态
        initial_tree = DecisionTree(
            version=1,
            root_node_id="root",
            nodes={
                "root": DecisionTreeNode(
                    node_id="root",
                    node_type="conclusion",
                    content="初始结论",
                    confidence=0.8
                )
            },
            primary_conclusion="初始结论"
        )
        
        state = SessionState(
            user_input="测试输入",
            decision_tree=initial_tree,
            iteration_count=1
        )
        
        # 添加用户回应
        from src.core.state import UserResponse, AdversarialQuestion
        
        question = AdversarialQuestion(
            question_type="counterfactual",
            question_text="测试问题",
            target_node_id="root",
            bias_type="confirmation_bias"
        )
        
        response = UserResponse(
            question_id=question.question_id,
            response_text="用户回应内容"
        )
        
        state.adversarial_questions = [question]
        state.user_responses = [response]
        
        # 模拟 LLM 更新响应
        updated_tree_data = {
            "version": 2,
            "root_node_id": "root",
            "primary_conclusion": "更新后的结论",
            "nodes": {
                "root": {
                    "node_type": "conclusion",
                    "content": "更新后的内容",
                    "confidence": 0.7,
                    "children_ids": []
                }
            }
        }
        
        self.mock_llm_client.generate_json.return_value = updated_tree_data
        
        updated_state = self.agent.run(state)
        
        assert updated_state.decision_tree.version == 2
        assert updated_state.iteration_count == 2
        assert updated_state.decision_tree.primary_conclusion == "更新后的结论"
    
    def test_validate_tree_structure(self):
        """测试决策树结构验证"""
        # 有效树
        valid_tree = DecisionTree(
            version=1,
            root_node_id="root",
            nodes={
                "root": DecisionTreeNode(
                    node_id="root",
                    node_type="conclusion",
                    content="根节点",
                    children_ids=["child1"]
                ),
                "child1": DecisionTreeNode(
                    node_id="child1",
                    node_type="premise",
                    content="子节点",
                    parent_id="root"
                )
            },
            primary_conclusion="测试"
        )
        
        assert self.agent.validate_tree_structure(valid_tree) == True
        
        # 无效树（节点不连通）
        invalid_tree = DecisionTree(
            version=1,
            root_node_id="root",
            nodes={
                "root": DecisionTreeNode(
                    node_id="root",
                    node_type="conclusion",
                    content="根节点"
                ),
                "isolated": DecisionTreeNode(
                    node_id="isolated",
                    node_type="premise",
                    content="孤立节点"
                )
            },
            primary_conclusion="测试"
        )
        
        assert self.agent.validate_tree_structure(invalid_tree) == False
    
    def test_get_tree_summary(self):
        """测试获取决策树摘要"""
        tree = DecisionTree(
            version=1,
            root_node_id="root",
            nodes={
                "root": DecisionTreeNode(
                    node_id="root",
                    node_type="conclusion",
                    content="结论",
                    confidence=0.8
                ),
                "premise1": DecisionTreeNode(
                    node_id="premise1",
                    node_type="premise",
                    content="前提1",
                    premise_type="fact",
                    confidence=0.9,
                    parent_id="root"
                ),
                "premise2": DecisionTreeNode(
                    node_id="premise2",
                    node_type="premise",
                    content="前提2",
                    premise_type="assumption",
                    confidence=0.6,
                    parent_id="root"
                )
            },
            primary_conclusion="主要结论"
        )
        
        summary = self.agent.get_tree_summary(tree)
        
        assert summary["total_nodes"] == 3
        assert summary["node_type_distribution"]["premise"] == 2
        assert summary["node_type_distribution"]["conclusion"] == 1
        assert summary["assumption_count"] == 1
        assert 0.7 <= summary["average_confidence"] <= 0.8
        assert summary["primary_conclusion"] == "主要结论"
    
    @patch('src.agents.agent_a.logger')
    def test_json_parsing_error_handling(self, mock_logger):
        """测试 JSON 解析错误处理"""
        # 模拟格式错误的 JSON 响应
        self.mock_llm_client.generate_json.side_effect = [
            Exception("JSON 解析错误"),  # 第一次失败
            {
                "version": 1,
                "root_node_id": "root",
                "primary_conclusion": "修复后的结论",
                "nodes": {
                    "root": {
                        "node_type": "conclusion",
                        "content": "修复内容",
                        "confidence": 0.8
                    }
                }
            }  # 第二次成功
        ]
        
        # 模拟修复方法
        with patch.object(self.agent, '_fix_json') as mock_fix:
            mock_fix.return_value = {
                "version": 1,
                "root_node_id": "root",
                "primary_conclusion": "修复后的结论",
                "nodes": {
                    "root": {
                        "node_type": "conclusion",
                        "content": "修复内容",
                        "confidence": 0.8
                    }
                }
            }
            
            user_input = "测试输入"
            tree = self.agent._build_initial_tree(user_input)
            
            # 验证日志记录
            mock_logger.warning.assert_called()
            assert tree.primary_conclusion == "修复后的结论"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])