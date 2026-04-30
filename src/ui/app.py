"""
Streamlit Web UI 应用
提供三面板界面：决策树可视化、对话流、审计报告预览
"""

import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from typing import Dict, Any, Optional
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.graph import WorkflowManager
from src.utils.logger import setup_logging
from src.core.state import SessionState


class CogBiasUI:
    """认知偏误审计 Web UI"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化 UI"""
        self.config = config
        self.workflow_manager = WorkflowManager(config)
        
        # 设置页面配置
        st.set_page_config(
            page_title="认知偏误审计与决策纠偏系统",
            page_icon="🧠",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # 隐藏右上角菜单（包括 Deploy 按钮）
        hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
        """
        st.markdown(hide_streamlit_style, unsafe_allow_html=True)
        
        # 初始化 session state
        if 'current_session_id' not in st.session_state:
            st.session_state.current_session_id = None
        if 'session_history' not in st.session_state:
            st.session_state.session_history = {}
    
    def render_sidebar(self):
        """渲染侧边栏"""
        with st.sidebar:
            st.title("🧠 认知偏误审计系统")
            st.markdown("---")
            
            # 会话管理
            st.subheader("会话管理")
            
            # 新会话创建
            with st.form("new_session_form"):
                user_input = st.text_area(
                    "请输入您的决策问题或描述:",
                    placeholder="例如：我应该投资这个创业项目吗？为什么？",
                    height=100
                )
                
                if st.form_submit_button("开始分析"):
                    if user_input.strip():
                        self._create_new_session(user_input)
                    else:
                        st.error("请输入决策问题")
            
            st.markdown("---")
            
            # 活跃会话列表
            st.subheader("活跃会话")
            active_sessions = self.workflow_manager.list_active_sessions()
            
            if active_sessions:
                for session in active_sessions:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(f"会话: {session['session_id'][-8:]}", 
                                   key=f"session_{session['session_id']}"):
                            st.session_state.current_session_id = session['session_id']
                    with col2:
                        if st.button("❌", key=f"close_{session['session_id']}"):
                            self._close_session(session['session_id'])
            else:
                st.info("暂无活跃会话")
            
            st.markdown("---")
            
            # 系统信息
            st.subheader("系统信息")
            st.markdown("""
            **架构**: 多 Agent 协作系统
            **框架**: LangGraph
            **版本**: 1.0.0
            """)
    
    def render_main_content(self):
        """渲染主内容区域"""
        if not st.session_state.current_session_id:
            self._render_welcome_screen()
        else:
            self._render_session_interface()
    
    def _render_welcome_screen(self):
        """渲染欢迎界面"""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.title("🧠 欢迎使用认知偏误审计系统")
            st.markdown("""
            ### 系统介绍
            
            本系统采用多 Agent 协作架构，帮助您识别和纠正决策过程中的认知偏误：
            
            **🤖 Agent A - 决策构建追踪器**
            - 解析自然语言决策描述
            - 构建结构化决策树
            - 追踪决策逻辑演变
            
            **🔍 Agent B - 偏误模式匹配引擎**
            - 检测30+种认知偏误
            - 采用 Chain-of-Thought 推理
            - 生成风险热力图
            
            **⚔️ Agent C - 对抗性推理 Agent**
            - 生成尖锐的逻辑挑战
            - 进行反事实情景测试
            - 扮演异见者角色
            
            **📊 Agent D - 元认知记录器**
            - 记录决策演变轨迹
            - 生成审计报告
            - 建立偏误指纹库
            
            ### 使用指南
            1. 在左侧边栏输入您的决策问题
            2. 系统将逐步引导您完成偏误检测
            3. 回答对抗性问题以完善决策
            4. 查看最终的审计报告
            """)
    
    def _render_session_interface(self):
        """渲染会话界面"""
        session_id = st.session_state.current_session_id
        
        # 会话标题
        col1, col2 = st.columns([4, 1])
        with col1:
            st.title(f"会话分析: {session_id[-8:]}")
        with col2:
            if st.button("结束会话并生成报告"):
                self._end_session(session_id)
        
        # 三面板布局
        tab1, tab2, tab3 = st.tabs(["📊 决策树可视化", "💬 对话流", "📋 审计报告预览"])
        
        with tab1:
            self._render_decision_tree_panel(session_id)
        
        with tab2:
            self._render_conversation_panel(session_id)
        
        with tab3:
            self._render_audit_report_panel(session_id)
    
    def _render_decision_tree_panel(self, session_id: str):
        """渲染决策树面板"""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("决策树结构")
            
            # 获取会话状态
            session_info = self.workflow_manager.get_session_info(session_id)
            
            if session_info.get('success'):
                # 这里应该渲染决策树可视化
                # 目前显示文本表示
                st.info("决策树可视化功能开发中...")
                
                # 显示决策树摘要
                if 'state' in session_info:
                    state = session_info['state']
                    if state.decision_tree:
                        st.json(state.decision_tree.dict(), expanded=False)
            else:
                st.error("获取会话信息失败")
        
        with col2:
            st.subheader("偏误热力图")
            
            # 模拟热力图数据
            heatmap_data = {
                '节点': ['前提1', '证据1', '结论1', '前提2', '证据2'],
                '风险评分': [0.8, 0.6, 0.3, 0.9, 0.4]
            }
            
            df = pd.DataFrame(heatmap_data)
            fig = px.bar(df, x='风险评分', y='节点', orientation='h', 
                        color='风险评分', color_continuous_scale='RdYlGn_r')
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_conversation_panel(self, session_id: str):
        """渲染对话面板"""
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.subheader("对话历史")
            
            # 显示消息历史
            session_info = self.workflow_manager.get_session_info(session_id)
            
            if session_info.get('success') and 'state' in session_info:
                state = session_info['state']
                
                for message in state.messages[-10:]:  # 显示最近10条消息
                    with st.chat_message(message['role']):
                        st.write(message['content'])
                        if 'metadata' in message:
                            st.caption(f"元数据: {message['metadata']}")
            
            # 用户输入区域
            st.subheader("您的回应")
            
            # 检查是否有待回答的问题
            if session_info.get('success') and 'state' in session_info:
                state = session_info['state']
                
                if state.adversarial_questions and len(state.user_responses) < len(state.adversarial_questions):
                    current_question = state.adversarial_questions[len(state.user_responses)]
                    
                    st.info(f"**待回答问题**: {current_question.question_text}")
                    
                    with st.form("user_response_form"):
                        response = st.text_area("请输入您的回应:", height=100)
                        
                        if st.form_submit_button("提交回应"):
                            if response.strip():
                                self._submit_response(session_id, response, current_question.question_id)
                            else:
                                st.error("请输入回应内容")
                else:
                    st.success("所有问题已回答完毕！")
        
        with col2:
            st.subheader("偏误标记")
            
            # 显示检测到的偏误
            session_info = self.workflow_manager.get_session_info(session_id)
            
            if session_info.get('success') and 'state' in session_info:
                state = session_info['state']
                
                if state.bias_report and state.bias_report.detected_biases:
                    for i, bias in enumerate(state.bias_report.detected_biases):
                        with st.expander(f"偏误 {i+1}: {bias.bias_type}", expanded=True):
                            st.write(f"**严重程度**: {bias.severity}")
                            st.write(f"**置信度**: {bias.confidence:.2f}")
                            st.write(f"**推理**: {bias.reasoning}")
                            st.write(f"**纠正问题**: {bias.correction_question}")
                else:
                    st.info("暂无检测到的偏误")
    
    def _render_audit_report_panel(self, session_id: str):
        """渲染审计报告面板"""
        st.subheader("审计报告预览")
        
        # 生成报告按钮
        if st.button("生成完整审计报告"):
            with st.spinner("生成报告中..."):
                report_result = self.workflow_manager.generate_audit_report(session_id)
                
                if report_result['success']:
                    st.session_state.current_report = report_result['report']
                    st.success("报告生成成功！")
                else:
                    st.error(f"报告生成失败: {report_result['error']}")
        
        # 显示报告内容
        if 'current_report' in st.session_state:
            report = st.session_state.current_report
            
            # 报告摘要
            st.subheader("报告摘要")
            st.write(report.get('summary', '无摘要'))
            
            # 决策演变
            st.subheader("决策演变")
            evolution = report.get('decision_evolution', {})
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("初始结论", evolution.get('initial_conclusion', 'N/A'))
            with col2:
                st.metric("最终结论", evolution.get('final_conclusion', 'N/A'))
            
            # 偏误暴露
            st.subheader("偏误暴露情况")
            exposure = report.get('bias_exposure', {})
            
            if exposure.get('bias_types_detected'):
                st.write(f"检测到的偏误类型: {', '.join(exposure['bias_types_detected'])}")
            
            # 改进建议
            st.subheader("改进建议")
            recommendations = report.get('recommendations', [])
            
            for i, rec in enumerate(recommendations, 1):
                st.write(f"{i}. {rec}")
            
            # 导出选项
            st.subheader("导出报告")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("导出 JSON"):
                    st.download_button(
                        label="下载 JSON 报告",
                        data=json.dumps(report, indent=2, ensure_ascii=False),
                        file_name=f"audit_report_{session_id[-8:]}.json",
                        mime="application/json"
                    )
            
            with col2:
                if st.button("导出文本"):
                    # 这里应该调用文本格式化方法
                    text_report = "文本报告生成功能开发中..."
                    st.download_button(
                        label="下载文本报告",
                        data=text_report,
                        file_name=f"audit_report_{session_id[-8:]}.txt",
                        mime="text/plain"
                    )
    
    def _create_new_session(self, user_input: str):
        """创建新会话"""
        with st.spinner("创建会话中..."):
            result = self.workflow_manager.create_session(user_input)
            
            if result['success']:
                st.session_state.current_session_id = result['session_id']
                st.success("会话创建成功！")
                st.rerun()
            else:
                st.error(f"会话创建失败: {result['error']}")
    
    def _submit_response(self, session_id: str, response: str, question_id: str):
        """提交用户回应"""
        with st.spinner("处理回应中..."):
            result = self.workflow_manager.submit_response(session_id, response, question_id)
            
            if result['success']:
                st.success("回应提交成功！")
                st.rerun()
            else:
                st.error(f"回应提交失败: {result['error']}")
    
    def _end_session(self, session_id: str):
        """结束会话"""
        with st.spinner("结束会话中..."):
            result = self.workflow_manager.end_session(session_id)
            
            if result['success']:
                st.session_state.current_session_id = None
                if 'current_report' in st.session_state:
                    del st.session_state.current_report
                st.success("会话已结束，报告已生成！")
                st.rerun()
            else:
                st.error(f"结束会话失败: {result['error']}")
    
    def _close_session(self, session_id: str):
        """关闭会话"""
        if st.session_state.current_session_id == session_id:
            st.session_state.current_session_id = None
        st.rerun()
    
    def run(self):
        """运行 UI 应用"""
        # 渲染页面
        self.render_sidebar()
        self.render_main_content()


def main():
    """主函数"""
    # 加载配置
    import yaml
    
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        st.error("配置文件 config.yaml 未找到")
        return
    
    # 设置日志
    setup_logging(
        config.get('logging', {}).get('level', 'INFO'),
        config.get('logging', {}).get('file')
    )
    
    # 创建并运行 UI
    ui = CogBiasUI(config)
    ui.run()


if __name__ == "__main__":
    main()