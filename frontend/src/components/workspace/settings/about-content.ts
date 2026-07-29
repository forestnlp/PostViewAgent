/**
 * About 邮览官 markdown content. Inlined to avoid raw-loader dependency
 * (Turbopack cannot resolve raw-loader for .md imports).
 */
import { APP_VERSION } from "@/version";

export const aboutMarkdown = `# 📮 [关于邮览官 ${APP_VERSION}](https://github.com/forestnlp/PostViewAgent)

> **基于 DeerFlow 2.0 构建的邮政经营分析智能体**

邮览官（**Y**ou **L**an **G**uan - **P**ost **V**iew **A**gent）是一个基于 DeerFlow 2.0 构建的邮政经营分析智能体，专注于寄递业务数据分析、服务质量诊断和业务趋势预测。

---

## 🚀 核心功能

* **智能问数**: 自然语言查询邮政业务数据，自动生成 SQL 和可视化图表
* **业务诊断**: 寄递服务质量智能分析，异常预警和问题线路识别
* **趋势预测**: 业务量与收入智能预测，支持时间序列分析
* **网络优化**: 三级物流体系智能规划，路径优化和资源调度
* **子智能体协作**: 多个专业智能体协同完成复杂任务
* **长期记忆**: 记录用户偏好、业务重点和对话历史

---

## 🌟 GitHub 仓库

![Star History](https://api.star-history.com/svg?repos=forestnlp/PostViewAgent&type=Date)

在 GitHub 上探索邮览官：[github.com/forestnlp/PostViewAgent](https://github.com/forestnlp/PostViewAgent)

## 🌐 技术基础

邮览官基于 [DeerFlow 2.0](https://github.com/bytedance/deer-flow) 构建，这是一个开源的超级智能体编排框架。

## 📧 支持

如有任何问题或需要帮助，请联系邮政技术支持。

---

## 📜 许可证

邮览官基于 **MIT License** 开源。

核心框架基于 DeerFlow 2.0 (MIT License)。

---

## 🙌 致谢

我们衷心感谢为邮览官做出贡献的开源项目和贡献者。我们真正站在巨人的肩膀上。

### 核心框架
- **[DeerFlow 2.0](https://github.com/bytedance/deer-flow)**: 提供智能体编排、沙箱执行和记忆系统
- **[LangChain](https://github.com/langchain-ai/langchain)**: 强大的 LLM 交互框架
- **[LangGraph](https://github.com/langchain-ai/langgraph)**: 高级多智能体编排
- **[Next.js](https://nextjs.org/)**: 现代化的 Web 应用框架

### UI 库
- **[Shadcn](https://ui.shadcn.com/)**: 简洁的 UI 组件
- **[SToneX](https://github.com/stonexer)**: 逐字视觉效果的贡献者

这些优秀的项目构成了邮览官的核心基础，体现了开源协作的变革力量。

### 特别感谢
最后，我们要向 DeerFlow 1.0 和 2.0 的核心作者表达最诚挚的感谢：

- **[Daniel Walnut](https://github.com/hetaoBackend/)**
- **[Henry Li](https://github.com/magiccube/)**

没有他们的愿景、激情和奉献，邮览官就不会是今天的模样。
`;
