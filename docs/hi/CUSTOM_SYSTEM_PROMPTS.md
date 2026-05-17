# Custom System Prompts

[English](../en/CUSTOM_SYSTEM_PROMPTS.md) | [简体中文](../zh-CN/CUSTOM_SYSTEM_PROMPTS.md) | [繁體中文](../zh-TW/CUSTOM_SYSTEM_PROMPTS.md) | [日本語](../ja/CUSTOM_SYSTEM_PROMPTS.md) | [한국어](../ko/CUSTOM_SYSTEM_PROMPTS.md) | **हिन्दी** | [Tiếng Việt](../vi/CUSTOM_SYSTEM_PROMPTS.md) | [Français](../fr/CUSTOM_SYSTEM_PROMPTS.md) | [Русский](../ru/CUSTOM_SYSTEM_PROMPTS.md) | [Español](../es/CUSTOM_SYSTEM_PROMPTS.md) | [Português](../pt/CUSTOM_SYSTEM_PROMPTS.md) | [Norsk](../no/CUSTOM_SYSTEM_PROMPTS.md) | [Svenska](../sv/CUSTOM_SYSTEM_PROMPTS.md) | [Deutsch](../de/CUSTOM_SYSTEM_PROMPTS.md) | [Nederlands](../nl/CUSTOM_SYSTEM_PROMPTS.md) | [Italiano](../it/CUSTOM_SYSTEM_PROMPTS.md)

यह गाइड बताता है कि GAC द्वारा कमिट मैसेज बनाने के लिए उपयोग किए जाने वाले सिस्टम प्रॉम्प्ट को कैसे कस्टमाइज़ करें, जिससे आप अपनी खुद की कमिट मैसेज स्टाइल और सम्मेलनों को परिभाषित कर सकते हैं।

## Table of Contents

- [Custom System Prompts](#custom-system-prompts)
  - [Table of Contents](#table-of-contents)
  - [What Are System Prompts?](#what-are-system-prompts)
  - [Why Use Custom System Prompts?](#why-use-custom-system-prompts)
  - [Quick Start](#quick-start)
  - [Writing Your Custom System Prompt](#writing-your-custom-system-prompt)
  - [Examples](#examples)
    - [Emoji-Based Commit Style](#emoji-based-commit-style)
    - [Team-Specific Conventions](#team-specific-conventions)
    - [Detailed Technical Style](#detailed-technical-style)
  - [Best Practices](#best-practices)
    - [Do:](#do)
    - [Don't:](#dont)
    - [Tips:](#tips)
  - [Troubleshooting](#troubleshooting)
    - [Messages still have "chore:" prefix](#messages-still-have-chore-prefix)
    - [AI ignoring my instructions](#ai-ignoring-my-instructions)
    - [Messages are too long/short](#messages-are-too-longshort)
    - [Custom prompt not being used](#custom-prompt-not-being-used)
    - [Want to switch back to default](#want-to-switch-back-to-default)
  - [Related Documentation](#related-documentation)
  - [Need Help?](#need-help)

## What Are System Prompts?

GAC कमिट मैसेज बनाते समय दो प्रॉम्प्ट का उपयोग करता है:

1. **System Prompt** (कस्टमाइज़ेबल): निर्देश जो कमिट मैसेज के लिए भूमिका, स्टाइल, और सम्मेलनों को परिभाषित करते हैं
2. **User Prompt** (स्वचालित): गिट डिफ डेटा जो दिखाता है कि क्या बदला गया

सिस्टम प्रॉम्प्ट AI को बताता है कि कमिट मैसेज _कैसे_ लिखना है, जबकि यूजर प्रॉम्प्ट \_क्या प्रदान करता है (वास्तविक कोड परिवर्तन)।

## Why Use Custom System Prompts?

आप कस्टम सिस्टम प्रॉम्प्ट चाह सकते हैं यदि:

- आपकी टीम कन्वेंशनल कमिट्स से अलग कमिट मैसेज स्टाइल का उपयोग करती है
- आप इमोजी, प्रिफिक्सेस, या अन्य कस्टम फॉर्मेट पसंद करते हैं
- आप कमिट मैसेज में अधिक या कम विवरण चाहते हैं
- आपके पास कंपनी-विशिष्ट दिशानिर्देश या टेम्प्लेट हैं
- आप अपनी टीम की आवाज और टोन से मेल खाना चाहते हैं
- आप अलग भाषा में कमिट मैसेज चाहते हैं (नीचे भाषा कॉन्फिगरेशन देखें)

## Quick Start

1. **अपना कस्टम सिस्टम प्रॉम्प्ट फाइल बनाएं:**

   ```bash
   # कॉपी करें उदाहरण को शुरुआती बिंदु के रूप में
   cp custom_system_prompt.example.txt ~/.config/gac/my_system_prompt.txt

   # या अपना खुद से बनाएं
   vim ~/.config/gac/my_system_prompt.txt
   ```

2. **अपनी `.gac.env` फाइल में जोड़ें:**

   ```bash
   # ~/.gac.env में या प्रोजेक्ट-लेवल .gac.env में
   GAC_SYSTEM_PROMPT_PATH=/path/to/your/custom_system_prompt.txt
   ```

3. **इसे टेस्ट करें:**

   ```bash
   uvx gac --dry-run
   ```

बस! GAC अब डिफ़ॉल्ट के बजाय आपके कस्टम निर्देशों का उपयोग करेगा।

## Writing Your Custom System Prompt

आपका कस्टम सिस्टम प्रॉम्प्ट प्लेन टेक्स्ट हो सकता है - कोई विशेष फॉर्मेट या XML टैग की आवश्यकता नहीं है। बस AI को कमिट मैसेज कैसे बनाने चाहिए, यह स्पष्ट निर्देश लिखें।

**शामिल करने के लिए मुख्य बातें:**

1. **रोल परिभाषा** - AI को क्या कार्य करना चाहिए
2. **फॉर्मेट आवश्यकताएं** - संरचना, लंबाई, स्टाइल
3. **उदाहरण** - दिखाएं कि अच्छे कमिट मैसेज कैसे दिखते हैं
4. **प्रतिबंध** - क्या बचना है या क्या आवश्यकताएं पूरी करनी हैं

**उदाहरण संरचना:**

```text
You are a commit message writer for [your project/team].

When analyzing code changes, create a commit message that:

1. [First requirement]
2. [Second requirement]
3. [Third requirement]

Example format:
[Show an example commit message]

Your entire response will be used directly as the commit message.
```

## Examples

### Emoji-Based Commit Style

इमोजी-आधारित उदाहरण के लिए [`custom_system_prompt.example.txt`](../../examples/custom_system_prompt.example.txt) देखें।

**त्वरित स्निपेट:**

```text
You are a commit message writer that uses emojis and a friendly tone.

Start each message with an emoji:
- 🎉 for new features
- 🐛 for bug fixes
- 📝 for documentation
- ♻️ for refactoring

Keep the first line under 72 characters and explain WHY the change matters.
```

### Team-Specific Conventions

```text
You are writing commit messages for an enterprise banking application.

Requirements:
1. Start with a JIRA ticket number in brackets (e.g., [BANK-1234])
2. Use formal, professional tone
3. Include security implications if relevant
4. Reference any compliance requirements (PCI-DSS, SOC2, etc.)
5. Keep messages concise but complete

Format:
[TICKET-123] Brief summary of change

Detailed explanation of what changed and why. Include:
- Business justification
- Technical approach
- Risk assessment (if applicable)

Example:
[BANK-1234] Implement rate limiting for login endpoints

Added Redis-based rate limiting to prevent brute force attacks.
Limits login attempts to 5 per IP per 15 minutes.
Complies with SOC2 security requirements for access control.
```

### Detailed Technical Style

```text
You are a technical commit message writer who creates comprehensive documentation.

For each commit, provide:

1. A clear, descriptive title (under 72 characters)
2. A blank line
3. WHAT: What was changed (2-3 sentences)
4. WHY: Why the change was necessary (2-3 sentences)
5. HOW: Technical approach or key implementation details
6. IMPACT: Files/components affected and potential side effects

Use technical precision. Reference specific functions, classes, and modules.
Use present tense and active voice.

Example:
Refactor authentication middleware to use dependency injection

WHAT: Replaced global auth state with injectable AuthService. Updated
all route handlers to accept AuthService through constructor injection.

WHY: Global state made testing difficult and created hidden dependencies.
Dependency injection improves testability and makes dependencies explicit.

HOW: Created AuthService interface, implemented JWTAuthService and
MockAuthService. Modified route handler constructors to require AuthService.
Updated dependency injection container configuration.

IMPACT: Affects all authenticated routes. No behavior changes for users.
Tests now run 3x faster with MockAuthService. Migration required for
routes/auth.ts, routes/api.ts, and routes/admin.ts.
```

## Best Practices

### Do

- ✅ **विशिष्ट रहें** - स्पष्ट निर्देश बेहतर परिणाम देते हैं
- ✅ **उदाहरण शामिल करें** - AI को दिखाएं कि अच्छा क्या लगता है
- ✅ **पुनरावृत्ति से टेस्ट करें** - अपना प्रॉम्प्ट आज़माएं, परिणामों के आधार पर बेहतर बनाएं
- ✅ **इसे केंद्रित रखें** - बहुत सारे नियम AI को भ्रमित कर सकते हैं
- ✅ **संगत टर्मिनोलॉजी का उपयोग करें** - पूरे समय एक ही शब्दों पर टिके रहें
- ✅ **एक अनुस्मारक के साथ समाप्त करें** - यह दोहराएं कि प्रतिक्रिया का उपयोग जैसा है वैसे ही किया जाएगा

### Don't

- ❌ **XML टैग का उपयोग करें** - प्लेन टेक्स्ट सबसे अच्छा काम करता है (जब तक आप विशेष रूप से उस संरचना नहीं चाहते)
- ❌ **इसे बहुत लंबा बनाएं** - निर्देशों के लिए 200-500 शब्दों का लक्ष्य रखें
- ❌ **खुद का खंडन करें** - अपनी आवश्यकताओं में लगातार रहें
- ❌ **अंत को भूल जाएं** - हमेशा याद दिलाएं: "Your entire response will be used directly as the commit message"

### Tips

- **उदाहरण से शुरू करें** - `../../examples/custom_system_prompt.example.txt` कॉपी करें और इसे संशोधित करें
- **`--dry-run` के साथ टेस्ट करें** - कमिट किए बिना परिणाम देखें
- **`--show-prompt` का उपयोग करें** - देखें कि AI को क्या भेजा जा रहा है
- **परिणामों के आधार पर पुनरावृत्ति करें** - यदि मैसेज बिल्कुल सही नहीं हैं, तो अपने निर्देशों को समायोजित करें
- **अपने प्रॉम्प्ट को वर्जन कंट्रोल करें** - अपना कस्टम प्रॉम्प्ट अपनी टीम के रिपॉजिटरी में रखें
- **प्रोजेक्ट-विशिष्ट प्रॉम्प्ट** - प्रोजेक्ट-विशिष्ट स्टाइल के लिए प्रोजेक्ट-लेवल `.gac.env` का उपयोग करें

## Troubleshooting

### Messages still have "chore:" prefix

**समस्या:** आपके कस्टम इमोजी मैसेज में "chore:" जोड़ा जा रहा है।

**समाधान:** ऐसा नहीं होना चाहिए - GAC कस्टम सिस्टम प्रॉम्प्ट का उपयोग करते समय कन्वेंशनल कमिट एनफोर्समेंट को स्वचालित रूप से अक्षम कर देता है। यदि आप यह देखते हैं, तो कृपया [इश्यू फाइल करें](https://github.com/cellwebb/gac/issues)।

### AI ignoring my instructions

**समस्या:** बनाए गए मैसेज आपके कस्टम फॉर्मेट का पालन नहीं करते हैं।

**समाधान:**

1. अपने निर्देशों को अधिक स्पष्ट और विशिष्ट बनाएं
2. वांछित फॉर्मेट के स्पष्ट उदाहरण जोड़ें
3. इसके साथ समाप्त करें: "Your entire response will be used directly as the commit message"
4. आवश्यकताओं की संख्या कम करें - बहुत सारे AI को भ्रमित कर सकते हैं
5. एक अलग मॉडल का उपयोग करने का प्रयास करें (कुछ निर्देशों का बेहतर पालन करते हैं)

### Messages are too long/short

**समस्या:** बनाए गए मैसेज आपकी लंबाई की आवश्यकताओं से मेल नहीं खाते।

**समाधान:**

- लंबाई के बारे में स्पष्ट रहें (जैसे, "Keep messages under 50 characters")
- आप जिस लंबाई चाहते हैं उसके सटीक उदाहरण दिखाएं
- छोटे मैसेज के लिए `--one-liner` फ्लैग का उपयोग करने पर विचार करें

### Custom prompt not being used

**समस्या:** GAC अभी भी डिफ़ॉल्ट कमिट फॉर्मेट का उपयोग करता है।

**समाधान:**

1. जांचें कि `GAC_SYSTEM_PROMPT_PATH` सही ढंग से सेट है:

   ```bash
   uvx gac config get GAC_SYSTEM_PROMPT_PATH
   ```

2. सत्यापित करें कि फाइल पथ मौजूद है और पढ़ने योग्य है:

   ```bash
   cat "$GAC_SYSTEM_PROMPT_PATH"
   ```

3. इस क्रम में `.gac.env` फाइल जांचें:
   - प्रोजेक्ट लेवल: `./.gac.env`
   - यूजर लेवल: `~/.gac.env`
4. रिलेटिव पथ के बजाय एब्सोल्यूट पथ का प्रयास करें

### Language Configuration

**नोट:** कमिट मैसेज भाषा बदलने के लिए आपको कस्टम सिस्टम प्रॉम्प्ट की आवश्यकता नहीं है!

यदि आप केवल अपने कमिट मैसेज की भाषा बदलना चाहते हैं (जबकि मानक कन्वेंशनल कमिट फॉर्मेट बनाए रखते हुए), इंटरैक्टिव भाषा चयनकर्ता का उपयोग करें:

```bash
uvx gac language
```

यह 25+ भाषाओं के साथ एक इंटरैक्टिव मेनू प्रस्तुत करेगा जो उनकी मूल स्क्रिप्ट में हैं (Español, Français, 日本語, आदि)। अपनी पसंदीदा भाषा का चयन करें, और यह स्वचालित रूप से आपकी `~/.gac.env` फाइल में `GAC_LANGUAGE` सेट कर देगा।

वैकल्पिक रूप से, आप मैन्युअल रूप से भाषा सेट कर सकते हैं:

```bash
# ~/.gac.env में या प्रोजेक्ट-लेवल .gac.env में
GAC_LANGUAGE=Spanish
```

डिफ़ॉल्ट रूप से, कन्वेंशनल कमिट प्रिफिक्सेस (feat:, fix:, आदि) चेंजलॉग टूल और CI/CD पाइपलाइन के साथ संगतता के लिए अंग्रेजी में रहते हैं, जबकि सभी अन्य टेक्स्ट आपकी निर्दिष्ट भाषा में होता है।

**प्रिफिक्सेस का अनुवाद भी करना चाहते हैं?** `.gac.env` में `GAC_TRANSLATE_PREFIXES=true` सेट करें पूर्ण स्थानीयकरण के लिए:

```bash
GAC_LANGUAGE=Spanish
GAC_TRANSLATE_PREFIXES=true
```

यह सब कुछ अनुवाद करेगा, जिसमें प्रिफिक्सेस भी शामिल हैं (जैसे, `fix:` के बजाय `corrección:`)।

यदि भाषा आपकी एकमात्र कस्टमाइज़ेशन आवश्यकता है, तो यह कस्टम सिस्टम प्रॉम्प्ट बनाने से आसान है।

### Want to switch back to default

**समस्या:** अस्थायी रूप से डिफ़ॉल्ट प्रॉम्प्ट का उपयोग करना चाहते हैं।

**समाधान:**

```bash
# Option 1: Unset the environment variable
uvx gac config unset GAC_SYSTEM_PROMPT_PATH

# Option 2: Comment it out in .gac.env
# GAC_SYSTEM_PROMPT_PATH=/path/to/custom_prompt.txt

# Option 3: Use a different .gac.env for specific projects
```

---

## Related Documentation

- [USAGE.md](../USAGE.md) - कमांड-लाइन फ्लैग्स और विकल्प
- [README.md](../README.md) - इंस्टॉलेशन और बेसिक सेटअप
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - सामान्य ट्रबलशूटिंग

## Need Help?

- इश्यू रिपोर्ट करें: [GitHub Issues](https://github.com/cellwebb/gac/issues)
- अपने कस्टम प्रॉम्प्ट साझा करें: योगदान आमंत्रित हैं!
