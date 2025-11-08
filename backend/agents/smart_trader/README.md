# 智能投资团队智能体

参考：
- [TradingAgents](https://github.com/TauricResearch/TradingAgents.git)
- [TradingAgents研究报告](ai_memory/research/0003-TradingAgents多智能体交易系统架构研究.md)
- [Google ADK Multi Agents System](https://google.github.io/adk-docs/agents/multi-agents/#agent-hierarchy-parent-agent-sub-agents)

## 整体架构

整体采用Google ADK Multi Agents System，架构如下：
- Agent Root：SequentialAgent，负责调度各个Agent团队完成各自的阶段性任务
  - Agent Team：投资团队，仿照TradingAgents的架构，分成如下几个子团队
    - 分析师团队 (Analysts)：负责收集市场数据，分析市场趋势，预测市场走势
        - 基本面分析师 (Fundamentals Analyst)：分析公司基本面信息，包括财务报表、公司概况和财务历史
        - 市场分析师 (Market Analyst)：技术分析和市场趋势识别
        - 新闻分析师 (News Analyst)：分析近期新闻和宏观经济趋势
        - 社交媒体分析师 (Social Media Analyst)：分析社交媒体帖子和公众情绪
    - 研究员团队 (Researchers)：为投资股票提供论证
        - 看涨研究员 (Bull Researcher)：为投资股票提供看涨论证，建立基于证据的增长潜力论证
        - 看跌研究员 (Bear Researcher)：提出反对投资股票的理由，强调风险、挑战和负面指标
    - 风险管理团队 (Risk Management)：负责策略制定和风险管理
        - 激进风险分析师 (Aggressive Debator)：积极支持高回报、高风险机会，强调大胆策略和竞争优势
        - 保守风险分析师 (Conservative Debator)：保护资产，最小化波动性，确保稳定可靠的增长
        - 中立风险分析师 (Neutral Debator)：提供平衡的观点，权衡利弊，考虑更广泛的市场趋势和经济变化
    - 管理团队 (Managers)：负责决策
        - 研究经理 (Research Manager)：评估投资辩论并做出决定性决策，制定详细的投资计划
        - 风险经理 (Risk Manager)：评估风险分析师之间的辩论，确定交易者的最佳行动方案
    - 交易员 (Trader)：基于分析团队的综合分析做出投资决策，提供具体的买入、卖出或持有建议

**执行流程**:
1. **数据收集阶段**: 四位分析师**严格串行**工作，按顺序生成专业报告
2. **投资辩论阶段**: 看涨和看跌研究员进行**双向循环**辩论
3. **研究裁决阶段**: 研究经理评估辩论并制定投资计划
4. **交易决策阶段**: 交易员基于投资计划做出交易决策
5. **风险管理阶段**: 三位风险分析师进行**三方循环**风险评估
6. **最终裁决阶段**: 风险经理做出最终交易决策