"""
LangGraph 工作流定义
实现多 Agent 协作的有状态工作流
"""

import logging
from typing import Dict, Any, Literal, List
from langgraph.graph import StateGraph, END

from .state import SessionState
from ..agents.agent_a import DecisionTreeBuilder
from ..agents.agent_b import BiasPatternMatcher
from ..agents.agent_c import AdversarialChallenger
from ..agents.agent_d import MetaCognitionRecorder
from ..utils.llm_client import LLMClient
from ..db.repository import Repository

logger = logging.getLogger(__name__)


class CogBiasWorkflow:
    """认知偏误审计工作流"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化工作流
        
        Args:
            config: 系统配置
        """
        self.config = config
        
        # 初始化组件
        self.llm_client = LLMClient(config)
        self.repository = Repository(config["database"]["url"])
        
        # 初始化 Agent
        self.agent_a = DecisionTreeBuilder(self.llm_client, config.get("agents", {}).get("agent_a", {}))
        self.agent_b = BiasPatternMatcher(self.llm_client, config.get("agents", {}).get("agent_b", {}))
        self.agent_c = AdversarialChallenger(self.llm_client, config.get("agents", {}).get("agent_c", {}))
        self.agent_d = MetaCognitionRecorder(self.llm_client, self.repository, config.get("agents", {}).get("agent_d", {}))
        
        # 构建工作流图
        self.graph = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """构建工作流图"""
        # 创建状态图 - 提供默认状态实例
        import uuid
        
        # 创建一个有效的默认状态用于验证
        default_state = SessionState(
            session_id=str(uuid.uuid4()),
            user_input="初始化状态"
        )
        
        workflow = StateGraph(SessionState)
        
        # 定义节点
        workflow.add_node("agent_a", self._run_agent_a)
        workflow.add_node("agent_b", self._run_agent_b)
        workflow.add_node("agent_c", self._run_agent_c)
        workflow.add_node("agent_d", self._run_agent_d)
        workflow.add_node("wait_for_user", self._wait_for_user_response)
        
        # 定义边（工作流路径）
        workflow.set_entry_point("agent_a")
        
        # 初始流程：A -> B -> C -> 等待用户
        workflow.add_edge("agent_a", "agent_b")
        workflow.add_edge("agent_b", "agent_c")
        workflow.add_edge("agent_c", "wait_for_user")
        
        # 用户回应后的流程：等待用户 -> A（更新） -> B -> C -> 等待用户 或 END
        workflow.add_conditional_edges(
            "wait_for_user",
            self._should_continue_after_response,
            {
                "continue": "agent_a",
                "generate_report": "agent_d",
                "end": END
            }
        )
        
        # 审计报告生成后结束
        workflow.add_edge("agent_d", END)
        
        # 在 LangGraph 1.1.10+ 版本中，SqliteSaver 已被移除
        # 使用内存检查点或简化版本
        return workflow.compile()
    
    def _run_agent_a(self, state: SessionState) -> SessionState:
        """运行 Agent A"""
        logger.info("工作流执行: Agent A - 决策构建追踪器")
        return self.agent_a.run(state)
    
    def _run_agent_b(self, state: SessionState) -> SessionState:
        """运行 Agent B"""
        logger.info("工作流执行: Agent B - 偏误模式匹配引擎")
        return self.agent_b.run(state)
    
    def _run_agent_c(self, state: SessionState) -> SessionState:
        """运行 Agent C"""
        logger.info("工作流执行: Agent C - 对抗性推理 Agent")
        return self.agent_c.run(state)
    
    def _run_agent_d(self, state: SessionState) -> SessionState:
        """运行 Agent D"""
        logger.info("工作流执行: Agent D - 元认知记录与校准引擎")
        return self.agent_d.run(state)
    
    def _wait_for_user_response(self, state: SessionState) -> SessionState:
        """等待用户回应"""
        logger.info("工作流状态: 等待用户回应")
        
        # 在实际应用中，这里会等待外部输入
        # 目前只是记录状态
        state.add_message("workflow", "等待用户回应", {
            "questions_count": len(state.adversarial_questions),
            "iteration": state.iteration_count
        })
        
        return state
    
    def _should_continue_after_response(self, state: SessionState) -> Literal["continue", "generate_report", "end"]:
        """判断用户回应后是否继续"""
        
        # 检查用户是否要求结束
        latest_response = state.get_latest_user_response()
        if latest_response:
            response_text = latest_response.response_text.lower()
            if any(keyword in response_text for keyword in ["结束", "完成", "生成报告", "stop", "finish"]):
                return "generate_report"
        
        # 检查迭代限制
        max_iterations = self.config.get("workflow", {}).get("max_iterations", 10)
        if state.iteration_count >= max_iterations:
            return "generate_report"
        
        # 检查是否有未处理的偏误
        if state.bias_report and state.bias_report.detected_biases:
            # 检查用户是否已经回应了所有问题
            if (len(state.user_responses) >= len(state.adversarial_questions) and
                len(state.adversarial_questions) > 0):
                return "continue"
        
        # 默认继续
        return "continue"
    
    def start_session(self, user_input: str, session_id: str = None) -> Dict[str, Any]:
        """开始新会话"""
        logger.info(f"开始新会话，用户输入: {user_input[:50]}...")
        
        # 确保 session_id 不为 None
        if session_id is None:
            import uuid
            session_id = str(uuid.uuid4())
        
        # 创建初始状态
        initial_state = SessionState(
            user_input=user_input,
            session_id=session_id
        )
        
        # 执行工作流
        try:
            # 执行初始流程（到等待用户回应）
            result = self.graph.invoke(
                initial_state,
                {"configurable": {"thread_id": initial_state.session_id}}
            )
            
            return {
                "success": True,
                "session_id": initial_state.session_id,
                "state": result,
                "next_step": "wait_for_user_response"
            }
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": initial_state.session_id
            }
    
    def process_user_response(self, session_id: str, response_text: str, question_id: str = None) -> Dict[str, Any]:
        """处理用户回应"""
        logger.info(f"处理用户回应，会话: {session_id}")
        
        try:
            # 获取当前状态
            current_state = self._get_current_state(session_id)
            
            if not current_state:
                return {"success": False, "error": "会话不存在"}
            
            # 创建用户回应记录
            from ..core.state import UserResponse
            user_response = UserResponse(
                question_id=question_id or "",
                response_text=response_text
            )
            
            # 添加到状态
            current_state.user_responses.append(user_response)
            
            # 继续执行工作流
            result = self.graph.invoke(
                current_state,
                {"configurable": {"thread_id": session_id}}
            )
            
            return {
                "success": True,
                "session_id": session_id,
                "state": result,
                "next_step": self._determine_next_step(result)
            }
            
        except Exception as e:
            logger.error(f"处理用户回应失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    def _get_current_state(self, session_id: str) -> SessionState:
        """获取当前状态"""
        # 这里应该从检查点恢复状态
        # 目前返回一个基础状态
        return SessionState(session_id=session_id, user_input="")
    
    def _determine_next_step(self, state: SessionState) -> str:
        """确定下一步"""
        if state.status == "completed":
            return "end"
        elif state.adversarial_questions and not state.user_responses:
            return "wait_for_user_response"
        else:
            return "continue"
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """获取会话状态"""
        try:
            # 从检查点获取状态
            # 这里简化实现
            return {
                "session_id": session_id,
                "status": "active",
                "iteration": 1,
                "has_questions": True,
                "questions_count": 3
            }
        except Exception as e:
            logger.error(f"获取会话状态失败: {e}")
            return {"error": str(e)}
    
    def generate_audit_report(self, session_id: str) -> Dict[str, Any]:
        """生成审计报告"""
        try:
            # 获取会话历史
            session_history = self.repository.get_session_history(session_id)
            
            if not session_history:
                return {"success": False, "error": "会话历史不存在"}
            
            # 创建临时状态用于生成报告
            temp_state = SessionState(
                session_id=session_id,
                user_input=session_history["session"].user_input
            )
            
            # 生成报告
            report = self.agent_d._generate_audit_report(temp_state)
            
            return {
                "success": True,
                "session_id": session_id,
                "report": report.dict(),
                "export_formats": ["json", "text"]
            }
            
        except Exception as e:
            logger.error(f"生成审计报告失败: {e}")
            return {"success": False, "error": str(e)}


class WorkflowManager:
    """工作流管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化工作流管理器"""
        self.config = config
        self.workflow = CogBiasWorkflow(config)
        self.active_sessions = {}
    
    def create_session(self, user_input: str) -> Dict[str, Any]:
        """创建新会话"""
        result = self.workflow.start_session(user_input)
        
        if result["success"]:
            session_id = result["session_id"]
            # 从字典中获取时间信息
            state_dict = result["state"]
            created_at = state_dict.get("created_at", "")
            updated_at = state_dict.get("updated_at", "")
            
            self.active_sessions[session_id] = {
                "created_at": created_at,
                "status": "active",
                "last_activity": updated_at
            }
        
        return result
    
    def submit_response(self, session_id: str, response_text: str, question_id: str = None) -> Dict[str, Any]:
        """提交用户回应"""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "会话不存在"}
        
        result = self.workflow.process_user_response(session_id, response_text, question_id)
        
        if result["success"]:
            self.active_sessions[session_id]["last_activity"] = result["state"].updated_at
            self.active_sessions[session_id]["status"] = result["state"].status
        
        return result
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """获取会话信息"""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "会话不存在"}
        
        return self.workflow.get_session_status(session_id)
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """结束会话"""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "会话不存在"}
        
        # 生成最终报告
        result = self.workflow.generate_audit_report(session_id)
        
        if result["success"]:
            self.active_sessions[session_id]["status"] = "completed"
        
        return result
    
    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """列出活跃会话"""
        sessions = []
        for session_id, info in self.active_sessions.items():
            if info["status"] == "active":
                sessions.append({
                    "session_id": session_id,
                    "created_at": info["created_at"],
                    "last_activity": info["last_activity"]
                })
        
        return sessions