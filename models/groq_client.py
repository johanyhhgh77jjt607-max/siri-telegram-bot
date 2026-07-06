"""
عميل Groq - اتصال فائق السرعة بنماذج Llama/Mixtral
"""
from groq import AsyncGroq
from typing import Optional

class GroqClient:
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.client = AsyncGroq(api_key=api_key)
        self.model = model

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt: messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = await self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.3, max_tokens=4096)
        return response.choices[0].message.content

    async def explain_code(self, code: str) -> str:
        prompt = f"شرح الكود التالي باللغة العربية شرحاً م!:\n```python\n{code}\n```"
        return await self.generate(prompt)

    async def optimize_code(self, code: str) -> str:
        prompt = f"قم بتحسين الكود لمن حيث الأداء والسرعة:\n```python\n{code}\n```"
        return await self.generate(prompt)
