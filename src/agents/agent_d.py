"""
Agent D - 元认知记录与校准引擎 (Meta-Cognition Recorder)
功能：记录会话历史，生成审计报告，管理数据持久化
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..core.state import SessionState, AuditReport, DecisionTree, BiasReport, UserResponse
from ..db.repository import Repository
from ..utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class MetaCognitionRecorder:
    """元认知记录与校准引擎 Agent"""
    
    def __init__(self, llm_client: LLMClient, repository: Repository, config: Dict[str, Any]):
        """
        初始化元认知记录器
        
        Args:
            llm_client: LLM 客户端
            repository: 数据仓库
            config: Agent 配置
        """
        self.llm_client = llm_client
        self.repository = repository
        self.config = config
        
        # 内置提示词
        self.system_prompt = """你是一个专业的认知审计专家，负责分析决策过程中的元认知模式。

你的任务：
1. 分析决策演变轨迹
2. 识别个人偏误指纹
3. 生成改进建议
4. 创建全面的审计报告

请基于完整的历史数据，提供深入的分析和建设性建议。"""
        
        self.audit_prompt = """
基于以下完整的会话历史，生成认知纠偏审计报告：

会话基本信息：
- 会话ID: {session_id}
- 初始决策问题: {initial_input}
- 总迭代次数: {iteration_count}
- 会话时长: {session_duration}

决策演变历史：
{decision_evolution}

偏误暴露情况：
{bias_exposure}

用户回应分析：
{response_analysis}

请生成包含以下部分的详细审计报告：

1. 决策演变摘要
   - 初始决策 vs 最终决策
   - 关键修正点分析
   - 学习轨迹总结

2. 偏误暴露清单
   - 检测到的偏误类型及频率
   - 偏误处理状态（接受/抵触/忽略）
   - 系统性偏误模式识别

3. 个人偏误指纹
   - 本次会话的偏误特征
   - 与历史模式的对比（如有）
   - 认知弱点分析

4. 改进建议
   - 针对性的决策改进策略
   - 认知偏误防范措施
   - 下次决策预警提示

请返回严格的 JSON 格式：
{{
    "decision_evolution": {{
        "initial_conclusion": "初始结论",
        "final_conclusion": "最终结论",
        "key_changes": ["关键变化1", "关键变化2"],
        "learning_trajectory": "学习轨迹描述"
    }},
    "bias_exposure": {{
        "bias_types_detected": ["偏误类型1", "偏误类型2"],
        "bias_frequency": {{"偏误类型": 次数}},
        "response_patterns": {{"接受": 次数, "抵触": 次数, "忽略": 次数}},
        "systematic_patterns": ["系统性模式1"]
    }},
    "bias_fingerprint": {{
        "dominant_biases": ["主要偏误类型"],
        "cognitive_weaknesses": ["认知弱点"],
        "improvement_areas": ["改进领域"]
    }},
    "recommendations": ["建议1", "建议2", "建议3"],
    "summary": "报告摘要"
}}
"""
    
    def run(self, state: SessionState) -> SessionState:
        """
        执行元认知记录和审计报告生成
        
        Args:
            state: 当前会话状态
            
        Returns:
            更新后的会话状态
        """
        logger.info(f"Agent D 开始生成审计报告，会话: {state.session_id}")
        
        # 保存会话数据到数据库
        self._persist_session_data(state)
        
        # 生成审计报告
        audit_report = self._generate_audit_report(state)
        
        # 更新会话状态
        state.status = "completed"
        state.add_message("agent_d", "审计报告生成完成", {
            "report_generated": True,
            "bias_fingerprint_identified": len(audit_report.bias_fingerprint.get("dominant_biases", [])) > 0
        })
        
        logger.info(f"Agent D 完成，审计报告已生成")
        return state
    
    def _persist_session_data(self, state: SessionState):
        """持久化会话数据"""
        try:
            # 创建或获取会话记录
            session = self.repository.get_session_by_id(state.session_id)
            if not session:
                session = self.repository.create_session(state.session_id, state.user_input)
            
            # 保存决策树
            if state.decision_tree:
                self.repository.save_decision_tree(
                    state.session_id, 
                    state.decision_tree.dict(),
                    state.decision_tree.version
                )
            
            # 保存偏误报告
            if state.bias_report:
                self.repository.save_bias_report(
                    state.session_id,
                    state.bias_report.dict(),
                    state.iteration_count
                )
            
            # 保存对抗性问题和用户回应
            for i, question in enumerate(state.adversarial_questions):
                db_question = self.repository.save_adversarial_question(
                    state.session_id,
                    state.iteration_count,
                    question.question_type,
                    question.question_text,
                    question.target_node_id,
                    question.bias_type
                )
                
                # 保存对应的用户回应
                for response in state.user_responses:
                    if response.question_id == question.question_id:
                        self.repository.save_user_response(
                            db_question.id,
                            response.response_text,
                            response.bias_acknowledged,
                            response.response_type
                        )
            
            # 更新会话状态
            self.repository.update_session_status(state.session_id, state.status)
            
        except Exception as e:
            logger.error(f"数据持久化失败: {e}")
    
    def _generate_audit_report(self, state: SessionState) -> AuditReport:
        """生成审计报告"""
        # 准备分析数据
        analysis_data = self._prepare_analysis_data(state)
        
        prompt = self.audit_prompt.format(
            session_id=state.session_id,
            initial_input=state.user_input,
            iteration_count=state.iteration_count,
            session_duration=self._calculate_session_duration(state),
            decision_evolution=analysis_data["decision_evolution"],
            bias_exposure=analysis_data["bias_exposure"],
            response_analysis=analysis_data["response_analysis"]
        )
        
        try:
            report_data = self.llm_client.generate_json(prompt, self.system_prompt)
            return self._validate_and_convert_report(report_data, state)
        except Exception as e:
            logger.error(f"审计报告生成失败: {e}")
            return self._create_fallback_report(state)
    
    def _prepare_analysis_data(self, state: SessionState) -> Dict[str, str]:
        """准备分析数据"""
        # 决策演变分析
        decision_evolution = self._analyze_decision_evolution(state)
        
        # 偏误暴露分析
        bias_exposure = self._analyze_bias_exposure(state)
        
        # 用户回应分析
        response_analysis = self._analyze_user_responses(state)
        
        return {
            "decision_evolution": decision_evolution,
            "bias_exposure": bias_exposure,
            "response_analysis": response_analysis
        }
    
    def _analyze_decision_evolution(self, state: SessionState) -> str:
        """分析决策演变"""
        analysis = []
        
        if state.decision_tree:
            analysis.append(f"最终结论: {state.decision_tree.primary_conclusion}")
            analysis.append(f"决策树节点数: {len(state.decision_tree.nodes)}")
            analysis.append(f"平均置信度: {self._calculate_average_confidence(state.decision_tree):.2f}")
        
        if state.iteration_count > 1:
            analysis.append(f"经过 {state.iteration_count - 1} 次修正迭代")
        
        return "\n".join(analysis)
    
    def _analyze_bias_exposure(self, state: SessionState) -> str:
        """分析偏误暴露情况"""
        analysis = []
        
        if state.bias_report:
            bias_types = {}
            for bias in state.bias_report.detected_biases:
                bias_types[bias.bias_type] = bias_types.get(bias.bias_type, 0) + 1
            
            analysis.append(f"检测到 {len(state.bias_report.detected_biases)} 个偏误实例")
            analysis.append(f"涉及 {len(bias_types)} 种偏误类型")
            analysis.append(f"总体风险评分: {state.bias_report.overall_risk_score:.2f}")
            
            # 最频繁的偏误
            if bias_types:
                most_frequent = max(bias_types.items(), key=lambda x: x[1])
                analysis.append(f"最频繁偏误: {most_frequent[0]} ({most_frequent[1]}次)")
        
        return "\n".join(analysis)
    
    def _analyze_user_responses(self, state: SessionState) -> str:
        """分析用户回应"""
        analysis = []
        
        if state.user_responses:
            response_types = {}
            bias_acknowledged = 0
            
            for response in state.user_responses:
                response_types[response.response_type] = response_types.get(response.response_type, 0) + 1
                if response.bias_acknowledged:
                    bias_acknowledged += 1
            
            analysis.append(f"总回应数: {len(state.user_responses)}")
            analysis.append(f"偏误承认率: {bias_acknowledged/len(state.user_responses)*100:.1f}%")
            analysis.append(f"回应类型分布: {dict(response_types)}")
        
        return "\n".join(analysis)
    
    def _calculate_session_duration(self, state: SessionState) -> str:
        """计算会话时长"""
        duration = datetime.now() - state.created_at
        hours = duration.total_seconds() / 3600
        
        if hours < 1:
            minutes = hours * 60
            return f"{minutes:.0f} 分钟"
        else:
            return f"{hours:.1f} 小时"
    
    def _calculate_average_confidence(self, decision_tree: DecisionTree) -> float:
        """计算平均置信度"""
        if not decision_tree.nodes:
            return 0.0
        
        total_confidence = sum(node.confidence for node in decision_tree.nodes.values())
        return total_confidence / len(decision_tree.nodes)
    
    def _validate_and_convert_report(self, report_data: Dict[str, Any], state: SessionState) -> AuditReport:
        """验证并转换审计报告数据"""
        required_sections = ["decision_evolution", "bias_exposure", "bias_fingerprint", "recommendations", "summary"]
        
        for section in required_sections:
            if section not in report_data:
                raise ValueError(f"审计报告缺失必要部分: {section}")
        
        # 创建审计报告
        return AuditReport(
            session_id=state.session_id,
            decision_evolution=report_data["decision_evolution"],
            bias_exposure=report_data["bias_exposure"],
            bias_fingerprint=report_data["bias_fingerprint"],
            recommendations=report_data["recommendations"],
            summary=report_data["summary"]
        )
    
    def _create_fallback_report(self, state: SessionState) -> AuditReport:
        """创建回退审计报告"""
        return AuditReport(
            session_id=state.session_id,
            decision_evolution=[{
                "initial_conclusion": state.user_input,
                "final_conclusion": state.decision_tree.primary_conclusion if state.decision_tree else "无",
                "key_changes": ["基础分析完成"],
                "learning_trajectory": "基础决策分析流程"
            }],
            bias_exposure={
                "bias_types_detected": [],
                "bias_frequency": {},
                "response_patterns": {"接受": 0, "抵触": 0, "忽略": 0},
                "systematic_patterns": []
            },
            bias_fingerprint={
                "dominant_biases": [],
                "cognitive_weaknesses": ["需要更深入分析"],
                "improvement_areas": ["建议使用完整版分析"]
            },
            recommendations=[
                "建议进行更全面的认知审计",
                "关注决策过程中的假设验证",
                "建立系统性的偏误防范机制"
            ],
            summary="基础审计报告 - 建议使用完整分析功能"
        )
    
    def get_session_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话历史"""
        return self.repository.get_session_history(session_id)
    
    def generate_bias_fingerprint(self, session_history: Dict[str, Any]) -> Dict[str, Any]:
        """生成偏误指纹"""
        fingerprint = {
            "bias_frequency": {},
            "response_patterns": {},
            "cognitive_tendencies": [],
            "improvement_timeline": []
        }
        
        # 分析偏误频率
        bias_reports = session_history.get("bias_reports", [])
        for report in bias_reports:
            report_data = report.report_data
            for bias in report_data.get("detected_biases", []):
                bias_type = bias.get("bias_type", "unknown")
                fingerprint["bias_frequency"][bias_type] = fingerprint["bias_frequency"].get(bias_type, 0) + 1
        
        # 分析回应模式
        questions = session_history.get("adversarial_questions", [])
        for question in questions:
            # 这里可以添加更复杂的模式分析
            pass
        
        return fingerprint
    
    def compare_with_historical_patterns(self, current_fingerprint: Dict[str, Any]) -> Dict[str, Any]:
        """与历史模式对比"""
        # 这里可以实现与历史数据的对比分析
        # 目前返回基础对比结果
        return {
            "comparison_available": False,
            "message": "历史数据对比功能待完善",
            "recommendations": ["建议积累更多会话数据以进行模式分析"]
        }
    
    def generate_improvement_plan(self, audit_report: AuditReport) -> Dict[str, Any]:
        """生成改进计划"""
        plan = {
            "short_term": [],
            "medium_term": [],
            "long_term": [],
            "immediate_actions": []
        }
        
        # 基于审计报告生成改进计划
        recommendations = audit_report.recommendations
        
        for i, recommendation in enumerate(recommendations[:3]):  # 取前3个建议
            if i == 0:
                plan["immediate_actions"].append(recommendation)
            elif i == 1:
                plan["short_term"].append(recommendation)
            else:
                plan["medium_term"].append(recommendation)
        
        # 添加长期改进项
        plan["long_term"].append("建立持续性的认知偏误监测机制")
        plan["long_term"].append("定期进行决策质量回顾和反思")
        
        return plan
    
    def export_report(self, audit_report: AuditReport, format: str = "json") -> str:
        """导出报告"""
        if format == "json":
            return audit_report.json(indent=2)
        elif format == "text":
            return self._format_text_report(audit_report)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def _format_text_report(self, audit_report: AuditReport) -> str:
        """格式化文本报告"""
        report_text = f"认知纠偏审计报告\n"
        report_text += f"=" * 50 + "\n\n"
        
        report_text += f"会话ID: {audit_report.session_id}\n"
        report_text += f"生成时间: {audit_report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 决策演变
        report_text += "1. 决策演变摘要\n"
        report_text += "-" * 30 + "\n"
        evolution = audit_report.decision_evolution
        report_text += f"初始结论: {evolution.get('initial_conclusion', 'N/A')}\n"
        report_text += f"最终结论: {evolution.get('final_conclusion', 'N/A')}\n"
        report_text += f"关键变化: {', '.join(evolution.get('key_changes', []))}\n\n"
        
        # 偏误暴露
        report_text += "2. 偏误暴露情况\n"
        report_text += "-" * 30 + "\n"
        exposure = audit_report.bias_exposure
        report_text += f"检测到的偏误类型: {', '.join(exposure.get('bias_types_detected', []))}\n"
        report_text += f"回应模式: {exposure.get('response_patterns', {})}\n\n"
        
        # 改进建议
        report_text += "3. 改进建议\n"
        report_text += "-" * 30 + "\n"
        for i, recommendation in enumerate(audit_report.recommendations, 1):
            report_text += f"{i}. {recommendation}\n"
        
        report_text += "\n" + "=" * 50 + "\n"
        report_text += f"报告摘要: {audit_report.summary}"
        
        return report_text