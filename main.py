#!/usr/bin/env python3
"""
认知偏误审计与决策纠偏 Agent 群 - 主入口文件
支持命令行和程序化两种使用方式
"""

import argparse
import sys
import yaml
import logging
from pathlib import Path

from src.core.graph import WorkflowManager
from src.utils.logger import setup_logging


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='认知偏误审计与决策纠偏 Agent 群')
    
    parser.add_argument('--config', '-c', default='config.yaml', 
                       help='配置文件路径 (默认: config.yaml)')
    parser.add_argument('--mode', '-m', choices=['web', 'cli', 'api'], default='web',
                       help='运行模式: web(Web UI), cli(命令行), api(API服务)')
    parser.add_argument('--input', '-i', help='决策问题输入 (CLI模式使用)')
    parser.add_argument('--session', '-s', help='会话ID (CLI模式使用)')
    parser.add_argument('--response', '-r', help='用户回应 (CLI模式使用)')
    parser.add_argument('--log-level', '-l', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='日志级别')
    
    args = parser.parse_args()
    
    # 加载配置
    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"错误: 配置文件 {args.config} 未找到")
        sys.exit(1)
    
    # 设置日志
    setup_logging(args.log_level, config.get('logging', {}).get('file'))
    logger = logging.getLogger(__name__)
    
    # 创建工作流管理器
    try:
        workflow_manager = WorkflowManager(config)
    except Exception as e:
        logger.error(f"初始化工作流管理器失败: {e}")
        sys.exit(1)
    
    # 根据模式执行
    if args.mode == 'web':
        run_web_ui(config)
    elif args.mode == 'cli':
        run_cli_mode(workflow_manager, args)
    elif args.mode == 'api':
        run_api_mode(workflow_manager, config)


def run_web_ui(config: dict):
    """运行 Web UI 模式"""
    try:
        from src.ui.app import CogBiasUI
        ui = CogBiasUI(config)
        ui.run()
    except ImportError as e:
        print(f"Web UI 依赖缺失: {e}")
        print("请安装 Streamlit: pip install streamlit")
        sys.exit(1)


def run_cli_mode(workflow_manager: WorkflowManager, args):
    """运行命令行模式"""
    if args.input:
        # 创建新会话
        result = workflow_manager.create_session(args.input)
        if result['success']:
            print(f"会话创建成功! 会话ID: {result['session_id']}")
            print(f"下一步: 使用 --session {result['session_id']} --response '您的回应' 继续")
        else:
            print(f"会话创建失败: {result['error']}")
    
    elif args.session and args.response:
        # 处理用户回应
        result = workflow_manager.submit_response(args.session, args.response)
        if result['success']:
            print("回应处理成功!")
            print(f"下一步: {result['next_step']}")
        else:
            print(f"回应处理失败: {result['error']}")
    
    elif args.session:
        # 获取会话状态
        result = workflow_manager.get_session_info(args.session)
        if 'error' in result:
            print(f"获取会话信息失败: {result['error']}")
        else:
            print(f"会话状态: {result}")
    
    else:
        print("请提供 --input 创建会话或 --session 和 --response 处理回应")


def run_api_mode(workflow_manager: WorkflowManager, config: dict):
    """运行 API 服务模式"""
    try:
        from flask import Flask, request, jsonify
        
        app = Flask(__name__)
        
        @app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({'status': 'healthy', 'service': 'cogbias-swarm'})
        
        @app.route('/sessions', methods=['POST'])
        def create_session():
            data = request.get_json()
            if not data or 'input' not in data:
                return jsonify({'error': '缺少 input 参数'}), 400
            
            result = workflow_manager.create_session(data['input'])
            return jsonify(result)
        
        @app.route('/sessions/<session_id>/responses', methods=['POST'])
        def submit_response(session_id):
            data = request.get_json()
            if not data or 'response' not in data:
                return jsonify({'error': '缺少 response 参数'}), 400
            
            result = workflow_manager.submit_response(
                session_id, 
                data['response'],
                data.get('question_id')
            )
            return jsonify(result)
        
        @app.route('/sessions/<session_id>/report', methods=['GET'])
        def get_report(session_id):
            result = workflow_manager.generate_audit_report(session_id)
            return jsonify(result)
        
        port = config.get('web_ui', {}).get('port', 5000)
        host = config.get('web_ui', {}).get('host', '0.0.0.0')
        
        print(f"API 服务启动在 http://{host}:{port}")
        app.run(host=host, port=port, debug=config.get('web_ui', {}).get('debug', False))
        
    except ImportError:
        print("API 模式需要 Flask，请安装: pip install flask")
        sys.exit(1)


if __name__ == "__main__":
    main()