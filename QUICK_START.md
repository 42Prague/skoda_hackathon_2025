# 快速启动指南 Quick Start Guide

## 已完成的设置 ✅

1. ✓ 后端依赖已安装（Flask, flask-cors, pandas等）
2. ✓ 前端依赖已安装（React, Vite, Plotly.js等）
3. ✓ 后端代码已修复（支持数据文件缺失时启动）
4. ✓ 所有组件已创建并配置完成

## 启动服务器 🚀

### 方式1: 使用启动脚本（推荐）

**终端1 - 启动后端：**
```bash
./start_backend.sh
```

**终端2 - 启动前端：**
```bash
./start_frontend.sh
```

### 方式2: 手动启动

**终端1 - 启动后端：**
```bash
cd srcs/server
python3 run.py
```

后端将在 `http://localhost:5000` 启动

**终端2 - 启动前端：**
```bash
cd frontend
npm run dev
```

前端将在 `http://localhost:3000` 启动

## 访问应用 🌐

启动成功后，在浏览器中打开：
- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:5000

## 功能说明 📋

前端包含三个主要功能模块：

### 1. Employee Indicators Dashboard（员工指标面板）
- 查看所有员工的技能指标
- 搜索和排序功能
- 可视化进度条

### 2. Skill Clustering Visualization（技能聚类可视化）
- 交互式2D可视化（UMAP + K-Means）
- 按聚类筛选
- 显示每个聚类的顶级技能
- **注意**: 需要先运行 `employee_skill_model.py` 生成 `employee_skill_positions.csv`

### 3. Mentor Finder（导师查找器）
- 高级筛选功能
- 根据多个条件查找合适的导师
- **注意**: 需要相应的数据文件（见 `mentor_filter.py`）

## 测试后端 API 🧪

运行测试脚本：
```bash
python3 test_servers.py
```

或直接测试API端点：
```bash
curl http://localhost:5000/
curl http://localhost:5000/api/v1/skills/diagrams/export
```

## 常见问题 ❓

### Q: 数据文件缺失怎么办？
A: 服务器可以正常启动，只是没有实际数据。API会返回空列表。要使用完整功能，需要：
1. 将数据文件放在正确的位置
2. 或运行数据生成脚本

### Q: 端口被占用？
A: 修改配置文件：
- 后端端口: `srcs/server/config/settings.py` 中的 `PORT = 5000`
- 前端端口: `frontend/vite.config.js` 中的 `port: 3000`

### Q: CORS错误？
A: 确保 `flask-cors` 已安装：
```bash
cd srcs/server
pip install flask-cors
```

## 下一步 📝

1. 确保两个服务器都在运行（后端5000端口，前端3000端口）
2. 在浏览器中打开 http://localhost:3000
3. 测试各个功能模块
4. 如需完整功能，请准备相应的数据文件

## 项目结构 📁

```
42Prague_skoda_hackathon/
├── srcs/server/          # 后端Flask应用
│   ├── api/              # API路由
│   ├── services/         # 业务逻辑
│   ├── models/           # 数据模型
│   └── run.py            # 启动脚本
├── frontend/             # 前端React应用
│   ├── src/
│   │   ├── components/   # React组件
│   │   └── App.jsx       # 主应用
│   └── package.json      # 前端依赖
├── start_backend.sh      # 后端启动脚本
├── start_frontend.sh     # 前端启动脚本
└── test_servers.py       # 服务器测试脚本
```

祝使用愉快！🎉

