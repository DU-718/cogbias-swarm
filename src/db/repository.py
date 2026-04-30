"""
数据访问层
提供对数据库的 CRUD 操作
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, Session, DecisionTree, BiasReport, AdversarialQuestion, UserResponse, AuditReport, BiasKnowledge

logger = logging.getLogger(__name__)


class Repository:
    """数据仓库类"""
    
    def __init__(self, database_url: str):
        """
        初始化数据库连接
        
        Args:
            database_url: 数据库连接字符串
        """
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # 创建表
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()
    
    def create_session(self, session_id: str, user_input: str) -> Session:
        """创建新会话"""
        db = self.get_session()
        try:
            session = Session(session_id=session_id, user_input=user_input)
            db.add(session)
            db.commit()
            db.refresh(session)
            return session
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"创建会话失败: {e}")
            raise
        finally:
            db.close()
    
    def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """根据 ID 获取会话"""
        db = self.get_session()
        try:
            return db.query(Session).filter(Session.session_id == session_id).first()
        finally:
            db.close()
    
    def save_decision_tree(self, session_id: str, tree_data: Dict[str, Any], version: int = 1) -> DecisionTree:
        """保存决策树"""
        db = self.get_session()
        try:
            tree = DecisionTree(
                session_id=session_id,
                version=version,
                tree_data=tree_data
            )
            db.add(tree)
            db.commit()
            db.refresh(tree)
            return tree
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"保存决策树失败: {e}")
            raise
        finally:
            db.close()
    
    def get_latest_decision_tree(self, session_id: str) -> Optional[DecisionTree]:
        """获取最新的决策树"""
        db = self.get_session()
        try:
            return db.query(DecisionTree).filter(
                DecisionTree.session_id == session_id
            ).order_by(desc(DecisionTree.version)).first()
        finally:
            db.close()
    
    def save_bias_report(self, session_id: str, report_data: Dict[str, Any], iteration: int = 1) -> BiasReport:
        """保存偏误报告"""
        db = self.get_session()
        try:
            report = BiasReport(
                session_id=session_id,
                iteration=iteration,
                report_data=report_data
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            return report
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"保存偏误报告失败: {e}")
            raise
        finally:
            db.close()
    
    def save_adversarial_question(self, session_id: str, iteration: int, question_type: str, 
                                question_text: str, target_node_id: Optional[str] = None, 
                                bias_type: Optional[str] = None) -> AdversarialQuestion:
        """保存对抗性问题"""
        db = self.get_session()
        try:
            question = AdversarialQuestion(
                session_id=session_id,
                iteration=iteration,
                question_type=question_type,
                question_text=question_text,
                target_node_id=target_node_id,
                bias_type=bias_type
            )
            db.add(question)
            db.commit()
            db.refresh(question)
            return question
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"保存对抗性问题失败: {e}")
            raise
        finally:
            db.close()
    
    def save_user_response(self, question_id: int, response_text: str, 
                          bias_acknowledged: bool = False, response_type: str = "normal") -> UserResponse:
        """保存用户回应"""
        db = self.get_session()
        try:
            response = UserResponse(
                question_id=question_id,
                response_text=response_text,
                bias_acknowledged=bias_acknowledged,
                response_type=response_type
            )
            db.add(response)
            db.commit()
            db.refresh(response)
            return response
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"保存用户回应失败: {e}")
            raise
        finally:
            db.close()
    
    def save_audit_report(self, session_id: str, report_data: Dict[str, Any], 
                         summary: str, bias_fingerprint: Dict[str, Any], 
                         recommendations: str) -> AuditReport:
        """保存审计报告"""
        db = self.get_session()
        try:
            report = AuditReport(
                session_id=session_id,
                report_data=report_data,
                summary=summary,
                bias_fingerprint=bias_fingerprint,
                recommendations=recommendations
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            return report
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"保存审计报告失败: {e}")
            raise
        finally:
            db.close()
    
    def get_bias_knowledge(self) -> List[BiasKnowledge]:
        """获取偏误知识库"""
        db = self.get_session()
        try:
            return db.query(BiasKnowledge).all()
        finally:
            db.close()
    
    def update_session_status(self, session_id: str, status: str) -> bool:
        """更新会话状态"""
        db = self.get_session()
        try:
            session = db.query(Session).filter(Session.session_id == session_id).first()
            if session:
                session.status = status
                db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"更新会话状态失败: {e}")
            return False
        finally:
            db.close()
    
    def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """获取会话完整历史"""
        db = self.get_session()
        try:
            session = db.query(Session).filter(Session.session_id == session_id).first()
            if not session:
                return {}
            
            decision_trees = db.query(DecisionTree).filter(
                DecisionTree.session_id == session_id
            ).order_by(DecisionTree.version).all()
            
            bias_reports = db.query(BiasReport).filter(
                BiasReport.session_id == session_id
            ).order_by(BiasReport.iteration).all()
            
            questions = db.query(AdversarialQuestion).filter(
                AdversarialQuestion.session_id == session_id
            ).order_by(AdversarialQuestion.iteration).all()
            
            return {
                "session": session,
                "decision_trees": decision_trees,
                "bias_reports": bias_reports,
                "adversarial_questions": questions
            }
        finally:
            db.close()