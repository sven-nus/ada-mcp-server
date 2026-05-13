# ADA MCP Server

AWS DevOps Agent (ADA) 的 MCP (Model Context Protocol) 服务器，让 AI 助手（如 Kiro CLI、Claude Desktop 等）能够直接调用 ADA 的能力。

## 功能

| 工具 | 说明 |
|------|------|
| `ada_chat` | 向 ADA 发送消息并获取回复（事件调查、运维咨询等） |
| `ada_list_recommendations` | 列出 ADA 的优化建议 |
| `ada_get_recommendation` | 获取特定建议的详细信息 |
| `ada_list_services` | 列出已注册的服务 |
| `ada_list_goals` | 列出运维目标 |
| `ada_list_journal` | 查看审计日志 |
| `ada_list_executions` | 列出最近的执行记录 |
| `ada_get_usage` | 查看账户用量 |

## 前置要求

- Python 3.10+
- AWS 账户已开通 DevOps Agent (ADA) 服务
- 已创建 Agent Space 并获取 Space ID
- AWS credentials 已配置（支持 profile）

## 安装

```bash
pip install mcp boto3
```

或使用 uv：

```bash
uv pip install mcp boto3
```

## 配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ADA_AGENT_SPACE_ID` | ADA Agent Space ID（必需） | - |
| `AWS_DEFAULT_REGION` | AWS 区域 | us-east-1 |
| `AWS_PROFILE` | AWS 配置文件名 | default |

### Kiro CLI 配置

编辑 `~/.kiro/settings/mcp.json`，添加：

```json
{
  "mcpServers": {
    "ada-devops": {
      "command": "python3",
      "args": ["-u", "/path/to/ada_mcp_server.py"],
      "timeout": 30000,
      "env": {
        "ADA_AGENT_SPACE_ID": "your-agent-space-id",
        "AWS_PROFILE": "your-profile",
        "AWS_DEFAULT_REGION": "us-west-2"
      }
    }
  }
}
```

### Claude Desktop 配置

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "ada-devops": {
      "command": "python3",
      "args": ["-u", "/path/to/ada_mcp_server.py"],
      "env": {
        "ADA_AGENT_SPACE_ID": "your-agent-space-id",
        "AWS_DEFAULT_REGION": "us-west-2"
      }
    }
  }
}
```

## 使用示例

配置完成后，AI 助手可以直接调用 ADA 工具：

- "用 ADA 查看我账号下的 EC2 实例"
- "ADA 有什么优化建议？"
- "查看 ADA 用量"
- "问 ADA 关于 EFS 跨可用区流量费的问题"

## 获取 Agent Space ID

1. 登录 AWS Console
2. 进入 DevOps Agent (ADA) 服务
3. 在 Agent Spaces 页面找到或创建你的 Space
4. 复制 Space ID

## 工作原理

```
AI 助手 (Kiro/Claude) <--MCP协议--> ada_mcp_server.py <--boto3--> AWS DevOps Agent API
```

服务器通过 stdio 传输与 AI 助手通信，使用 boto3 调用 AWS DevOps Agent API。聊天功能使用流式响应，实时收集 ADA 的回复。

## License

MIT
