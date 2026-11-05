# CORSIKA Agent — lxplus 快速上手指南

在 lxplus 上通过 opencode 直接使用 CORSIKA 7 研究 Agent（终端 TUI 交互 + 一次性命令）。
模型通过 CERN AI Gateway（AIGW）调用，无需任何外部 API key。

---

## 0. 你需要准备的

| 项目 | 说明 |
|---|---|
| CERN 账号 | 能登录 lxplus 即可 |
| AIGW API key | 到 https://aigw.cern.ch/ui/?page=api-keys 创建；**Team 选 sandbox，Models 选 "All Team Models"** |
| CORSIKA 7.8010 | 默认使用 Zhuo 提供的编译副本 `/eos/user/z/zhuoch/corsika-78010`（需要他先给你开读权限），无需自己安装 |

## 1. 安装 opencode（一次性）

```bash
ssh lxplus.cern.ch
curl -fsSL https://opencode.ai/install | bash
# 退出并重新登录，使 ~/.opencode/bin 进入 PATH
opencode --version   # 应显示 1.x
```

## 2. 配置 API key（一次性）

```bash
cat >> ~/.bashrc <<'EOF'
export CERN_AI_API_KEY="你的AIGW密钥"
EOF
source ~/.bashrc
```

密钥只存在于环境变量中，不会写入任何文件或命令行参数。

## 3. 获取 Agent 并自检

```bash
git clone https://github.com/CZ-COLLAB/corsika-agent.git
source corsika-agent/lxplus/setup.sh
```

四项检查（opencode / 网关连通 / API key / CORSIKA 可读）全部 OK 才继续。

## 4. 选择模型并试运行

```bash
# 查看你的 key 能用哪些模型（模型名以命令输出为准）
./corsika-agent/lxplus/corsika-cli models

# 把选定的模型写进 ~/.bashrc，例如：
echo 'export CERN_AI_MODEL="gpt-oss-120b"' >> ~/.bashrc && source ~/.bashrc

# 冒烟测试（约1分钟，Agent 会实际读取 CORSIKA 目录）
./corsika-agent/lxplus/corsika-cli smoke "列出 run/ 目录下编译好的 CORSIKA 可执行文件，并说明各自的强子相互作用模型"
```

## 5. 日常使用

```bash
CL=corsika-agent/lxplus/corsika-cli

# 交互式 TUI（推荐；工作区 my-shower 自动创建）
$CL my-shower

# 一次性命令
$CL my-shower "生成一张 1-proton 簇射 steering card（SIBYLL+URQMD，E=1 TeV，
固定种子），运行 1 个簇射做冒烟测试，并确认 DAT 输出文件正常生成"

# 临时换模型
$CL -m claude-sonnet-4 my-shower "..."

# 查看已有工作区
$CL list
```

- 每个工作区位于 `/eos/user/<首字母>/<你的用户名>/corsika-agent-workspaces/<名字>/`，
  内含 Agent 自动注入的 4 份 CORSIKA 知识文档（`.opencode/skills/corsika7/`），
  聊天记录、steering card、DAT 输出、绘图脚本都保存在这里。
- TUI 中用 `/exit` 退出；工作区可反复进入，历史全部保留。
- Agent 默认只允许读写你的工作区和 CORSIKA 目录，`sudo/ssh/scp/pip` 等命令被禁止。

## 6. 大统计量任务

不要在 lxplus 登录节点上串行跑大量簇射。让 Agent 用 HTCondor 提交
（`condor_submit`，每个种子一个 job，输出写回工作区），直接告诉它即可，例如：

> 用 HTCondor 把这个模拟跑 100 个不同种子的簇射，每个 1000 showers，输出放到工作区 condor/ 下。

## 7. 常见问题

| 现象 | 处理 |
|---|---|
| `setup.sh` 报 CORSIKA 不可读 | 让 Zhuo 给你的账号开读权限；或自己注册下载 CORSIKA 后 `export CORSIKA_ROOT=你的路径` |
| `corsika-cli models` 401/403 | API key 错误，或建 key 时没选 "All Team Models"；到 AIGW UI 重建 |
| 模型名无效 | 模型列表会变化，重新跑 `corsika-cli models` 确认名字 |
| Agent 找不到 CORSIKA | 确认 `echo $MUON_CORSIKA7_ROOT`（脚本自动设置），必要时 `export CORSIKA_ROOT=...` |
| 输出太大占满 EOS 配额 | 簇射数/减薄(thinning)参数让 Agent 帮你控制；`lfs quota /eos/user/<首字母>/<用户名>` 查看配额 |
| opencode 报 provider 错误 | 先用 curl 验证 key：见 https://ml.docs.cern.ch/aigw/gettingstarted/ |

## 8. 技术说明（可选阅读）

- Agent = opencode + 4 份 CORSIKA prompt 文档（skill），无额外框架；编译、运行、分析均由 Agent 在你的工作区内自主完成。
- 每次启动注入 `OPENCODE_CONFIG_CONTENT`：CERN AI Gateway provider、目录白名单、bash 命令黑名单。
- 脚本位于 `lxplus/corsika-cli`，环境变量均可覆盖（`CERN_AI_BASE_URL`、`CORSIKA_ROOT`、`WORKSPACE_PARENT`）。
- 需要网页界面的话另见主 README 的 Web UI 部署说明（当前适配版仅面向 CLI/TUI）。
