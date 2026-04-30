"""
SQLAlchemy 数据模型定义
定义会话、决策树、偏误检测等数据表结构
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Session(Base):
    """会话记录表"""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    user_input = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(32), default="active")  # active, completed, cancelled
    
    # 关系
    decision_trees = relationship("DecisionTree", back_populates="session")
    bias_reports = relationship("BiasReport", back_populates="session")
    audit_reports = relationship("AuditReport", back_populates="session")


class DecisionTree(Base):
    """决策树版本记录表"""
    __tablename__ = "decision_trees"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), ForeignKey("sessions.session_id"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    tree_data = Column(JSON, nullable=False)  # 完整的决策树 JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    session = relationship("Session", back_populates="decision_trees")


class BiasReport(Base):
    """偏误检测报告表"""
    __tablename__ = "bias_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), ForeignKey("sessions.session_id"), nullable=False)
    iteration = Column(Integer, nullable=False, default=1)
    report_data = Column(JSON, nullable=False)  # 偏误检测结果
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    session = relationship("Session", back_populates="bias_reports")


class AdversarialQuestion(Base):
    """对抗性问题记录表"""
    __tablename__ = "adversarial_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), ForeignKey("sessions.session_id"), nullable=False)
    iteration = Column(Integer, nullable=False)
    question_type = Column(String(32), nullable=False)  # counterfactual, stakeholder, stress_test
    question_text = Column(Text, nullable=False)
    target_node_id = Column(String(64))  # 针对的决策树节点
    bias_type = Column(String(64))  # 相关的偏误类型
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user_responses = relationship("UserResponse", back_populates="question")


class UserResponse(Base):
    """用户回应记录表"""
    __tablename__ = "user_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("adversarial_questions.id"), nullable=False)
    response_text = Column(Text, nullable=False)
    bias_acknowledged = Column(Boolean, default=False)  # 用户是否承认偏误
    response_type = Column(String(32), default="normal")  # normal, defensive, accepting
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    question = relationship("AdversarialQuestion", back_populates="user_responses")


class AuditReport(Base):
    """审计报告表"""
    __tablename__ = "audit_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), ForeignKey("sessions.session_id"), nullable=False)
    report_data = Column(JSON, nullable=False)  # 完整的审计报告
    summary = Column(Text)  # 报告摘要
    bias_fingerprint = Column(JSON)  # 用户偏误指纹
    recommendations = Column(Text)  # 改进建议
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    session = relationship("Session", back_populates="audit_reports")


class BiasKnowledge(Base):
    """偏误知识库表"""
    __tablename__ = "bias_knowledge"
    
    id = Column(Integer, primary_key=True, index=True)
    bias_type = Column(String(64), unique=True, nullable=False)
    category = Column(String(64), nullable=False)  # cognitive, social, emotional, etc.
    definition = Column(Text, nullable=False)
    triggers = Column(JSON)  # 触发条件列表
    examples = Column(JSON)  # 示例列表
    severity = Column(String(32), default="medium")  # low, medium, high, critical
    correction_strategies = Column(JSON)  # 纠正策略
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)