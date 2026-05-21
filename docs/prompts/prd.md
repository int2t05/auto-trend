# 初始需求
一个 Actions 自动化层
 1. GitHub Actions 定时触发
  2. 拉取 GitHub Trending https://zread.ai上的项目
  3. 抓 README / 基础元数据
  4. 调 LLM 做结构化分析
  5. 生成 Markdown
  6. 直接 commit 回仓库
githubpages上可以直接浏览docs
做每日的定时任务 自动爬取然后分析 生成日报

# 约束
整个是一个薄层 然后分析采用相似开源仓库的分析方法