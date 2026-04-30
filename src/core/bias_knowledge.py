"""
认知偏误知识库
内置 30+ 种常见认知偏误的定义、触发条件和纠正策略
"""

from typing import Dict, Any, List


class BiasKnowledgeBase:
    """认知偏误知识库"""
    
    def __init__(self):
        self.biases = self._initialize_biases()
    
    def _initialize_biases(self) -> Dict[str, Dict[str, Any]]:
        """初始化偏误知识库"""
        return {
            "confirmation_bias": {
                "name": "确认偏误",
                "category": "cognitive",
                "definition": "倾向于寻找、解释和记忆支持已有信念的信息，而忽视或低估相矛盾的信息",
                "triggers": [
                    "决策涉及个人信念或价值观",
                    "存在强烈的情感投入",
                    "决策结果对个人有重大影响",
                    "信息环境存在回音室效应"
                ],
                "examples": [
                    "只阅读支持自己政治观点的新闻",
                    "在投资决策中只关注利好消息",
                    "在招聘中过度关注符合偏见的候选人特质"
                ],
                "severity": "high",
                "correction_strategies": [
                    "主动寻找反面证据",
                    "采用魔鬼代言人方法",
                    "建立系统性的信息收集流程"
                ]
            },
            "anchoring_bias": {
                "name": "锚定偏误",
                "category": "cognitive",
                "definition": "过度依赖最先获得的信息（锚点）进行决策，即使后续信息更相关",
                "triggers": [
                    "存在明确的初始参考点",
                    "决策涉及数值估计",
                    "信息呈现有先后顺序",
                    "时间压力或认知负荷高"
                ],
                "examples": [
                    "谈判中第一个报价影响最终结果",
                    "产品定价受初始价格影响",
                    "绩效评估受第一印象主导"
                ],
                "severity": "medium",
                "correction_strategies": [
                    "考虑多个参考点",
                    "延迟决策以收集更多信息",
                    "使用统计方法而非直觉"
                ]
            },
            "availability_heuristic": {
                "name": "可得性启发",
                "category": "cognitive",
                "definition": "基于最容易想起的例证或信息进行判断，而非基于统计概率",
                "triggers": [
                    "决策基于记忆中的例证",
                    "近期发生类似事件",
                    "媒体报道频繁",
                    "情感冲击强烈的事件"
                ],
                "examples": [
                    "高估飞机事故概率因为媒体报道",
                    "基于最近的成功案例做决策",
                    "过度关注负面新闻影响风险评估"
                ],
                "severity": "medium",
                "correction_strategies": [
                    "查找统计数据而非依赖记忆",
                    "考虑基础概率",
                    "系统性地收集信息"
                ]
            },
            "overconfidence_bias": {
                "name": "过度自信偏误",
                "category": "cognitive",
                "definition": "高估自己的知识、能力或预测准确性",
                "triggers": [
                    "领域专业知识较强",
                    "过去有成功经验",
                    "决策复杂度高",
                    "缺乏即时反馈"
                ],
                "examples": [
                    "投资者高估选股能力",
                    "医生高估诊断准确性",
                    "项目经理低估项目风险"
                ],
                "severity": "high",
                "correction_strategies": [
                    "寻求外部验证",
                    "考虑不确定性范围",
                    "记录预测与实际结果对比"
                ]
            },
            "sunk_cost_fallacy": {
                "name": "沉没成本谬误",
                "category": "cognitive",
                "definition": "因已投入资源而继续投入更多，即使继续投入不理性",
                "triggers": [
                    "已投入大量时间、金钱或精力",
                    "决策涉及个人情感",
                    "存在公开承诺",
                    "害怕承认失败"
                ],
                "examples": [
                    "继续投资失败项目",
                    "坚持使用无效的治疗方法",
                    "不放弃表现不佳的员工"
                ],
                "severity": "medium",
                "correction_strategies": [
                    "忽略已投入成本",
                    "基于未来收益做决策",
                    "定期进行项目审查"
                ]
            },
            "groupthink": {
                "name": "群体思维",
                "category": "social",
                "definition": "群体为达成共识而压制异议和批判性思维",
                "triggers": [
                    "群体凝聚力强",
                    "存在强势领导者",
                    "外部威胁感知高",
                    "决策时间紧迫"
                ],
                "examples": [
                    "团队忽视潜在风险",
                    "成员不敢提出反对意见",
                    "决策过程缺乏多样性观点"
                ],
                "severity": "high",
                "correction_strategies": [
                    "指定魔鬼代言人",
                    "鼓励建设性冲突",
                    "匿名收集意见"
                ]
            },
            "hindsight_bias": {
                "name": "后见之明偏误",
                "category": "cognitive",
                "definition": "事件发生后认为结果本来就可预测",
                "triggers": [
                    "结果已知",
                    "存在强烈的情感反应",
                    "决策涉及个人责任",
                    "需要解释失败"
                ],
                "examples": [
                    "'我早就知道会这样'",
                    "过度简化复杂事件的因果关系",
                    "基于结果重新解释决策过程"
                ],
                "severity": "medium",
                "correction_strategies": [
                    "记录决策时的信息状态",
                    "考虑替代情景",
                    "进行事前概率评估"
                ]
            },
            "negativity_bias": {
                "name": "负面偏误",
                "category": "emotional",
                "definition": "给予负面信息比正面信息更多权重",
                "triggers": [
                    "存在潜在威胁",
                    "决策涉及风险",
                    "个人有焦虑倾向",
                    "近期有负面经历"
                ],
                "examples": [
                    "过度关注产品负面评价",
                    "高估失败概率",
                    "忽视积极信号"
                ],
                "severity": "medium",
                "correction_strategies": [
                    "平衡考虑正反信息",
                    "设置决策检查清单",
                    "寻求客观第三方意见"
                ]
            },
            "optimism_bias": {
                "name": "乐观偏误",
                "category": "emotional",
                "definition": "低估负面事件发生在自己身上的概率",
                "triggers": [
                    "决策涉及个人利益",
                    "缺乏直接负面经验",
                    "控制感较强",
                    "社会文化鼓励乐观"
                ],
                "examples": [
                    "低估健康风险",
                    "高估项目成功率",
                    "忽视潜在危机"
                ],
                "severity": "medium",
                "correction_strategies": [
                    "考虑最坏情况",
                    "参考统计概率",
                    "进行风险评估练习"
                ]
            },
            "fundamental_attribution_error": {
                "name": "基本归因错误",
                "category": "social",
                "definition": "过度强调个人特质而非情境因素解释他人行为",
                "triggers": [
                    "观察他人行为",
                    "存在文化差异",
                    "缺乏情境信息",
                    "涉及道德判断"
                ],
                "examples": [
                    "将员工失误归因于能力而非培训",
                    "认为他人失败是因为懒惰",
                    "忽视环境对行为的影响"
                ],
                "severity": "medium",
                "correction_strategies": [
                    "考虑情境因素",
                    "寻求更多背景信息",
                    "进行同理心训练"
                ]
            },
            "status_quo_bias": {
                "name": "现状偏误",
                "category": "cognitive",
                "definition": "偏好维持现状，抵制改变",
                "triggers": [
                    "改变涉及不确定性",
                    "存在转换成本",
                    "决策者风险厌恶",
                    "现状被视为默认选项"
                ],
                "examples": [
                    "坚持使用旧系统",
                    "不愿尝试新方法",
                    "默认选择现有选项"
                ],
                "severity": "medium",
                "correction_strategies": [
                    "明确比较改变与不改变的利弊",
                    "设置改变的时间限制",
                    "进行小规模试点"
                ]
            },
            "dunning_kruger_effect": {
                "name": "邓宁-克鲁格效应",
                "category": "cognitive",
                "definition": "能力不足者高估自己的能力，而能力强者低估自己的能力",
                "triggers": [
                    "缺乏元认知能力",
                    "领域知识有限",
                    "缺乏反馈机制",
                    "存在自我评估需求"
                ],
                "examples": [
                    "新手过度自信",
                    "专家低估自己的专业知识",
                    "缺乏自我反思能力"
                ],
                "severity": "high",
                "correction_strategies": [
                    "寻求客观反馈",
                    "进行能力测试",
                    "与同行比较"
                ]
            },
            "bandwagon_effect": {
                "name": "从众效应",
                "category": "social",
                "definition": "因他人行为而改变自己的信念或行为",
                "triggers": [
                    "社会压力大",
                    "信息不确定性高",
                    "渴望社会认同",
                    "决策涉及群体规范"
                ],
                "examples": [
                    "投资热门股票",
                    "采纳流行管理方法",
                    "跟随主流意见"
                ],
                "severity": "medium",
                "correction_strategies": [
                    "独立思考",
                    "评估证据质量",
                    "考虑少数派观点"
                ]
            },
            "halo_effect": {
                "name": "光环效应",
                "category": "cognitive",
                "definition": "基于单一积极特质形成整体积极印象",
                "triggers": [
                    "存在突出的积极特质",
                    "第一印象强烈",
                    "信息有限",
                    "决策时间短"
                ],
                "examples": [
                    "因外貌好而认为能力强",
                    "因名校背景而高估能力",
                    "因一次成功而忽视缺点"
                ],
                "severity": "medium",
                "correction_strategies": [
                    "多维度评估",
                    "延迟整体判断",
                    "收集全面信息"
                ]
            },
            "horn_effect": {
                "name": "尖角效应",
                "category": "cognitive",
                "definition": "基于单一负面特质形成整体负面印象",
                "triggers": [
                    "存在突出的负面特质",
                    "第一印象负面",
                    "情感反应强烈",
                    "存在刻板印象"
                ],
                "examples": [
                    "因一次失误而否定整体能力",
                    "因外表而低估内在品质",
                    "因背景而产生偏见"
                ],
                "severity": "medium",
                "correction_strategies": [
                    "分离特质评估",
                    "考虑情境因素",
                    "给予第二次机会"
                ]
            },
            "recency_bias": {
                "name": "近因偏误",
                "category": "cognitive",
                "definition": "给予最近信息过多权重",
                "triggers": [
                    "信息按时间顺序呈现",
                    "记忆限制",
                    "决策基于近期事件",
                    "缺乏系统记录"
                ],
                "examples": [
                    "绩效评估受最近表现影响",
                    "投资决策基于近期市场",
                    "忽视长期趋势"
                ],
                "severity": "medium",
                "correction_strategies": [
                    "查看历史数据",
                    "使用加权平均",
                    "建立系统记录"
                ]
            },
            "survivorship_bias": {
                "name": "幸存者偏误",
                "category": "cognitive",
                "definition": "只关注成功案例而忽视失败案例",
                "triggers": [
                    "成功案例更可见",
                    "失败案例被隐藏",
                    "媒体选择性报道",
                    "缺乏完整数据"
                ],
                "examples": [
                    "只研究成功企业",
                    "忽视失败的投资策略",
                    "基于成功故事做决策"
                ],
                "severity": "high",
                "correction_strategies": [
                    "考虑完整样本",
                    "研究失败案例",
                    "进行统计分析"
                ]
            },
            "planning_fallacy": {
                "name": "规划谬误",
                "category": "cognitive",
                "definition": "低估完成任务所需的时间、成本和风险",
                "triggers": [
                    "乐观情绪",
                    "缺乏历史数据",
                    "计划基于理想情景",
                    "存在时间压力"
                ],
                "examples": [
                    "项目时间估计过短",
                    "预算估计不足",
                    "忽视潜在风险"
                ],
                "severity": "high",
                "correction_strategies": [
                    "参考类似项目",
                    "使用统计方法",
                    "考虑最坏情况"
                ]
            },
            "zero_risk_bias": {
                "name": "零风险偏误",
                "category": "cognitive",
                "definition": "偏好完全消除小风险而非大幅降低大风险",
                "triggers": [
                    "风险感知强烈",
                    "存在情感因素",
                    "决策涉及安全",
                    "缺乏风险评估能力"
                ],
                "examples": [
                    "花费大量资源消除微小风险",
                    "忽视更大的系统性风险",
                    "过度关注可见风险"
                ],
                "severity": "medium",
                "correction_strategies": [
                    "进行成本效益分析",
                    "考虑风险优先级",
                    "使用风险评估工具"
                ]
            },
            "framing_effect": {
                "name": "框架效应",
                "category": "cognitive",
                "definition": "决策受问题表述方式影响而非实质内容",
                "triggers": [
                    "信息呈现方式不同",
                    "存在默认选项",
                    "涉及得失表述",
                    "决策者认知有限"
                ],
                "examples": [
                    "90%存活率 vs 10%死亡率",
                    "增益框架 vs 损失框架",
                    "积极表述 vs 消极表述"
                ],
                "severity": "medium",
                "correction_strategies": [
                    "多角度表述问题",
                    "关注实质内容",
                    "进行理性分析"
                ]
            }
        }
    
    def get_bias(self, bias_type: str) -> Dict[str, Any]:
        """获取特定偏误信息"""
        return self.biases.get(bias_type, {})
    
    def get_biases_by_category(self, category: str) -> List[Dict[str, Any]]:
        """按类别获取偏误列表"""
        return [bias for bias in self.biases.values() if bias.get("category") == category]
    
    def get_all_biases(self) -> List[Dict[str, Any]]:
        """获取所有偏误"""
        return list(self.biases.values())
    
    def detect_biases_in_text(self, text: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """在文本中检测可能的偏误"""
        # 这里可以扩展为使用 LLM 进行更复杂的检测
        detected_biases = []
        
        for bias_type, bias_info in self.biases.items():
            # 简单的关键词匹配（实际应用中应该使用更复杂的方法）
            triggers = bias_info.get("triggers", [])
            examples = bias_info.get("examples", [])
            
            # 检查文本中是否包含偏误相关的关键词
            bias_keywords = self._extract_keywords(bias_info)
            if any(keyword in text.lower() for keyword in bias_keywords):
                detected_biases.append({
                    "bias_type": bias_type,
                    "bias_info": bias_info,
                    "confidence": 0.7,  # 简单匹配的置信度
                    "evidence": "关键词匹配"
                })
        
        return detected_biases
    
    def _extract_keywords(self, bias_info: Dict[str, Any]) -> List[str]:
        """从偏误信息中提取关键词"""
        keywords = []
        
        # 从定义中提取关键词
        definition = bias_info.get("definition", "")
        keywords.extend(definition.split()[:5])  # 取前5个词
        
        # 从名称中提取关键词
        name = bias_info.get("name", "")
        keywords.extend(name.split())
        
        # 去重并转换为小写
        keywords = list(set([kw.lower() for kw in keywords if len(kw) > 1]))
        
        return keywords
    
    def get_correction_suggestions(self, bias_type: str, context: Dict[str, Any] = None) -> List[str]:
        """获取偏误纠正建议"""
        bias_info = self.get_bias(bias_type)
        if not bias_info:
            return []
        
        strategies = bias_info.get("correction_strategies", [])
        
        # 根据上下文定制建议
        if context:
            customized_suggestions = []
            for strategy in strategies:
                # 这里可以根据上下文信息定制建议
                customized_suggestions.append(f"在当前情境下，建议：{strategy}")
            return customized_suggestions
        
        return strategies