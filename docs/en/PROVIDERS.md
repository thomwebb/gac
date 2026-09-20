# AI Provider Configuration Guide

**English** | [简体中文](../zh-CN/PROVIDERS.md) | [繁體中文](../zh-TW/PROVIDERS.md) | [日本語](../ja/PROVIDERS.md) | [한국어](../ko/PROVIDERS.md) | [हिन्दी](../hi/PROVIDERS.md) | [Tiếng Việt](../vi/PROVIDERS.md) | [Français](../fr/PROVIDERS.md) | [Русский](../ru/PROVIDERS.md) | [Español](../es/PROVIDERS.md) | [Português](../pt/PROVIDERS.md) | [Norsk](../no/PROVIDERS.md) | [Svenska](../sv/PROVIDERS.md) | [Deutsch](../de/PROVIDERS.md) | [Nederlands](../nl/PROVIDERS.md) | [Italiano](../it/PROVIDERS.md)

---

This guide provides configuration examples for all **35+ AI providers** supported by gac.

## Quick Reference Table

| Provider             | Provider ID        | Model Format                                                  | Auth Type        | Required Env Vars                                                           | Optional Env Vars                                                  |
| -------------------- | ------------------ | ------------------------------------------------------------- | ---------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| **Anthropic**        | `anthropic`        | `anthropic:claude-sonnet-5`                                   | API Key          | `ANTHROPIC_API_KEY`                                                         | —                                                                  |
| **Azure OpenAI**     | `azure-openai`     | `azure-openai:my-deployment-name`                             | API Key          | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION` | —                                                                  |
| **Cerebras**         | `cerebras`         | `cerebras:zai-glm-4.7`                                        | API Key          | `CEREBRAS_API_KEY`                                                          | `CEREBRAS_BASE_URL`                                                |
| **ChatGPT OAuth**    | `chatgpt-oauth`    | `chatgpt-oauth:gpt-5.6-luna`                                  | OAuth            | —                                                                           | `CHATGPT_OAUTH_TOKEN`                                              |
| **Chutes.ai**        | `chutes`           | `chutes:deepseek-ai/DeepSeek-V3-0324`                         | API Key          | `CHUTES_API_KEY`                                                            | `CHUTES_BASE_URL`                                                  |
| **Claude Code**      | `claude-code`      | `claude-code:claude-sonnet-5`                                 | OAuth            | `CLAUDE_CODE_ACCESS_TOKEN`                                                  | —                                                                  |
| **Copilot (GitHub)** | `copilot`          | `copilot:gpt-5.6-luna`                                        | OAuth            | —                                                                           | `GITHUB_COPILOT_TOKEN`                                             |
| **Crof.ai**          | `crof`             | `crof:claude-sonnet-5`                                        | API Key          | `CROF_API_KEY`                                                              | `CROF_BASE_URL`                                                    |
| **Custom Anthropic** | `custom-anthropic` | `custom-anthropic:claude-sonnet-5`                            | API Key          | `CUSTOM_ANTHROPIC_API_KEY`, `CUSTOM_ANTHROPIC_BASE_URL`                     | `CUSTOM_ANTHROPIC_VERSION`                                         |
| **Custom OpenAI**    | `custom-openai`    | `custom-openai:gpt-5.6-luna`                                  | API Key          | `CUSTOM_OPENAI_API_KEY`, `CUSTOM_OPENAI_BASE_URL`                           | —                                                                  |
| **DeepInfra**        | `deepinfra`        | `deepinfra:meta-llama/Llama-3.3-70B-Instruct`                 | API Key          | `DEEPINFRA_API_KEY`                                                         | `DEEPINFRA_BASE_URL`                                               |
| **DeepSeek**         | `deepseek`         | `deepseek:deepseek-flash`                                     | API Key          | `DEEPSEEK_API_KEY`                                                          | `DEEPSEEK_BASE_URL`                                                |
| **Fireworks AI**     | `fireworks`        | `fireworks:accounts/fireworks/models/llama-v3p1-70b-instruct` | API Key          | `FIREWORKS_API_KEY`                                                         | `FIREWORKS_BASE_URL`                                               |
| **Gemini (Google)**  | `gemini`           | `gemini:gemini-3.5-flash-lite`                                | API Key          | `GEMINI_API_KEY`                                                            | `GEMINI_BASE_URL`                                                  |
| **Groq**             | `groq`             | `groq:openai/gpt-oss-120b`                                    | API Key          | `GROQ_API_KEY`                                                              | `GROQ_BASE_URL`                                                    |
| **Kimi for Coding**  | `kimi-for-coding`  | `kimi-for-coding:kimi-for-coding`                             | API Key          | `KIMI_API_KEY`                                                              | `KIMI_BASE_URL`                                                    |
| **LM Studio**        | `lm-studio`        | `lm-studio:local-model-name`                                  | Optional API Key | —                                                                           | `LMSTUDIO_API_URL`, `LMSTUDIO_API_KEY`                             |
| **MiniMax**          | `minimax`          | `minimax:MiniMax-M3`                                          | API Key          | `MINIMAX_API_KEY`                                                           | `MINIMAX_BASE_URL`                                                 |
| **Mistral AI**       | `mistral`          | `mistral:devstral-2512`                                       | API Key          | `MISTRAL_API_KEY`                                                           | `MISTRAL_BASE_URL`                                                 |
| **Moonshot AI**      | `moonshot`         | `moonshot:kimi-k3`                                            | API Key          | `MOONSHOT_API_KEY`                                                          | `MOONSHOT_BASE_URL`                                                |
| **Neuralwatt**       | `neuralwatt`       | `neuralwatt:nemotron-3-ultra`                                 | API Key          | `NEURALWATT_API_KEY`                                                        | `NEURALWATT_BASE_URL`                                              |
| **Ollama**           | `ollama`           | `ollama:gemma4`                                               | Optional API Key | —                                                                           | `OLLAMA_API_URL`, `OLLAMA_API_KEY`                                 |
| **Ollama Cloud**     | `ollama-cloud`     | `ollama-cloud:gpt-oss:120b-cloud`                             | API Key          | `OLLAMA_CLOUD_API_KEY`                                                      | `OLLAMA_CLOUD_BASE_URL`                                            |
| **OpenAI**           | `openai`           | `openai:gpt-5.6-luna`                                         | API Key          | `OPENAI_API_KEY`                                                            | `OPENAI_BASE_URL`, `OPENAI_ORG_ID`                                 |
| **OpenCode Go**      | `opencode-go`      | `opencode-go:codellama`                                       | API Key          | `OPENCODE_GO_API_KEY`                                                       | `OPENCODE_GO_BASE_URL`                                             |
| **OpenRouter**       | `openrouter`       | `openrouter:anthropic/claude-3.5-sonnet`                      | API Key          | `OPENROUTER_API_KEY`                                                        | `OPENROUTER_BASE_URL`, `OPENROUTER_REFERER`, `OPENROUTER_APP_NAME` |
| **Plexus Gateway**   | `plexus`           | `plexus:gpt-5.6-luna`                                         | API Key          | `PLEXUS_API_KEY`                                                            | `PLEXUS_BASE_URL`                                                  |
| **Qwen (Intl)**      | `qwen`             | `qwen:qwen3.8-flash`                                          | API Key          | `QWEN_API_KEY`                                                              | `QWEN_BASE_URL`                                                    |
| **Qwen API (Intl)**  | `qwen-api`         | `qwen-api:qwen3.8-flash`                                      | API Key          | `QWEN_API_KEY`                                                              | `QWEN_API_BASE_URL`                                                |
| **Qwen API (CN)**    | `qwen-api-cn`      | `qwen-api-cn:qwen3.8-flash`                                   | API Key          | `QWEN_API_KEY`                                                              | `QWEN_API_BASE_URL`                                                |
| **Replicate**        | `replicate`        | `replicate:meta/llama-3.1-405b-instruct`                      | API Token        | `REPLICATE_API_TOKEN`                                                       | `REPLICATE_BASE_URL`                                               |
| **Streamlake**       | `streamlake`       | `streamlake:deepseek-chat`                                    | API Key          | `STREAMLAKE_API_KEY`                                                        | `STREAMLAKE_BASE_URL`                                              |
| **Synthetic.new**    | `synthetic`        | `synthetic:gpt-5.6-luna`                                      | API Key          | `SYNTHETIC_API_KEY`                                                         | `SYNTHETIC_BASE_URL`                                               |
| **Together AI**      | `together`         | `together:meta-llama/Llama-3.3-70B-Instruct-Turbo`            | API Key          | `TOGETHER_API_KEY`                                                          | `TOGETHER_BASE_URL`                                                |
| **Wafer.ai**         | `wafer`            | `wafer:wafer-1`                                               | API Key          | `WAFER_API_KEY`                                                             | `WAFER_BASE_URL`                                                   |
| **Z.ai**             | `zai`              | `zai:glm-5.3`                                                 | API Key          | `ZAI_API_KEY`                                                               | `ZAI_BASE_URL`, `ZAI_USE_CODING_PLAN`                              |
| **Z.ai Coding**      | `zai-coding`       | `zai-coding:glm-5.3`                                          | API Key          | `ZAI_API_KEY`                                                               | `ZAI_BASE_URL`                                                     |

---

## Detailed Provider Configurations

### 1. Anthropic (Claude)

**Best for:** General-purpose coding, reasoning, long context

```bash
# .gac.env
GAC_MODEL=anthropic:claude-sonnet-5
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx
```

**Available Models:**

- `claude-sonnet-5` (recommended)
- `claude-haiku-4-5`
- `claude-3-opus-20240229`

---

### 2. Azure OpenAI

**Best for:** Enterprise Azure deployments, compliance requirements

```bash
# .gac.env
GAC_MODEL=azure-openai:my-gpt4o-deployment
AZURE_OPENAI_API_KEY=xxxxxxxxxxxx
AZURE_OPENAI_ENDPOINT=https://my-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-10-21
```

**Notes:**

- Model name = **deployment name**, not model name
- API version must match your deployment's supported version
- Uses `api-key` header instead of Bearer token

---

### 3. Cerebras

**Best for:** Ultra-fast inference with Llama models

```bash
# .gac.env
GAC_MODEL=cerebras:zai-glm-4.7
CEREBRAS_API_KEY=csk-xxxxxxxxxxxx
# Optional: CEREBRAS_BASE_URL=https://api.cerebras.ai/v1
```

---

### 4. ChatGPT OAuth

**Best for:** Using your ChatGPT Plus/Pro subscription

```bash
# Run interactive setup
uvx gac init
# Select "ChatGPT OAuth" as provider
# Browser will open for authentication
```

**No API key needed** — uses your ChatGPT subscription via OAuth.

---

### 5. Chutes.ai

**Best for:** Serverless inference with open models

```bash
# .gac.env
GAC_MODEL=chutes:deepseek-ai/DeepSeek-V3-0324
CHUTES_API_KEY=chutes_xxxxxxxxxxxx
# Optional: CHUTES_BASE_URL=https://llm.chutes.ai/v1
```

---

### 6. Claude Code (Anthropic OAuth)

**Best for:** Anthropic Claude Code subscription users

```bash
# Run interactive setup
uvx gac init
# Select "Claude Code" as provider
# Browser will open for authentication
```

**Requires:** Active Claude Code subscription.

---

### 7. GitHub Copilot

**Best for:** GitHub Copilot subscribers

```bash
# Run interactive setup
uvx gac init
# Select "GitHub Copilot" as provider
# Browser will open for GitHub OAuth
```

---

### 8. Crof.ai

**Best for:** Multi-model access via single API

```bash
# .gac.env
GAC_MODEL=crof:claude-sonnet-5
CROF_API_KEY=crof_xxxxxxxxxxxx
# Optional: CROF_BASE_URL=https://api.crof.ai/v1
```

---

### 9. Custom Anthropic-Compatible Endpoint

**Best for:** Proxies, self-hosted Anthropic-compatible APIs (e.g., Omniroute, LiteLLM)

```bash
# .gac.env
GAC_MODEL=custom-anthropic:claude-sonnet-5
CUSTOM_ANTHROPIC_API_KEY=your-proxy-key
CUSTOM_ANTHROPIC_BASE_URL=https://your-proxy.example.com/v1
# Optional: CUSTOM_ANTHROPIC_VERSION=2023-06-01
```

**Important:** If your proxy defaults to streaming, gac automatically sends `stream: false`.

---

### 10. Custom OpenAI-Compatible Endpoint

**Best for:** Proxies, self-hosted OpenAI-compatible APIs (vLLM, Text Generation Inference, LocalAI, etc.)

```bash
# .gac.env
GAC_MODEL=custom-openai:gpt-5.6-luna
CUSTOM_OPENAI_API_KEY=your-proxy-key
CUSTOM_OPENAI_BASE_URL=https://your-proxy.example.com/v1
```

**Important:** If your proxy defaults to streaming, gac automatically sends `stream: false`.

---

### 11. DeepInfra

**Best for:** Low-cost open model inference

```bash
# .gac.env
GAC_MODEL=deepinfra:meta-llama/Llama-3.3-70B-Instruct
DEEPINFRA_API_KEY=your-key
# Optional: DEEPINFRA_BASE_URL=https://api.deepinfra.com/v1/openai
```

---

### 12. DeepSeek

**Best for:** Cost-effective reasoning models

```bash
# .gac.env
GAC_MODEL=deepseek:deepseek-flash
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxx
# Optional: DEEPSEEK_BASE_URL=https://api.deepseek.com
```

**Models:**

- `deepseek-flash` (V4.1 Flash)
- `deepseek-reasoner` (R1)

---

### 13. Fireworks AI

**Best for:** Fast inference with compound AI systems

```bash
# .gac.env
GAC_MODEL=fireworks:accounts/fireworks/models/llama-v3p1-70b-instruct
FIREWORKS_API_KEY=fw_xxxxxxxxxxxx
# Optional: FIREWORKS_BASE_URL=https://api.fireworks.ai/inference/v1
```

---

### 14. Google Gemini

**Best for:** Long context (1M+ tokens), multimodal

```bash
# .gac.env
GAC_MODEL=gemini:gemini-3.5-flash-lite
GEMINI_API_KEY=your-gemini-key
# Optional: GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
```

**Models:**

- `gemini-3.5-flash-lite` (1M context)
- `gemini-3.5-flash-lite` (fast, 1M context)
- `gemini-3.5-flash-lite` (experimental)

---

### 15. Groq

**Best for:** Ultra-low latency inference

```bash
# .gac.env
GAC_MODEL=groq:openai/gpt-oss-120b
GROQ_API_KEY=gsk_xxxxxxxxxxxx
# Optional: GROQ_BASE_URL=https://api.groq.com/openai/v1
```

**Models:**

- `openai/gpt-oss-120b`
- `llama-3.1-8b-instant`
- `mixtral-8x7b-32768`

---

### 16. Kimi for Coding

**Best for:** Coding-focused model from Moonshot

```bash
# .gac.env
GAC_MODEL=kimi-for-coding:kimi-for-coding
KIMI_API_KEY=sk-xxxxxxxxxxxx
# Optional: KIMI_BASE_URL=https://api.moonshot.cn/v1
```

---

### 17. LM Studio (Local)

**Best for:** Running models locally with GUI

```bash
# .gac.env
GAC_MODEL=lm-studio:my-local-model
# Optional (defaults to http://localhost:1234):
LMSTUDIO_API_URL=http://localhost:1234
# Optional (if LM Studio requires auth):
LMSTUDIO_API_KEY=your-key
```

**Setup:**

1. Start LM Studio and load a model
2. Start the local server (Developer → Start Server)
3. Use the model name as shown in LM Studio

---

### 18. MiniMax

**Best for:** Chinese language optimization, long context

```bash
# .gac.env
GAC_MODEL=minimax:MiniMax-M3
MINIMAX_API_KEY=your-key
# Optional: MINIMAX_BASE_URL=https://api.minimax.chat/v1
```

---

### 19. Mistral AI

**Best for:** European hosting, strong multilingual

```bash
# .gac.env
GAC_MODEL=mistral:devstral-2512
MISTRAL_API_KEY=your-key
# Optional: MISTRAL_BASE_URL=https://api.mistral.ai/v1
```

**Models:**

- `devstral-2512`
- `mistral-small-latest`
- `pixtral-large-latest` (multimodal)

---

### 20. Moonshot AI (Kimi)

**Best for:** Long context, Chinese language

```bash
# .gac.env
GAC_MODEL=moonshot:kimi-k3
MOONSHOT_API_KEY=sk-xxxxxxxxxxxx
# Optional: MOONSHOT_BASE_URL=https://api.moonshot.cn/v1
```

**Models:**

- `kimi-k3`
- `kimi-k3`
- `kimi-k3`

---

### 21. Neuralwatt

**Best for:** NVIDIA Nemotron models

```bash
# .gac.env
GAC_MODEL=neuralwatt:nemotron-3-ultra
NEURALWATT_API_KEY=your-key
# Optional: NEURALWATT_BASE_URL=https://api.neuralwatt.ai/v1
```

---

### 22. Ollama (Local)

**Best for:** Fully local inference, privacy, no API costs

```bash
# .gac.env
GAC_MODEL=ollama:gemma4
# Optional (defaults to http://localhost:11434):
OLLAMA_API_URL=http://localhost:11434
# Optional (if Ollama configured with auth):
OLLAMA_API_KEY=your-key
```

**Setup:**

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull gemma4

# Start Ollama server (if not running as service)
ollama serve
```

**Popular Models:**

- `gemma4` / `llama3.2`
- `qwen2.5-coder`
- `deepseek-coder`
- `codellama`
- `phi3.5`

---

### 23. Ollama Cloud

**Best for:** Managed Ollama hosting

```bash
# .gac.env
GAC_MODEL=ollama-cloud:gpt-oss:120b-cloud
OLLAMA_CLOUD_API_KEY=your-key
# Optional: OLLAMA_CLOUD_BASE_URL=https://ollama.com/api
```

---

### 24. OpenAI

**Best for:** GPT-4o, o1 reasoning, broad compatibility

```bash
# .gac.env
GAC_MODEL=openai:gpt-5.6-luna
OPENAI_API_KEY=sk-xxxxxxxxxxxx
# Optional:
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_ORG_ID=org-xxxxxxxxxxxx
```

**Models:**

- `gpt-5.6-luna` / `gpt-5.6-luna`
- `o1-preview` / `o1-mini` (reasoning)
- `gpt-5.6-terra`

---

### 25. OpenCode Go

**Best for:** OpenCode Go users

```bash
# .gac.env
GAC_MODEL=opencode-go:codellama
OPENCODE_GO_API_KEY=your-key
# Optional: OPENCODE_GO_BASE_URL=https://api.opencode.ai/v1
```

---

### 26. OpenRouter

**Best for:** Access 300+ models via single API, model routing

```bash
# .gac.env
GAC_MODEL=openrouter:anthropic/claude-3.5-sonnet
OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxx
# Optional:
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_REFERER=https://github.com/thomwebb/gac
OPENROUTER_APP_NAME=gac
```

**Popular Models:**

- `anthropic/claude-3.5-sonnet`
- `openai/gpt-5.6-luna`
- `google/gemini-3.5-flash-lite`
- `meta-llama/openai/gpt-oss-120b`
- `deepseek/deepseek-chat`

---

### 27. Plexus Gateway

**Best for:** Enterprise gateway with multiple providers

```bash
# .gac.env
GAC_MODEL=plexus:gpt-5.6-luna
PLEXUS_API_KEY=your-key
# Optional: PLEXUS_BASE_URL=https://your-gateway.example.com/v1
```

---

### 28. Qwen (International)

**Best for:** Alibaba's Qwen models (international)

```bash
# .gac.env
GAC_MODEL=qwen:qwen3.8-flash
QWEN_API_KEY=your-key
# Optional: QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/api/v1
```

---

### 29. Qwen API (International)

**Best for:** Direct Qwen API access (international)

```bash
# .gac.env
GAC_MODEL=qwen-api:qwen3.8-flash
QWEN_API_KEY=your-key
# Optional: QWEN_API_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

---

### 30. Qwen API (China)

**Best for:** Direct Qwen API access (China mainland)

```bash
# .gac.env
GAC_MODEL=qwen-api-cn:qwen3.8-flash
QWEN_API_KEY=your-key
# Optional: QWEN_API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

---

### 31. Replicate

**Best for:** Running open models via API, pay-per-use

```bash
# .gac.env
GAC_MODEL=replicate:meta/llama-3.1-405b-instruct
REPLICATE_API_TOKEN=r8_xxxxxxxxxxxx
# Optional: REPLICATE_BASE_URL=https://api.replicate.com/v1
```

---

### 32. Streamlake / Vanchin

**Best for:** Chinese provider, DeepSeek models

```bash
# .gac.env
GAC_MODEL=streamlake:deepseek-chat
STREAMLAKE_API_KEY=your-key
# Optional: STREAMLAKE_BASE_URL=https://api.streamlake.ai/v1
```

---

### 33. Synthetic.new

**Best for:** Synthetic data generation, model access

```bash
# .gac.env
GAC_MODEL=synthetic:gpt-5.6-luna
SYNTHETIC_API_KEY=your-key
# Optional: SYNTHETIC_BASE_URL=https://api.synthetic.new/v1
```

---

### 34. Together AI

**Best for:** Open model inference, fine-tuning

```bash
# .gac.env
GAC_MODEL=together:meta-llama/Llama-3.3-70B-Instruct-Turbo
TOGETHER_API_KEY=your-key
# Optional: TOGETHER_BASE_URL=https://api.together.xyz/v1
```

---

### 35. Wafer.ai

**Best for:** High-quality inference

```bash
# .gac.env
GAC_MODEL=wafer:wafer-1
WAFER_API_KEY=your-key
# Optional: WAFER_BASE_URL=https://pass.Wafer.ai
```

---

### 36. Z.ai (GLM)

**Best for:** Zhipu AI's GLM models

```bash
# .gac.env
GAC_MODEL=zai:glm-5.3
ZAI_API_KEY=your-key
# Optional:
ZAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
ZAI_USE_CODING_PLAN=false  # Set true for coding plan
```

**Models:**

- `glm-5.3` / `glm-5.3-flash`
- `glm-5.3` (tool use)

---

### 37. Z.ai Coding

**Best for:** Z.ai's coding-specialized models

```bash
# .gac.env
GAC_MODEL=zai-coding:glm-5.3
ZAI_API_KEY=your-key
# Optional: ZAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
```

---

## Configuration Patterns

### Using `uvx gac init` (Recommended)

The interactive setup handles provider-specific prompts:

```bash
uvx gac init
# 1. Select provider from list
# 2. Enter model name
# 3. Enter API key / authenticate via OAuth
# 4. Optionally set language, output format
# 5. Saves to .gac.env
```

### Using `uvx gac model` (Provider/Model Only)

Change provider/model without reconfiguring language:

```bash
uvx gac model
# Select new provider/model
```

### Multiple Providers

You can configure multiple providers in `.gac.env` and switch via CLI:

```bash
# .gac.env
GAC_MODEL=openai:gpt-5.6-luna
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
GROQ_API_KEY=gsk-xxx

# Switch at runtime
uvx gac -m anthropic:claude-sonnet-5
uvx gac -m groq:openai/gpt-oss-120b
```

### Per-Project Configuration

Create `.gac.env` in your project root:

```bash
# Project-specific config
GAC_MODEL=anthropic:claude-sonnet-5
ANTHROPIC_API_KEY=sk-ant-xxx
GAC_LANGUAGE=English
GAC_VERBOSE=true
```

Global config at `~/.gac.env` is overridden by project config.

---

## Provider Capabilities Matrix

| Provider         | Streaming | Reasoning | Tool Use | Max Context     | Free Tier    |
| ---------------- | --------- | --------- | -------- | --------------- | ------------ |
| Anthropic        | ✅        | ✅        | ✅       | 200k            | ❌           |
| Azure OpenAI     | ✅        | ✅        | ✅       | 128k            | ❌           |
| Cerebras         | ❌        | ❌        | ❌       | 8k              | ✅           |
| ChatGPT OAuth    | ✅        | ✅        | ✅       | 128k            | Subscription |
| Chutes           | ✅        | ✅        | ❌       | 32k             | ✅           |
| Claude Code      | ✅        | ✅        | ✅       | 200k            | Subscription |
| Copilot          | ✅        | ✅        | ✅       | 128k            | Subscription |
| Crof             | ✅        | ✅        | ✅       | 200k            | ❌           |
| Custom Anthropic | ✅        | ✅        | ✅       | Varies          | Varies       |
| Custom OpenAI    | ✅        | ✅        | ✅       | Varies          | Varies       |
| DeepInfra        | ✅        | ✅        | ❌       | 128k            | ✅           |
| DeepSeek         | ✅        | ✅        | ❌       | 64k             | ✅           |
| Fireworks        | ✅        | ✅        | ❌       | 128k            | ✅           |
| Gemini           | ✅        | ✅        | ✅       | 1M+             | ✅           |
| Groq             | ✅        | ❌        | ❌       | 32k             | ✅           |
| Kimi Coding      | ✅        | ✅        | ✅       | 128k            | ❌           |
| LM Studio        | ❌        | ❌        | ❌       | Model-dependent | Local        |
| MiniMax          | ✅        | ✅        | ✅       | 1M              | ❌           |
| Mistral          | ✅        | ✅        | ✅       | 128k            | ❌           |
| Moonshot         | ✅        | ✅        | ✅       | 128k            | ❌           |
| Neuralwatt       | ✅        | ✅        | ❌       | 32k             | ❌           |
| Ollama           | ❌        | ❌        | ❌       | Model-dependent | Local        |
| Ollama Cloud     | ✅        | ✅        | ✅       | Model-dependent | ❌           |
| OpenAI           | ✅        | ✅        | ✅       | 128k            | ❌           |
| OpenCode Go      | ✅        | ❌        | ❌       | 32k             | ❌           |
| OpenRouter       | ✅        | ✅        | ✅       | Model-dependent | ✅           |
| Plexus           | ✅        | ✅        | ✅       | Varies          | ❌           |
| Qwen             | ✅        | ✅        | ✅       | 128k            | ❌           |
| Replicate        | ✅        | ❌        | ❌       | Model-dependent | Pay-per-use  |
| Streamlake       | ✅        | ✅        | ❌       | 64k             | ❌           |
| Synthetic        | ✅        | ✅        | ✅       | 128k            | ❌           |
| Together         | ✅        | ✅        | ❌       | 128k            | ✅           |
| Wafer            | ✅        | ✅        | ✅       | 128k            | ❌           |
| Z.ai             | ✅        | ✅        | ✅       | 128k            | ❌           |

---

## Troubleshooting

### "Authentication Error" / "API Key Not Set"

1. Run `uvx gac init` to reconfigure
2. Or manually set the required env var in `.gac.env`
3. For OAuth providers, re-run `uvx gac init` to refresh tokens

### "Model Not Found"

- Verify model name format: `provider:model-name`
- Check provider's model list (some use deployment names, not model names)
- For Azure: use deployment name, not model name

### "Connection Error" / Timeout

- Check `GAC_NO_VERIFY_SSL=true` for corporate proxies
- Verify base URL is correct and accessible
- Increase timeout: `GAC_HTTP_TIMEOUT=60`

### "Rate Limited"

- Wait and retry
- Switch to a different model/provider
- Check provider's rate limit policies

### Local Models (Ollama, LM Studio) - "Connection Refused"

- Ensure server is running: `ollama serve` or LM Studio "Start Server"
- Check URL: `http://localhost:11434` (Ollama) or `http://localhost:1234` (LM Studio)
- Try `curl http://localhost:11434/api/tags` to verify

---

## Adding a New Provider

Want to add a provider? See [CONTRIBUTING.md](../CONTRIBUTING.md#adding-a-new-provider) for the provider implementation guide.

---

## See Also

- [USAGE.md](USAGE.md) — Complete CLI reference
- [CUSTOM_SYSTEM_PROMPTS.md](CUSTOM_SYSTEM_PROMPTS.md) — Customize commit message style
- [CLAUDE_CODE.md](CLAUDE_CODE.md) — Claude Code OAuth setup
- [CHATGPT_OAUTH.md](CHATGPT_OAUTH.md) — ChatGPT OAuth setup
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — Common issues
