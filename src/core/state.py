"""
LangGraph 状态定义
定义工作流中传递的状态对象
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class DecisionTreeNode(BaseModel):
    """决策树节点"""
    node_id: str = Field(..., description="节点唯一标识")
    node_type: str = Field(..., description="节点类型: premise, evidence, conclusion")
    content: str = Field(..., description="节点内容")
    premise_type: Optional[str] = Field(None, description="前提类型: fact, assumption")
    evidence_strength: Optional[float] = Field(None, description="证据强度 0-1")
    reasoning_type: Optional[str] = Field(None, description="推理类型: deductive, inductive, abductive")
    parent_id: Optional[str] = Field(None, description="父节点ID")
    children_ids: List[str] = Field(default_factory=list, description="子节点ID列表")
    confidence: float = Field(default=1.0, description="置信度 0-1")
    tags: List[str] = Field(default_factory=list, description="标签列表")


class DecisionTree(BaseModel):
    """决策树"""
    version: int = Field(default=1, description="版本号")
    root_node_id: str = Field(..., description="根节点ID")
    nodes: Dict[str, DecisionTreeNode] = Field(..., description="节点字典")
    primary_conclusion: str = Field(..., description="主要结论")
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="创建时间")
    
    def get_node_path(self, node_id: str) -> List[DecisionTreeNode]:
        """获取节点路径"""
        path = []
        current_id = node_id
        
        while current_id in self.nodes:
            node = self.nodes[current_id]
            path.insert(0, node)
            current_id = node.parent_id
            
        return path
    
    def dict(self, **kwargs):
        """重写 dict 方法，处理 datetime 序列化"""
        data = super().dict(**kwargs)
        # 将 datetime 转换为 ISO 字符串格式
        if 'created_at' in data and isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].isoformat()
        return data


class BiasDetection(BaseModel):
    """偏误检测结果"""
    bias_type: str = Field(..., description="偏误类型")
    node_id: str = Field(..., description="相关节点ID")
    confidence: float = Field(..., description="检测置信度 0-1")
    reasoning: str = Field(..., description="推理过程")
    severity: str = Field(..., description="严重程度: low, medium, high, critical")
    correction_question: str = Field(..., description="纠正性问题")
    evidence: List[str] = Field(default_factory=list, description="证据列表")


class BiasReport(BaseModel):
    """偏误报告"""
    iteration: int = Field(..., description="迭代次数")
    detected_biases: List[BiasDetection] = Field(default_factory=list, description="检测到的偏误")
    overall_risk_score: float = Field(..., description="总体风险评分 0-1")
    risk_heatmap: Dict[str, float] = Field(..., description="风险热力图")
    recommendations: List[str] = Field(default_factory=list, description="建议列表")


class AdversarialQuestion(BaseModel):
    """对抗性问题"""
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="问题ID")
    question_type: str = Field(..., description="问题类型: counterfactual, stakeholder, stress_test")
    question_text: str = Field(..., description="问题文本")
    target_node_id: str = Field(..., description="目标节点ID")
    bias_type: str = Field(..., description="相关偏误类型")
    intensity: str = Field(..., description="强度: mild, moderate, strong")
    expected_response_type: str = Field(..., description="期望回应类型")


class UserResponse(BaseModel):
    """用户回应"""
    question_id: str = Field(..., description="问题ID")
    response_text: str = Field(..., description="回应文本")
    bias_acknowledged: bool = Field(default=False, description="是否承认偏误")
    response_type: str = Field(default="normal", description="回应类型: normal, defensive, accepting")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="时间戳")


class SessionState(BaseModel):
    """会话状态 - LangGraph 状态对象"""
    
    # 基础信息
    session_id: str = ""
    user_input: str = ""
    iteration_count: int = 0
    status: str = "active"
    
    # Agent 输出
    decision_tree: Optional[DecisionTree] = None
    bias_report: Optional[BiasReport] = None
    adversarial_questions: List[AdversarialQuestion] = []
    user_responses: List[UserResponse] = []
    
    # 消息历史
    messages: List[Dict[str, Any]] = []
    
    # 元数据
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """添加消息"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        if metadata:
            message["metadata"] = metadata
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_latest_user_response(self) -> Optional[UserResponse]:
        """获取最新的用户回应"""
        if not self.user_responses:
            return None
        return self.user_responses[-1]
    
    def should_continue(self) -> bool:
        """判断是否应该继续迭代"""
        if self.status != "active":
            return False
        
        if self.iteration_count >= 10:  # 最大迭代次数
            return False
        
        # 如果有未回答的问题，继续等待
        if self.adversarial_questions and not self.user_responses:
            return True
        
        # 如果用户回应了所有问题，继续处理
        if (self.adversarial_questions and self.user_responses and 
            len(self.user_responses) >= len(self.adversarial_questions)):
            return True
        
        return self.iteration_count == 0  # 初始迭代


class AuditReport(BaseModel):
    """审计报告"""
    session_id: str = Field(..., description="会话ID")
    decision_evolution: List[Dict[str, Any]] = Field(..., description="决策演变历史")
    bias_exposure: Dict[str, Any] = Field(..., description="偏误暴露情况")
    bias_fingerprint: Dict[str, Any] = Field(..., description="偏误指纹")
    recommendations: List[str] = Field(..., description="改进建议")
    summary: str = Field(..., description="报告摘要")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(), description="生成时间")