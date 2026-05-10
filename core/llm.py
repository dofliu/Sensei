"""
Sensei · LLM Module (Ollama backend)
================================
Gemma 4 wrapper using Ollama as the local inference runtime.

Why Ollama instead of raw transformers + bitsandbytes:

1. ZERO-FRICTION DEPLOYMENT. Any teacher on macOS/Windows/Linux can
   `ollama pull gemma4:e2b` and run Sensei. No Python ML environment
   wrangling, no CUDA driver matching, no quantization config.
   This DIRECTLY supports the hackathon's impact thesis: AI for
   under-resourced classrooms with non-engineer teachers.

2. NATIVE JSON MODE. Ollama's `format="json"` parameter constrains
   Gemma 4's output at the sampling level — invalid JSON cannot be
   emitted. This is Sensei's structured-output guarantee.

3. AUTOMATIC VRAM MANAGEMENT. Ollama swaps models in/out of GPU as
   needed; Whisper and Gemma 4 coexist gracefully on a 12GB laptop.

4. PRODUCTION-GRADE BACKEND. Ollama uses llama.cpp under the hood —
   the same engine running Gemma 4 in millions of edge deployments.
   This is not a hack; it's the recommended path for on-device Gemma 4.

Default model: gemma4:e2b
   Why e2b not e4b? On RTX 4080 (12GB) we run Whisper large-v3 (~3GB)
   alongside the LLM. e2b leaves comfortable headroom; e4b would force
   Ollama to spill into system RAM, killing real-time latency.
"""

import json
import re
from pathlib import Path

import ollama
from pydantic import ValidationError

from .templates import TEMPLATE_REGISTRY


PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "classifier.txt"
EXTEND_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "extender.txt"


# ──────────────────────────────────────────────
# Native function-calling: each template is a tool
# ──────────────────────────────────────────────
# Gemma 4 + Ollama support tools natively (verified via `ollama show gemma4:e2b`
# capabilities: completion, vision, audio, tools, thinking). Sensei uses tool
# calling as the *primary* path for template selection — letting the model
# pick a tool replaces the older "classify into a JSON template field" pattern.
# JSON-mode remains as a silent fallback if the tool path returns nothing.

TOOL_DESCRIPTIONS = {
    "enumeration_cards": "當老師列舉多個並列項目時呼叫（例：「PID、最佳、神經、非線性、強健控制」、「監督式、非監督式、強化學習」）。",
    "comparison_table":  "當老師比較兩個東西的差異時呼叫（例：「單迴路 vs 雙迴路」、「PLC 與 PC-Based 比較」）。",
    "flow_diagram":      "當老師描述步驟順序、流程時呼叫（例：「先量測，再特徵抽取，再分類，最後報警」）。",
    "hierarchy_tree":    "當老師描述「分類有子分類」（一層樹狀）時呼叫（例：「線性控制分為 P、PI、PID」）。",
    "swot":              "當老師明確談優勢、劣勢、機會、威脅四面向（或其中至少三面向）時呼叫。",
    "pyramid":           "當老師描述線性層級（從基礎到頂層的單軸結構）時呼叫，例如 Maslow 需求層次。",
}

SYSTEM_TOOLS_PROMPT = (
    "你是課堂視覺化助教。請根據老師剛說的話，呼叫**剛好一個**工具來把內容結構化。\n"
    "重要規則：\n"
    "1. **每一個物件的所有 required 欄位都必須填入**。例如 enumeration_cards 的每個 item 必須同時有 name、icon、desc 三個欄位，缺一不可。\n"
    "2. 不確定 icon 名稱時，請填 `circle` 作為預設值，不要省略。\n"
    "3. desc 欄位（若有）必須極短，最多 10 字。\n"
    "4. 中文一律繁體，不要簡體。\n"
    "5. 工具參數中每個欄位只能出現一次。\n"
    "6. icon 欄位用 Lucide slug；常用：trending-up, brain, wind, zap, "
    "settings, sliders, target, gauge, shield, alert-triangle, arrow-right, "
    "code, bot, users, graduation-cap, lightbulb, book-open, circle。"
)


def _build_tools() -> list[dict]:
    """從 TEMPLATE_REGISTRY 自動生成 Ollama tools spec。
    `template` 欄位是模板識別常數，由工具名稱本身承載，因此從 parameters 移除以免混淆模型。
    """
    tools: list[dict] = []
    for name, model_cls in TEMPLATE_REGISTRY.items():
        schema = model_cls.model_json_schema()
        # Strip the literal `template` field — the tool name carries this info.
        props = schema.get("properties", {})
        if "template" in props:
            props.pop("template")
        if "required" in schema:
            schema["required"] = [r for r in schema["required"] if r != "template"]
        tools.append({
            "type": "function",
            "function": {
                "name": name,
                "description": TOOL_DESCRIPTIONS.get(name, name),
                "parameters": schema,
            },
        })
    return tools


class LLMConfig:
    # Model — must already be `ollama pull`ed locally.
    # Run `ollama list` to see what you have.
    MODEL_ID = "gemma4:e2b"     # 7.2 GB, fast, fits with Whisper large-v3
    # Alternative: "gemma4:e4b"  # 9.6 GB, higher quality, needs Whisper medium

    # Sampling
    TEMPERATURE = 0.3            # Low for structured output
    TOP_P = 0.9
    NUM_PREDICT = 1024           # Max output tokens
    NUM_CTX = 4096               # Context window

    # Ollama server (default localhost:11434)
    HOST = "http://localhost:11434"


class SenseiLLM:
    """
    Gemma-4-via-Ollama wrapper. Stateless — Ollama keeps the model warm.
    """

    def __init__(self, config: LLMConfig = LLMConfig()):
        self.config = config
        self.client = ollama.Client(host=config.HOST)
        self._verify_model()
        self.prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
        self.extend_template = EXTEND_PROMPT_PATH.read_text(encoding="utf-8")
        self._tools = _build_tools()
        print(
            f"[Sensei LLM] Ready · backend=Ollama · model={config.MODEL_ID}"
            f" · tools={len(self._tools)}"
        )

    def _verify_model(self):
        """Fail fast with a helpful message if the model isn't pulled."""
        try:
            models = self.client.list().get("models", [])
            available = {m.get("model") or m.get("name") for m in models}
            if self.config.MODEL_ID not in available:
                raise RuntimeError(
                    f"\n[Sensei LLM] Model '{self.config.MODEL_ID}' not found in Ollama.\n"
                    f"  Available: {sorted(available)}\n"
                    f"  Fix:       ollama pull {self.config.MODEL_ID}"
                )
        except ollama.ResponseError as e:
            raise RuntimeError(
                f"[Sensei LLM] Cannot reach Ollama at {self.config.HOST}.\n"
                f"  Is Ollama running? Start it with `ollama serve` "
                f"(or just open the Ollama app)."
            ) from e

    # ──────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────
    def structurize(self, text: str, template_hint: str | None = None) -> dict:
        """
        Convert spoken text → schema-validated visualization JSON.

        Primary path: native Gemma 4 tool-calling via Ollama. The model picks
        one of six tools (= one template) and fills its arguments. Pydantic
        validates the args against the matching schema.

        Fallback: legacy classifier prompt + format="json", same Pydantic pass.
        This keeps demos resilient if a future Ollama / Gemma 4 release changes
        the tool-call wire format.

        Optional `template_hint` forces a specific tool (operator override).
        Returns dict with key "template" identifying which schema was used.
        On failure, returns {"template": "raw", ...}.
        """
        if template_hint and template_hint not in TEMPLATE_REGISTRY:
            print(f"[Sensei LLM] [!] Unknown template_hint '{template_hint}', ignoring.", flush=True)
            template_hint = None

        # 1. Tool-calling path
        result = self._structurize_via_tools(text, template_hint=template_hint)
        if result.get("template") not in ("raw", None):
            print(f"[Sensei LLM] path=tools template={result.get('template')}", flush=True)
            result["_path"] = "tools"
            return result

        # 2. JSON-mode fallback
        print(
            f"[Sensei LLM] tool-call path returned raw "
            f"({result.get('_error', 'unknown')}); falling back to JSON mode.",
            flush=True,
        )
        raw = self._generate(text, template_hint=template_hint)
        result = self._parse_and_validate(raw)
        result["_path"] = "json-mode" if result.get("template") != "raw" else "raw-fallback"
        print(f"[Sensei LLM] path={result['_path']} template={result.get('template')}", flush=True)
        return result

    def _structurize_via_tools(self, text: str, template_hint: str | None = None) -> dict:
        """Native function-calling path. Returns {'template': 'raw', ...} on miss."""
        # When a hint is given, hand the model only that one tool — forces its
        # hand without relying on tool_choice (not all Ollama versions support).
        if template_hint:
            tools = [t for t in self._tools if t["function"]["name"] == template_hint]
            if not tools:
                tools = self._tools
        else:
            tools = self._tools

        try:
            response = self.client.chat(
                model=self.config.MODEL_ID,
                messages=[
                    {"role": "system", "content": SYSTEM_TOOLS_PROMPT},
                    {"role": "user",   "content": text},
                ],
                tools=tools,
                options={
                    "temperature": self.config.TEMPERATURE,
                    "top_p":       self.config.TOP_P,
                    "num_predict": self.config.NUM_PREDICT,
                    "num_ctx":     self.config.NUM_CTX,
                },
            )
        except Exception as e:
            return {"template": "raw", "_error": f"tool_chat:{e}"}

        msg = response.get("message", {}) or {}
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            return {"template": "raw", "_error": "no_tool_call"}

        call = tool_calls[0]
        fn = call.get("function") or {}
        template_name = fn.get("name", "")
        args = fn.get("arguments") or {}
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError as e:
                return {"template": "raw", "_error": f"args_parse:{e}"}
        if not isinstance(args, dict):
            return {"template": "raw", "_error": "args_not_dict"}

        schema = TEMPLATE_REGISTRY.get(template_name)
        if not schema:
            return {"template": "raw", "_error": f"unknown_tool:{template_name}"}

        # Reconstitute as standard format (template field at top level)
        data = {**args, "template": template_name}
        # Strict first
        try:
            return schema.model_validate(data).model_dump()
        except ValidationError:
            pass
        # Lenient salvage (icon defaults to 'circle', desc to '', etc.) before giving up
        salvaged = self._salvage_card_data(data, template_name)
        try:
            result = schema.model_validate(salvaged).model_dump()
            print(f"[Sensei LLM] tool path salvaged template={template_name}", flush=True)
            result["_salvaged"] = True
            return result
        except ValidationError as e:
            print(f"[Sensei LLM] [!] tool args failed validation; will fall back to JSON mode")
            return {"template": "raw", "_error": f"schema:{e}", "_partial": data}

    # Mapping: language code → (prompt-name, native script word for "STRICT")
    # Native script anchor (e.g. "厳密に") helps the small model commit to the
    # target language by including a target-script token in the instruction.
    TRANSLATION_TARGETS = {
        "en": ("English",                        "STRICTLY"),
        "ja": ("Japanese (日本語)",              "厳密に"),
        "ko": ("Korean (한국어)",                "엄격히"),
        "vi": ("Vietnamese (Tiếng Việt)",        "NGHIÊM NGẶT"),
        "id": ("Indonesian (Bahasa Indonesia)",  "DENGAN KETAT"),
        "es": ("Spanish (Español)",              "ESTRICTAMENTE"),
        "fr": ("French (Français)",              "STRICTEMENT"),
    }

    def translate(self, data: dict, target_lang: str = "en") -> dict:
        """
        把卡片資料從繁中翻譯成 target_lang。
        - 預設目標：英文。其他支援：ja, ko, vi, id, es, fr。
        - 用 JSON mode + Pydantic 驗證；翻譯失敗時退回原資料。
        """
        if not data or "template" not in data:
            return data
        template = data.get("template", "")
        if template not in TEMPLATE_REGISTRY:
            return data
        if target_lang == "zh" or target_lang not in self.TRANSLATION_TARGETS:
            return data  # no-op for unknown / source language

        target_name, strictly = self.TRANSLATION_TARGETS[target_lang]
        clean = {k: v for k, v in data.items() if not k.startswith("_")}

        prompt = (
            f"TASK: Translate this JSON card from Chinese to {target_name}.\n\n"
            f"CRITICAL: every output value must be in {target_name} ({strictly}). "
            f"The output JSON must contain ZERO Chinese characters in any value field "
            f"— values must be in {target_name} only.\n\n"
            "EXAMPLE INPUT (Chinese):\n"
            '{\n'
            '  "template": "enumeration_cards",\n'
            '  "title": "控制方法",\n'
            '  "subtitle": "進階策略",\n'
            '  "items": [\n'
            '    {"name": "PID 控制", "icon": "sliders", "desc": "業界主流", "tag": ""}\n'
            '  ]\n'
            '}\n\n'
            f"EXAMPLE OUTPUT ({target_name}) — same structure, all values translated:\n"
            "(produce a parallel object with the same keys; values translated naturally)\n\n"
            "RULES:\n"
            "- Same JSON structure, same field names. Do not rename or drop fields.\n"
            "- Keep these field values UNCHANGED: template, icon (Lucide slugs stay English).\n"
            f"- Translate every other text value to short, natural {target_name} suitable "
            "for a classroom projector display.\n"
            "- Output STRICT JSON only. No markdown fence. No commentary.\n\n"
            f"# CARD TO TRANSLATE:\n{json.dumps(clean, ensure_ascii=False, indent=2)}\n\n"
            f"# {target_name.upper()} JSON OUTPUT:"
        )
        try:
            response = self.client.chat(
                model=self.config.MODEL_ID,
                messages=[{"role": "user", "content": prompt}],
                format="json",
                options={
                    "temperature": 0.2,
                    "top_p":       self.config.TOP_P,
                    "num_predict": self.config.NUM_PREDICT,
                    "num_ctx":     self.config.NUM_CTX,
                },
            )
        except Exception as e:
            print(f"[Sensei LLM] translate chat failed: {e}; returning original", flush=True)
            return clean

        raw = response["message"]["content"].strip()
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
        try:
            translated = json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"[Sensei LLM] translate JSON parse failed: {e}; returning original", flush=True)
            return clean

        # Force template field correct (model may drop it)
        translated["template"] = template
        schema = TEMPLATE_REGISTRY[template]
        try:
            return schema.model_validate(translated).model_dump()
        except ValidationError as e:
            print(f"[Sensei LLM] translate schema invalid: {e}; returning original", flush=True)
            return clean

    def summarize_session(self, transcripts: list[str], date_str: str = "") -> dict:
        """
        把今日所有逐字稿整理成一張「今日課程總結」enumeration_cards。
        故意鎖死模板為 enumeration_cards — 總結就是並列要點，不需要 LLM 自選結構。
        """
        if not transcripts:
            return {"template": "raw", "_error": "no_content"}
        joined = "\n---\n".join(transcripts)
        prompt = (
            "你是課程內容總結助理。整理老師今天上課的內容成一張 enumeration_cards 卡片。\n\n"
            "**輸出格式必須跟下面範例完全一致**（最外層是物件，內含 template/title/subtitle/items 四個 key）：\n\n"
            "範例輸出：\n"
            '{\n'
            '  "template": "enumeration_cards",\n'
            f'  "title": "今日課程總結 · {date_str}",\n'
            '  "subtitle": "本日主軸描述（≤20 字）",\n'
            '  "items": [\n'
            '    {"name": "PID 控制", "icon": "sliders", "desc": "業界主流"},\n'
            '    {"name": "強健控制", "icon": "shield", "desc": "穩定性保障"},\n'
            '    {"name": "故障診斷", "icon": "alert-triangle", "desc": "及時警示"},\n'
            '    {"name": "監控流程", "icon": "workflow", "desc": "量測到報警"}\n'
            '  ]\n'
            '}\n\n'
            "嚴格規則：\n"
            "1. 最外層必須有 \"template\" 欄位，值為 \"enumeration_cards\"（**不可**把 items 改名為 enumeration_cards）。\n"
            "2. items 陣列含 4–6 個物件，每個物件**必須同時有** name、icon、desc 三個欄位。\n"
            "3. name ≤ 8 字、desc ≤ 10 字、icon 用 Lucide slug。\n"
            "4. 繁體中文，無 markdown fence，無重複欄位。\n\n"
            f"# 今日內容\n{joined}\n\n"
            "# 直接輸出符合上述範例格式的 JSON："
        )
        try:
            response = self.client.chat(
                model=self.config.MODEL_ID,
                messages=[{"role": "user", "content": prompt}],
                format="json",
                options={
                    "temperature": 0.4,
                    "top_p":       self.config.TOP_P,
                    "num_predict": self.config.NUM_PREDICT,
                    "num_ctx":     8192,  # 多容納長 transcript 串接
                },
            )
        except Exception as e:
            return {"template": "raw", "_error": f"summarize_chat:{e}"}

        raw = response["message"]["content"].strip()
        return self._parse_and_validate(raw)

    def suggest_next(self, card_data: dict) -> list[str]:
        """
        從一張卡片提出 3 個「老師接下去可以講什麼」的建議句。
        刻意不用 format="json" — 在 e2b 上 format=json 會讓這類短陣列任務直接輸出空字串，
        改用 prompt + 後處理 regex 抽 array 反而穩定。
        """
        if not card_data:
            return []
        clean = {k: v for k, v in card_data.items() if not k.startswith("_")}
        # Keep ASCII-only in instructions; only the example uses Chinese.
        # Empirically gemma4:e2b is more reliable when the imperative is plain English.
        prompt = (
            f"Card: {json.dumps(clean, ensure_ascii=False)}\n\n"
            "Suggest 3 follow-up topics in Traditional Chinese (each under 25 chars).\n"
            "Output ONLY a JSON array of 3 strings.\n"
            'Example: ["xxxxx", "yyyyy", "zzzzz"]\n\n'
            "JSON array:"
        )
        # Small e2b sometimes returns empty completions on this task; retry up to 3x
        # with progressively more aggressive sampling to bust the empty-output pattern.
        retry_options = [
            {"temperature": 0.6, "top_p": 0.9,  "num_predict": 512, "num_ctx": 4096},
            {"temperature": 0.4, "top_p": 0.95, "num_predict": 512, "num_ctx": 4096},
            {"temperature": 0.9, "top_p": 1.0,  "num_predict": 256, "num_ctx": 2048},  # very different sampler
        ]
        raw = ""
        for attempt, opts in enumerate(retry_options, start=1):
            try:
                response = self.client.chat(
                    model=self.config.MODEL_ID,
                    messages=[{"role": "user", "content": prompt}],
                    options=opts,
                )
            except Exception as e:
                print(f"[Sensei LLM] suggest_next chat failed: {e}", flush=True)
                return []
            raw = (response["message"]["content"] or "").strip()
            if raw:
                break
            if attempt < len(retry_options):
                print(f"[Sensei LLM] suggest_next attempt {attempt} returned empty; retrying with different sampling", flush=True)
        if not raw:
            print(f"[Sensei LLM] suggest_next gave up after {len(retry_options)} attempts", flush=True)
            return []

        # Strip markdown fence if any
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
        # Extract first JSON array (allows surrounding prose if model adds any)
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return []

        if isinstance(parsed, list):
            items = parsed
        elif isinstance(parsed, dict):
            items = next((v for v in parsed.values() if isinstance(v, list)), [])
        else:
            return []
        return [str(s).strip() for s in items[:3] if s][:3]

    def extend(self, base_data: dict, new_text: str) -> dict:
        """
        延伸既有卡片：模板強制鎖死為 base_data['template']，
        LLM 只能在原有清單後新增項目，不可刪除或換模板。
        """
        template = (base_data or {}).get("template", "")
        if template not in TEMPLATE_REGISTRY:
            return {
                "template": "raw",
                "_error": f"cannot extend: unknown template '{template}'",
            }

        base_clean = {k: v for k, v in base_data.items() if not k.startswith("_")}
        base_json = json.dumps(base_clean, ensure_ascii=False, indent=2)
        prompt = (
            self.extend_template
            .replace("{base_json}", base_json)
            .replace("{user_text}", new_text)
            .replace("{template}", template)
        )
        response = self.client.chat(
            model=self.config.MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            format="json",
            options={
                "temperature": self.config.TEMPERATURE,
                "top_p":       self.config.TOP_P,
                "num_predict": self.config.NUM_PREDICT,
                "num_ctx":     self.config.NUM_CTX,
            },
        )
        raw = response["message"]["content"].strip()
        merged = self._parse_and_validate(raw)

        # If the LLM violated the template lock, fall back to the original card
        # rather than confusing the user with a different layout mid-lecture.
        if merged.get("template") not in (template, "raw"):
            print(
                f"[Sensei LLM] [!] Extend produced wrong template "
                f"(got {merged.get('template')}, expected {template}). Keeping original."
            )
            return {**base_clean, "_error": "extend_template_violated", "_raw": raw}
        return merged

    # ──────────────────────────────────────────────
    # Internals
    # ──────────────────────────────────────────────
    def _generate(self, user_text: str, template_hint: str | None = None) -> str:
        prompt = self.prompt_template.replace("{user_text}", user_text)
        if template_hint:
            prompt = (
                "# 模板強制提示（最高優先）\n\n"
                f"老師本次指定使用 `{template_hint}` 模板。"
                "請忽略「先判斷模板」這一步，直接以此模板填寫對應欄位的 JSON。\n"
                "若內容真的完全不適合此模板（極少發生），才允許退回自動判斷。\n\n"
                + prompt
            )
        response = self.client.chat(
            model=self.config.MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            format="json",                     # ← Ollama-native JSON enforcement
            options={
                "temperature": self.config.TEMPERATURE,
                "top_p":       self.config.TOP_P,
                "num_predict": self.config.NUM_PREDICT,
                "num_ctx":     self.config.NUM_CTX,
            },
        )
        return response["message"]["content"].strip()

    @staticmethod
    def _salvage_card_data(data: dict, template_name: str) -> dict:
        """填入小模型常忘的安全預設值，讓 schema 驗證能過。
        只填**確定不會誤導內容**的欄位（icon='circle' 是視覺占位、desc='' 是空字串）。
        絕不填 name / aspect / a_value 這類「內容性」欄位。"""
        salvaged = json.loads(json.dumps(data))  # deep copy
        if template_name == "enumeration_cards":
            for item in salvaged.get("items", []):
                if isinstance(item, dict):
                    item.setdefault("icon", "circle")
                    item.setdefault("desc", "")
                    item.setdefault("name_en", "")
                    item.setdefault("tag", "")
        elif template_name == "flow_diagram":
            for step in salvaged.get("steps", []):
                if isinstance(step, dict):
                    step.setdefault("desc", "")
                    step.setdefault("icon", "")
        elif template_name == "swot":
            salvaged.setdefault("subject", "")
            for q in ("strengths", "weaknesses", "opportunities", "threats"):
                for item in salvaged.get(q, []):
                    if isinstance(item, dict):
                        item.setdefault("desc", "")
        elif template_name == "pyramid":
            salvaged.setdefault("subject", "")
            for layer in salvaged.get("layers", []):
                if isinstance(layer, dict):
                    layer.setdefault("desc", "")
        elif template_name == "comparison_table":
            # comparison_table 的所有欄位都是「內容性」的，無法安全預設
            pass
        return salvaged

    def _parse_and_validate(self, raw: str) -> dict:
        # With format="json" Ollama should never emit code fences, but we
        # strip just in case (cheap insurance).
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"[Sensei LLM] [!] JSON parse failed: {e}")
            print(f"--- raw output ---\n{raw}\n------------------")
            return {"template": "raw", "_raw": raw, "_error": f"json: {e}"}

        template_name = data.get("template")
        schema = TEMPLATE_REGISTRY.get(template_name)
        if not schema:
            print(f"[Sensei LLM] [!] Unknown template: {template_name}")
            return {"template": "raw", "_raw": raw, "_error": f"unknown template: {template_name}"}

        # Strict validation first
        try:
            return schema.model_validate(data).model_dump()
        except ValidationError:
            pass  # try lenient salvage below

        # Lenient salvage: fill safe defaults for fields the small model commonly omits
        salvaged = self._salvage_card_data(data, template_name)
        try:
            result = schema.model_validate(salvaged).model_dump()
            print(f"[Sensei LLM] salvaged template={template_name} (filled missing defaults)", flush=True)
            result["_salvaged"] = True
            return result
        except ValidationError as e:
            print(f"[Sensei LLM] [!] Schema validation failed even after salvage: {e}")
            return {"template": "raw", "_raw": raw, "_error": f"schema: {e}", "_partial": data}


if __name__ == "__main__":
    import sys
    test_text = " ".join(sys.argv[1:]) or (
        "同學，控制不是只有 PID 控制，"
        "其實還有最佳、類神經、非線性、強健控制等等"
    )
    llm = SenseiLLM()
    result = llm.structurize(test_text)
    print("\n--- Result ---")
    print(json.dumps(result, ensure_ascii=False, indent=2))
