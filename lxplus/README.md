# CORSIKA Agent — lxplus 快速上手

## 0. 前置条件

CERN 账号（能登录 lxplus）
AIGW API key：https://aigw.cern.ch/ui/?page=api-keys （Models 选 "All Team Models"）
CORSIKA 7.8010：使用 Zhuo 的副本，需他先开读权限，无需自装

## 1. 安装 opencode

ssh lxplus.cern.ch
curl -fsSL https://opencode.ai/install | bash
source ~/.bashrc
opencode --version    # 应显示 1.x

## 2. 配置 API key

echo 'export CERN_AI_API_KEY="你的key"' >> ~/.bashrc
source ~/.bashrc

## 3. 获取 Agent 并安装命令

git clone https://github.com/CZ-COLLAB/corsika-agent.git
ln -s "$(pwd)/corsika-agent/lxplus/corsika-cli" ~/.local/bin/corsika-agent
source corsika-agent/lxplus/setup.sh

## 4. 选择模型并冒烟测试

corsika-agent models
echo 'export CERN_AI_MODEL="模型名"' >> ~/.bashrc && source ~/.bashrc
corsika-agent smoke "列出 run/ 下编译好的 CORSIKA 可执行文件，并说明各自的强子相互作用模型"

## 5. 日常使用

corsika-agent my-shower                      # 交互式 TUI（/exit 退出）
corsika-agent my-shower "任务描述"            # 一次性命令
corsika-agent -m 模型名 my-shower "任务描述"   # 临时换模型
corsika-agent list                           # 工作区列表

## 6. 大统计量任务

corsika-agent my-shower "用 HTCondor 跑 100 个种子、每个 1000 showers，输出放到工作区 condor/ 下"

## 7. 常见问题

CORSIKA 不可读 → 让 Zhuo 开读权限；或自装后: export CORSIKA_ROOT=/path/to/corsika-78010
models 401/403 → key 错误或没选 "All Team Models"，重建 key
模型名无效 → 重新跑 corsika-agent models
其他 → https://ml.docs.cern.ch/aigw/gettingstarted/
