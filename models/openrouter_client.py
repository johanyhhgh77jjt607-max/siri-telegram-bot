"""
عميل OpenRouter - الوصول لـ 200+ نموذج (GPT-4o, Claude 3.5, etc.)
بمفتاح API واحد
"""
from openai import AsyncOpenAI
from typing import Optional

class OpenRouterClient:
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, model: Optional[str] = None, temperature: float = 0.3, max_tokens: int = 4096) -> str:
        messages = []; if system_prompt: messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = await self.client.chat.completions.create(model=model or "openai/gpt-4o", messages=messages, temperature=temperature, max_tokens=max_tokens)
        return response.choices[0].message.content

    async def generate_code_gpt4o(self, description: str) -> str:
        return await self.generate(f"أنشئ كود Python كامل ونظيف للتالي:\n{description}", system_prompt="أنت خبير Python محترف. أخرج الكود فقط داخل ```python ... ``` مع شرح موجز بالعربية.", model="openai/gpt-4o")

    async def review_code_claude(self, code: str) -> str:
        return await self.generate(f"راجع الكود التالي بعمق:\n```python\n{code}\n```", system_prompt="أنت مراجع أكواد Python خبير. ركز على: 1. الأخطاء المنطقية 2. الثغرات الأمنية 3. حالات الحافة 4. كفاءة الخوارزميات 5. قابلية الصيانة. التقرير بالعربية.", model="anthropic/claude-3.5-sonnet")

    async def analyze_patterns_gpt4o(self, code: str) -> str:
        return await self.generate(f"حلل أنماط التصميم وأفضل الممارسات: {code}", system_prompt="أنت محلل أنماط برمجية. Design Patterns, PEP 8, توثيق, معالجة الأخطاء, اقيراحات, بالعربية.", model="openai/gpt-4o")

    async def fix_code_gpt4o(self, code: str, error: Optional[str] = None) -> str:
        error_info = f"\nالخطأ: {error}" if error else ""
        return await self.generate(f"صحح الكود التالي وأخرج الكود المُصلح فقط داخل ```python ... ```{error_info}\nالكود:\n```python\n{code}\n```", system_prompt="أنت خبير تصحيح أخطاء Python. أصلح جميع الأخطاء وأخرج الكود النظيف.", model="openai/gpt-4o")

    async def validate_fix_claude(self, original: str, fixed: str) -> str:
        return await self.generate(f"الكود الأصلي:\n```python\n{original}\n```\nالكود المُصلح:\n```python\n{fixed}\n```", system_prompt="قارن الكود الأصلي بالمُصلح. هل تم تصحيح جميع الأخطاء؟ هل هناك أخطاء جديدة؟ هل تحسن الكود فعلاً؟ أجب بالعربية مع تقييم نهائي: ✅ نجح أو ❌ يحتاج مراجعة.", model="anthropic/claude-3.5-sonnet")
