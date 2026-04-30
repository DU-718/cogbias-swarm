# 🧠 Cognitive Bias Audit & Decision Rectification Agent Swarm

**认知偏误审计与决策纠偏 Agent 群**

**多语言 README 可用：**
- [English Version](README.md)
- [中文版本](README_zh.md) (当前)

---

## 🌟 核心特性

- **🤖 多 Agent 协作**: 四个专业 Agent 分工协作，覆盖决策分析全流程
- **🔍 智能偏误检测**: 内置 30+ 种认知偏误知识库，采用 Chain-of-Thought 推理
- **⚔️ 对抗性挑战**: 生成尖锐的逻辑挑战问题，进行深度压力测试
- **📊 实时可视化**: 三面板 Web UI，实时显示决策树、对话流和审计报告
- **💾 数据持久化**: SQLite 数据库存储完整会话历史和偏误指纹
- **🐳 容器化部署**: 完整的 Docker 支持，支持开发和生产环境

## 🏗️ 系统架构

### Agent 分工

| Agent       | 角色          | 核心功能            |
| ----------- | ----------- | --------------- |
| **Agent A** | 决策构建追踪器     | 解析自然语言，构建结构化决策树 |
| **Agent B** | 偏误模式匹配引擎    | 检测认知偏误，生成风险热力图  |
| **Agent C** | 对抗性推理 Agent | 生成逻辑挑战问题，进行压力测试 |
| **Agent D** | 元认知记录器      | 记录决策演变，生成审计报告   |

### 技术栈

- **编程语言**: Python 3.11+
- **多 Agent 框架**: LangGraph (选择理由：更灵活的状态管理和工作流控制)
- **LLM 接口**: OpenAI API 兼容接口
- **前端**: Streamlit Web UI
- **数据库**: SQLite + SQLAlchemy
- **配置管理**: YAML + 环境变量
- **部署**: Docker + Docker Compose

## 🚀 快速开始

### 环境要求

- Python 3.11+
- OpenAI API Key
- Docker (可选，用于容器化部署)

### 安装步骤

1. **克隆项目**

```bash
git clone https://github.com/DU-718/cogbias-swarm.git
cd cogbias-swarm
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **配置环境变量**

```bash
cp .env.example .env
# 编辑 .env 文件，设置您的 OpenAI API Key
```

4. **运行应用**

```bash
streamlit run src/ui/app.py
```

### Docker 部署

```bash
# 构建镜像
docker build -t cogbias-swarm .

# 运行容器
docker run -p 8501:8501 -e OPENAI_API_KEY=your_key cogbias-swarm

# 或使用 Docker Compose
docker-compose up -d
```

## 📖 使用指南

### 基本工作流程

1. **输入决策问题**: 在 Web UI 中输入您的决策描述
2. **决策树构建**: Agent A 解析并构建结构化决策树
3. **偏误检测**: Agent B 扫描决策树，识别认知偏误
4. **对抗挑战**: Agent C 生成尖锐的逻辑挑战问题
5. **用户回应**: 回答挑战问题，完善决策逻辑
6. **迭代优化**: 系统根据回应更新决策树，循环检测
7. **生成报告**: 最终生成完整的认知审计报告

### Web UI 界面

系统提供三面板界面：

- **左侧**: 决策树可视化（JSON 树形结构）
- **中间**: 实时对话流（含偏误标记）
- **右侧**: 审计报告预览和导出

## 🔧 配置说明

### 主要配置项

编辑 `config.yaml` 文件进行系统配置：

```yaml
# LLM 配置
llm:
  model: "gpt-4-turbo-preview"
  temperature: 0.1
  max_tokens: 4096

# Agent 配置
agents:
  agent_a:
    max_iterations: 5
  agent_b:
    bias_threshold: 0.7
  agent_c:
    challenge_intensity: "moderate"

# 工作流配置
workflow:
  max_iterations: 10
  timeout_minutes: 30
```

### 环境变量

重要环境变量（在 `.env` 中配置）：

- `OPENAI_API_KEY`: OpenAI API 密钥
- `OPENAI_BASE_URL`: API 基础 URL（支持兼容接口）
- `LOG_LEVEL`: 日志级别
- `DATABASE_URL`: 数据库连接字符串

## 🧪 测试

运行单元测试：

```bash
pytest tests/ -v
```

测试覆盖：

- Agent 功能测试
- 工作流状态管理测试
- 数据持久化测试
- 错误处理测试

## 📊 系统特性详解

### 偏误检测能力

系统内置 30+ 种常见认知偏误，包括：

- **确认偏误**: 倾向于寻找支持已有信念的信息
- **锚定偏误**: 过度依赖初始信息
- **过度自信偏误**: 高估自己的知识和能力
- **沉没成本谬误**: 因已投入而继续不理性投入
- **群体思维**: 为达成共识压制异议
- **后见之明偏误**: 认为结果本来就可预测

### 决策树结构

决策树采用分层结构：

```
结论节点 (结论)
├── 前提节点 (事实/假设)
│   ├── 证据节点 (推理类型 + 强度)
│   └── 证据节点
└── 前提节点
    └── 证据节点
```

### 审计报告内容

最终审计报告包含：

1. **决策演变摘要**: 初始 vs 最终决策对比
2. **偏误暴露清单**: 检测到的偏误类型及频率
3. **个人偏误指纹**: 用户的认知弱点分析
4. **改进建议**: 针对性的决策改进策略

## 🔍 API 使用

系统提供程序化 API 接口：

```python
from src.core.graph import WorkflowManager
import yaml

# 加载配置
with open('config.yaml') as f:
    config = yaml.safe_load(f)

# 创建工作流管理器
manager = WorkflowManager(config)

# 创建新会话
result = manager.create_session("我应该投资这个项目吗？")

# 处理用户回应
response_result = manager.submit_response(
    session_id=result['session_id'],
    response_text="我的回应内容",
    question_id="question_123"
)

# 生成审计报告
report = manager.generate_audit_report(result['session_id'])
```

## 🐛 故障排除

### 常见问题

1. **LLM 调用失败**
   - 检查 API Key 配置
   - 验证网络连接
   - 查看日志文件
2. **数据库连接错误**
   - 检查数据库文件权限
   - 验证数据库路径配置
3. **Web UI 无法访问**
   - 检查端口占用情况
   - 验证 Streamlit 配置

### 日志查看

日志文件位置：`./logs/cogbias.log`

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

### 开发规范

- 遵循 PEP 8 代码风格
- 为新增功能编写单元测试
- 更新相关文档
- 使用类型注解

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- 感谢 LangChain 团队提供的优秀框架
- 感谢认知科学领域的研究成果
- 感谢所有贡献者和用户

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 项目 Issues: [GitHub Issues]
- 文档: [项目 Wiki]

***

**🧠 做出更好的决策，从识别认知偏误开始**