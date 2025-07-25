import streamlit as st
import time
import os
import json
import random

# 模拟Strands Agent和Swarm功能
class MockAgent:
    def __init__(self, tools=None):
        self.tool = MockSwarmTool()

class MockSwarmTool:
    def swarm(self, task, swarm_size, coordination_pattern, phases=1):
        """模拟swarm工具的功能，返回模拟的结果"""
        # 生成模拟的智能体响应
        content = []
        
        # 添加头部信息
        content.append({"text": "Swarm initialized"})
        content.append({"text": f"Task: {task}"})
        
        # 为每个阶段生成智能体响应
        for phase in range(phases):
            for agent_id in range(1, swarm_size + 1):
                # 生成模拟的响应内容
                response_text = self._generate_mock_response(
                    agent_id, task, coordination_pattern, phase
                )
                
                # 添加响应
                content.append({
                    "text": f"🤖 Agent agent_{agent_id}: Response: {response_text}",
                    "agent_id": f"agent_{agent_id}",
                    "phase": phase
                })
                
                # 添加模拟的指标
                metrics_text = self._generate_mock_metrics()
                content.append({
                    "text": f"🤖 Agent agent_{agent_id}: Metrics: {metrics_text}",
                    "agent_id": f"agent_{agent_id}",
                    "phase": phase
                })
        
        # 返回模拟结果
        return {"content": content}
    
    def _generate_mock_response(self, agent_id, task, coordination_pattern, phase):
        """生成模拟的智能体响应"""
        # 根据任务类型生成不同的响应
        if "科学论文" in task or "paper" in task.lower():
            if coordination_pattern == "collaborative":
                return self._generate_paper_analysis_collaborative(agent_id, phase)
            elif coordination_pattern == "competitive":
                return self._generate_paper_analysis_competitive(agent_id)
            else:  # hybrid
                if agent_id % 2 == 0:
                    return self._generate_paper_analysis_collaborative(agent_id, phase)
                else:
                    return self._generate_paper_analysis_competitive(agent_id)
        elif "商业计划" in task or "business plan" in task.lower():
            if coordination_pattern == "collaborative":
                return self._generate_business_plan_collaborative(agent_id, phase)
            else:
                return self._generate_business_plan_competitive(agent_id)
        else:
            # 通用响应
            return self._generate_generic_response(agent_id, task, coordination_pattern)
    
    def _generate_paper_analysis_collaborative(self, agent_id, phase):
        """生成协作模式下的论文分析响应"""
        if phase == 0:
            responses = [
                "# 论文分析初步框架\n\n作为第一个参与分析的智能体，我注意到我们没有具体的论文可供分析。为了进行有效的分析，我们需要：\n\n1. 论文的标题和作者\n2. 论文的摘要或全文\n3. 研究领域背景\n\n一旦获得论文，我将关注：\n- 研究问题和假设\n- 方法论评估\n- 主要发现及其统计显著性\n- 作者的解释和结论\n- 研究局限性",
                "# 科学论文分析\n\n我注意到目前没有提供具体的科学论文。为了进行全面分析，我需要：\n- 论文全文或至少摘要\n- 出版信息和作者\n- 研究领域\n\n获得论文后，我将分析：\n1. 研究设计和方法\n2. 数据收集和分析技术\n3. 主要发现及其意义\n4. 与现有文献的关系\n5. 实际应用价值",
                "# 论文分析协作框架\n\n我将建立一个分析框架，帮助我们识别论文的关键发现。由于目前没有具体论文，我提议以下协作方法：\n\n1. **结构评估**：\n   - 分析摘要、方法、结果和讨论部分\n   - 识别核心研究问题\n\n2. **发现评估标准**：\n   - 统计显著性\n   - 方法创新性\n   - 与现有文献的关系\n   - 作者承认的局限性\n\n3. **协作策略**：\n   - 每个智能体从不同角度识别发现\n   - 基于科学影响力和创新性优先排序发现"
            ]
            return responses[agent_id % len(responses)]
        else:
            responses = [
                "# 论文分析框架整合\n\n基于之前阶段的讨论，我注意到我们都认识到缺少具体论文。我提议以下分析结构：\n\n1. **研究背景与问题**\n   - 主要研究目标\n   - 与现有文献的关系\n   - 测试的假设\n\n2. **方法论评估**\n   - 研究设计和程序\n   - 样本特征和规模\n   - 分析技术\n\n一旦获得论文，我们可以使用这个框架进行详细分析。",
                "# 综合分析框架\n\n整合前一阶段的见解，我发现我们都认识到缺少实际论文。作为智能体2，我将专注于：\n\n1. **核心贡献识别**\n   - 论文提出了什么新发现或理论进展？\n   - 如何解决现有文献中的空白？\n   - 解决了什么问题？\n\n2. **证据评估**\n   - 数据质量和样本规模\n   - 统计方法和结果显著性\n   - 可重复性考虑\n\n我将整合其他智能体的见解，构建对关键发现的全面理解。",
                "# 协作分析策略\n\n我注意到我们都认识到缺少具体论文。为了优化我们的协作，我提议：\n\n1. **知识整合**\n   - 每个智能体识别关键发现但强调不同方面\n   - 交叉引用发现以建立对主要结论的信心\n   - 链接互补见解以构建全面理解\n\n2. **评估标准**\n   - 科学严谨性和方法可靠性\n   - 超越现有文献的创新性\n   - 实际应用和现实世界影响\n\n这种协作方法将确保我们的分析既全面又连贯。"
            ]
            return responses[agent_id % len(responses)]
    
    def _generate_paper_analysis_competitive(self, agent_id):
        """生成竞争模式下的论文分析响应"""
        responses = [
            "# 科学论文分析 - 智能体1\n\n由于没有提供具体的科学论文，我将概述我分析科学论文的方法：\n\n## 系统分析方法\n\n1. **摘要和引言审查**\n   - 识别论文的核心研究问题和假设\n   - 注意作者声明的研究意义\n   - 理解所解决的研究空白\n\n2. **方法评估**\n   - 评估实验设计和统计方法\n   - 评价样本规模和选择标准\n   - 识别方法的潜在优势或局限性\n\n我准备好在提供具体论文时应用这个框架。",
            "# 科学论文分析 - 竞争智能体2\n\n我需要看到实际的科学论文才能分析其关键发现。任务指令中没有包含论文本身或任何相关细节。为了正确分析科学论文，我需要：\n\n1. 论文全文或至少摘要\n2. 作者、出版日期和期刊信息\n3. 学科领域\n\n请提供您希望我分析的科学论文，我将提供其关键发现的全面评述，并提供独特见解。",
            "# 科学论文分析：关键发现\n\n作为专注于独特解决方案的智能体3，我需要分析科学论文并识别关键发现。然而，我注意到实际要分析的科学论文尚未在提示中提供。\n\n为了有效进行，我需要：\n- 论文标题\n- 作者\n- 论文全文或至少摘要\n- 研究领域\n\n请提供您希望我分析的科学论文，我将提供关注独特见解的重点分析。"
        ]
        return responses[agent_id % len(responses)]
    
    def _generate_business_plan_collaborative(self, agent_id, phase):
        """生成协作模式下的商业计划分析响应"""
        if phase == 0:
            responses = [
                "# 商业计划分析 - 市场研究\n\n作为负责市场研究的智能体，我将分析目标市场的规模、增长趋势和客户需求。我建议我们首先确定：\n\n1. 目标市场的规模和增长率\n2. 主要客户群体及其特点\n3. 市场痛点和未满足的需求\n4. 竞争格局分析\n\n我将与其他智能体协作，确保我们的商业计划建立在坚实的市场理解基础上。",
                "# 商业计划分析 - 财务规划\n\n作为财务规划智能体，我将专注于商业计划的财务可行性。我计划分析：\n\n1. 初始投资需求\n2. 收入模型和定价策略\n3. 成本结构分析\n4. 盈亏平衡点计算\n5. 5年财务预测\n\n我期待与其他智能体协作，确保财务计划与市场策略和运营计划保持一致。",
                "# 商业计划分析 - 运营策略\n\n作为运营策略智能体，我将关注业务的日常运作和资源需求。我的分析将包括：\n\n1. 供应链和物流规划\n2. 人力资源需求\n3. 技术基础设施\n4. 质量控制流程\n5. 扩展策略\n\n我将与市场和财务智能体密切合作，确保运营计划支持整体业务目标。"
            ]
            return responses[agent_id % len(responses)]
        else:
            responses = [
                "# 商业计划整合 - 市场与财务协调\n\n基于第一阶段的分析，我已将市场研究与财务规划整合。我们的目标市场显示年增长率为15%，这支持我们的财务预测。关键发现：\n\n1. 客户获取成本与终身价值比率为1:3，表明良好的投资回报\n2. 市场细分显示三个主要客户群体，每个群体需要不同的定价策略\n3. 竞争分析表明我们可以通过服务差异化获得10%的市场份额\n\n我建议下一阶段关注具体的市场进入策略。",
                "# 商业计划整合 - 财务与运营协调\n\n整合财务和运营分析后，我发现几个关键协同点：\n\n1. 规模经济可在第3年实现，将运营成本降低20%\n2. 初始投资需求可通过分阶段实施减少30%\n3. 技术基础设施投资将提高运营效率，提升利润率\n\n建议优先考虑自动化投资，以支持长期财务可持续性。",
                "# 商业计划整合 - 全面战略\n\n综合所有智能体的分析，我提出以下整合战略：\n\n1. **差异化价值主张**：基于市场分析，专注于竞争对手忽视的客户痛点\n2. **灵活定价模型**：采用基于价值的定价，反映我们在不同市场细分中的独特优势\n3. **精益运营**：初期采用外包模式降低固定成本，随业务增长逐步内部化关键功能\n4. **阶段性扩张**：基于财务里程碑的明确扩张路径\n\n这种整合方法平衡了增长野心与财务审慎。"
            ]
            return responses[agent_id % len(responses)]
    
    def _generate_business_plan_competitive(self, agent_id):
        """生成竞争模式下的商业计划分析响应"""
        responses = [
            "# 创新型商业计划方案\n\n我提出一个基于订阅模式的商业计划，具有以下优势：\n\n1. **可预测的收入流**：月度订阅确保稳定现金流\n2. **客户锁定**：提高客户终身价值和忠诚度\n3. **数据驱动决策**：持续获取用户行为数据，实现产品优化\n4. **规模经济**：边际成本随用户增长而降低\n\n财务预测显示第2年实现盈亏平衡，第4年实现25%的利润率。这种模式优于传统一次性购买模式，提供更高的长期价值。",
            "# 市场渗透型商业计划\n\n我的商业计划专注于快速市场渗透策略：\n\n1. **免费增值模式**：基础功能免费，高级功能付费\n2. **病毒式获客**：内置社交分享和推荐奖励机制\n3. **战略合作伙伴关系**：与现有市场参与者合作，快速获取用户群\n4. **敏捷产品迭代**：每两周发布新功能，基于用户反馈\n\n这种方法将在18个月内实现15%的市场份额，优于竞争对手提出的缓慢增长模式。",
            "# 利基市场商业计划\n\n我提出专注于被忽视的利基市场的商业计划：\n\n1. **专业化服务**：为特定行业客户提供深度定制解决方案\n2. **高利润率**：专业知识允许溢价定价，实现40%的毛利率\n3. **低竞争压力**：大型竞争对手忽视的市场细分\n4. **口碑营销**：依靠客户推荐和行业声誉而非昂贵的广告\n\n这种专注策略比广泛市场方法更具可行性，特别是对于资源有限的新企业。财务模型显示初始投资需求低50%，回报周期短40%。"
        ]
        return responses[agent_id % len(responses)]
    
    def _generate_generic_response(self, agent_id, task, coordination_pattern):
        """生成通用响应"""
        if coordination_pattern == "collaborative":
            responses = [
                f"# 任务分析 - 智能体{agent_id}\n\n我已分析了任务：\"{task}\"。\n\n作为协作团队的一部分，我建议我们首先明确任务目标和范围，然后分配专门的分析领域给每个智能体。我将专注于[特定方面]，并期待与其他智能体的见解整合以形成全面解决方案。",
                f"# 协作分析 - 智能体{agent_id}\n\n关于任务：\"{task}\"，我注意到这需要多角度分析。\n\n我将贡献以下方面的专业知识：\n1. 问题的历史背景\n2. 当前解决方案的局限性\n3. 创新方法的可能性\n\n我期待与其他智能体的发现整合，以构建更全面的理解。",
                f"# 任务协作框架 - 智能体{agent_id}\n\n针对\"{task}\"，我提议以下协作框架：\n\n1. 问题分解\n2. 并行分析\n3. 见解整合\n4. 解决方案合成\n\n我将专注于[特定领域]，并期待与团队其他成员的协作。"
            ]
            return responses[agent_id % len(responses)]
        else:
            responses = [
                f"# 独立分析 - 智能体{agent_id}\n\n我已独立分析了任务：\"{task}\"。\n\n我的独特方法包括：\n1. 全面的问题分解\n2. 创新解决方案设计\n3. 实施考虑\n\n我相信我的方法提供了最有效的解决路径，因为它平衡了创新性和实用性。",
                f"# 竞争性解决方案 - 智能体{agent_id}\n\n对于\"{task}\"，我提出以下独特解决方案：\n\n1. [创新方法]\n2. [实施策略]\n3. [预期结果]\n\n我的方法优于传统方法，因为它解决了常见的效率和可扩展性问题。",
                f"# 优化方案 - 智能体{agent_id}\n\n我为\"{task}\"设计了一个优化解决方案，专注于：\n\n1. 性能效率\n2. 资源优化\n3. 长期可持续性\n\n我的方法通过创新技术和系统思考提供了卓越的结果。"
            ]
            return responses[agent_id % len(responses)]
    
    def _generate_mock_metrics(self):
        """生成模拟的指标数据"""
        cycle_time = round(random.uniform(3.5, 8.5), 3)
        tokens_in = random.randint(200, 300)
        tokens_out = random.randint(150, 300)
        latency = int(cycle_time * 1000 - random.randint(10, 30))
        
        return f"Event Loop Metrics Summary:\n├─ Cycles: total=1, avg_time={cycle_time}s, total_time={cycle_time}s\n├─ Tokens: in={tokens_in}, out={tokens_out}, total={tokens_in + tokens_out}\n├─ Latency: {latency}ms\n├─ Tool Usage:\n├─ Execution Trace:\n   └─ None - Duration: {cycle_time}s\n      └─ None - Duration: {cycle_time}s"

# 页面配置
st.set_page_config(
    page_title="Strands Swarm Agent Demo",
    page_icon="🤖",
    layout="wide",
)

# 标题和介绍
st.title("🤖 Strands Swarm Agent Demo")
st.markdown("""
## 多智能体群体协作演示

这个应用程序演示了使用Strands Agents SDK创建的智能体群体（Swarm）如何协同工作来解决复杂问题。
智能体群体是一组自主AI智能体，它们通过协作共同解决复杂问题。

### 群体智能的特点:
- **分布式问题解决**: 将复杂任务分解为可并行处理的子任务
- **信息共享**: 智能体交换见解以构建集体知识
- **专业化**: 不同智能体专注于问题的特定方面
- **冗余**: 多个智能体处理类似任务提高可靠性
- **涌现智能**: 系统表现出超越其单个组件的能力

### 示例任务:
- 分析科学论文并找出关键发现
- 评估商业计划的优缺点
- 为复杂问题提供多角度解决方案
""")

# 创建侧边栏
st.sidebar.title("配置参数")

# 任务选择
task_options = {
    "paper_analysis": "分析这篇科学论文并找出关键发现",
    "business_plan": "评估这个商业计划的优缺点",
    "climate_change": "提出解决气候变化的创新方法",
    "app_design": "为一个新的移动应用设计用户界面",
    "marketing": "为初创公司制定营销策略"
}

task_selection = st.sidebar.selectbox(
    "选择任务类型",
    options=list(task_options.keys()),
    format_func=lambda x: task_options[x]
)

# 自定义任务
custom_task = st.sidebar.text_area("或输入自定义任务", height=80)
task = custom_task if custom_task else task_options[task_selection]

# 其他配置参数
swarm_size = st.sidebar.slider("群体大小", min_value=2, max_value=10, value=5)
coordination_pattern = st.sidebar.selectbox(
    "协调模式",
    options=["collaborative", "competitive", "hybrid"],
    format_func=lambda x: {
        "collaborative": "协作模式 (智能体基于彼此的见解构建)",
        "competitive": "竞争模式 (智能体独立开发解决方案)",
        "hybrid": "混合模式 (平衡协作与独立探索)"
    }.get(x)
)

phases = st.sidebar.slider("阶段数", min_value=1, max_value=3, value=1)

# 创建两列布局
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 群体智能工作原理")
    st.markdown("""
    1. **初始化**: 创建具有共享内存和专业化智能体的群体
    2. **阶段处理**: 智能体使用ThreadPoolExecutor并行工作
    3. **知识共享**: 智能体从共享内存中存储和检索信息
    4. **结果收集**: 来自所有智能体的结果被聚合并呈现
    """)

    st.markdown("### 协调模式说明")
    st.markdown("""
    - **协作模式**: 智能体基于其他智能体的见解构建，寻求共识
    - **竞争模式**: 智能体独立开发解决方案，提供多样化的视角
    - **混合模式**: 平衡协作与独立探索，结合两种模式的优点
    """)
    
    # 添加多阶段工作流程说明
    if phases > 1:
        st.markdown("### 多阶段工作流程")
        st.markdown(f"""
        您选择了 {phases} 个阶段的工作流程:
        
        1. **第1阶段**: 智能体独立分析问题并提出初步框架
        2. **第2阶段**: 智能体查看第1阶段的所有输出，构建更全面的解决方案
        {"3. **第3阶段**: 智能体整合前两个阶段的见解，提出最终综合方案" if phases > 2 else ""}
        
        多阶段工作流程允许智能体在后续阶段中利用之前阶段的集体知识。
        """)

with col2:
    # 运行按钮
    if st.button("运行群体智能体", type="primary"):
        with st.spinner("智能体群体正在工作中..."):
            try:
                # 创建模拟智能体
                agent = MockAgent()
                
                # 运行群体
                start_time = time.time()
                result = agent.tool.swarm(
                    task=task,
                    swarm_size=swarm_size,
                    coordination_pattern=coordination_pattern,
                    phases=phases
                )
                end_time = time.time()
                
                # 显示结果
                st.success(f"群体智能体完成任务! 耗时: {end_time - start_time:.2f} 秒")
                
                # 显示智能体输出
                st.markdown("### 群体智能体输出")
                
                # 显示原始输出
                with st.expander("查看原始输出"):
                    st.json(result)
                
                # 提取并显示每个智能体的响应
                st.markdown("### 智能体响应")
                
                # 创建选项卡以显示不同阶段的结果
                if phases > 1:
                    tabs = st.tabs([f"阶段 {i+1}" for i in range(phases)])
                    
                    for phase_idx, tab in enumerate(tabs):
                        with tab:
                            # 过滤当前阶段的响应
                            phase_responses = [
                                item for item in result.get("content", [])[2:]
                                if isinstance(item, dict) and 
                                "text" in item and 
                                "Response:" in item["text"] and
                                f"\"phase\": {phase_idx}" in str(item)
                            ]
                            
                            for i, response in enumerate(phase_responses):
                                agent_id = response["text"].split("Agent ")[1].split(":")[0]
                                response_text = response["text"].split("Response:")[1].strip()
                                st.markdown(f"#### 智能体 {agent_id}")
                                st.markdown(response_text)
                                st.divider()
                else:
                    # 单阶段情况
                    responses = [
                        item for item in result.get("content", [])[2:]
                        if isinstance(item, dict) and 
                        "text" in item and 
                        "Response:" in item["text"]
                    ]
                    
                    for i, response in enumerate(responses):
                        if "Agent " in response["text"]:
                            agent_id = response["text"].split("Agent ")[1].split(":")[0]
                            response_text = response["text"].split("Response:")[1].strip()
                            st.markdown(f"#### 智能体 {agent_id}")
                            st.markdown(response_text)
                            st.divider()
            
            except Exception as e:
                st.error(f"发生错误: {str(e)}")
                st.info("请确保您已设置正确的API密钥环境变量。")

# 添加说明
st.sidebar.markdown("---")
st.sidebar.markdown("### 关于此演示")
st.sidebar.markdown("""
此演示使用模拟数据展示了多智能体群体系统的工作原理。
在实际应用中，这些智能体可以连接到大语言模型API以执行真实任务。
""")

# 页脚
st.markdown("---")
st.markdown("Strands Swarm Agent Demo | 基于Strands Agents SDK构建")