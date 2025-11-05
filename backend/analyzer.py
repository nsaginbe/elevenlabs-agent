import os
import re
import json
import html
import openai
from typing import Any, Dict
from models import ConversationAnalysis
from dotenv import load_dotenv

load_dotenv()


class ConversationAnalyzer:
    def __init__(self):
        """Analyzer for training conversations.

        - Uses OpenAI if OPENAI_API_KEY is configured
        - Falls back to a lightweight heuristic analysis otherwise
        """
        api_key = os.getenv("OPENAI_API_KEY")
        # Initialize client only if API key is present
        self.client = openai.OpenAI(api_key=api_key) if api_key else None
        self.enabled = bool(api_key)

    async def analyze_conversation(self, conversation_log: str) -> ConversationAnalysis:
        """
        Анализирует разговор продажника с ИИ-клиентом
        """

        prompt = f"""
        Проанализируй разговор продажника с клиентом. Оцени по шкале от 1 до 10:
        
        Разговор:
        {conversation_log}
        
        Верни анализ в формате JSON:
        {{
            "score": <оценка от 1 до 10>,
            "strengths": [<список сильных сторон>],
            "areas_for_improvement": [<области для улучшения>],
            "specific_feedback": "<конкретные рекомендации>",
            "key_moments": [<ключевые моменты разговора>]
        }}
        
        Критерии оценки:
        - Установление контакта с клиентом
        - Выявление потребностей
        - Презентация продукта/услуги
        - Работа с возражениями
        - Закрытие сделки
        - Общее впечатление
        """

        try:
            if not self.client:
                # No API configured – return heuristic analysis
                return self._fallback_analysis(conversation_log)

            response = self.client.chat.completions.create(
                # Prefer a widely available, cost-efficient model
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {
                        "role": "system",
                        "content": "Ты эксперт по продажам, анализирующий разговоры продажников. Отвечай только в формате JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )

            analysis_text = response.choices[0].message.content or ""
            analysis_data = self._extract_json(analysis_text)
            return ConversationAnalysis(**analysis_data)

        except Exception as e:
            print(f"Ошибка анализа: {e}")
            return self._fallback_analysis(conversation_log)

    def format_analysis_for_display(self, analysis: ConversationAnalysis) -> str:
        """Форматирует анализ в HTML для безопасного отображения на фронтенде."""
        # Escape all text content to prevent HTML injection
        def li(items: list[str]) -> str:
            return "\n".join(
                f"<li>{html.escape(str(item))}</li>" for item in items if str(item).strip()
            ) or "<li>—</li>"

        score_html = html.escape(f"{analysis.score}")
        feedback_html = html.escape(analysis.specific_feedback or "")

        return (
            "<section>"
            "<h1>📊 Анализ тренировочной сессии</h1>"
            f"<h2>Общая оценка: {score_html}/10</h2>"
            "<h3>✅ Сильные стороны</h3>"
            f"<ul>{li(analysis.strengths)}</ul>"
            "<h3>🎯 Области для улучшения</h3>"
            f"<ul>{li(analysis.areas_for_improvement)}</ul>"
            "<h3>💡 Конкретные рекомендации</h3>"
            f"<p>{feedback_html}</p>"
            "<h3>🔑 Ключевые моменты</h3>"
            f"<ul>{li(analysis.key_moments)}</ul>"
            "</section>"
        )

    # -----------------------------
    # Helpers
    # -----------------------------
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON object from a model response that may include prose.

        Falls back to a minimal structure if parsing fails.
        """
        try:
            # Try direct parse first
            return json.loads(text)
        except Exception:
            pass

        # Extract the longest {...} block to parse
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = text[start : end + 1]
                return json.loads(candidate)
        except Exception:
            pass

        # Try to clean common JSON issues (trailing commas, single quotes)
        cleaned = text.replace("'", '"')
        cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
        try:
            return json.loads(cleaned)
        except Exception:
            # Final fallback to heuristic analysis
            fa = self._fallback_analysis(text)
            return fa.dict()

    def _fallback_analysis(self, conversation_log: str) -> ConversationAnalysis:
        """Heuristic fallback analysis when OpenAI is unavailable or fails."""
        text = conversation_log or ""
        length = len(text.split())
        questions = text.count("?")
        objections = sum(text.lower().count(k) for k in ["дорого", "не устраивает", "сомневаюсь", "возраж"])  # ru
        closing = sum(text.lower().count(k) for k in ["готовы оформить", "оформим", "договор", "сделка"])  # ru

        # Simple scoring heuristic (1..10)
        score = 5.0
        score += min(2.0, questions * 0.5)  # asking questions is good
        score += min(1.5, closing * 0.75)
        score -= min(2.0, objections * 0.5)
        score += 1.0 if length > 120 else 0.0  # enough content
        score = max(1.0, min(10.0, round(score, 1)))

        strengths = []
        if questions >= 2:
            strengths.append("Вы задаете уточняющие вопросы и выявляете потребности")
        if closing >= 1:
            strengths.append("Попытка закрыть сделку присутствует")
        if length > 120:
            strengths.append("Содержательное общение с достаточной детализацией")
        if not strengths:
            strengths.append("Поддерживается вежливый тон и деловой стиль общения")

        improvements = []
        if objections == 0:
            improvements.append("Потренируйтесь работать с возражениями клиента")
        if questions < 2:
            improvements.append("Задавайте больше открытых вопросов для выявления потребностей")
        if closing == 0:
            improvements.append("Добавьте четкий шаг закрытия сделки с призывом к действию")

        key_moments = [
            "Начало разговора и установление контакта",
            "Уточнение потребностей и ожиданий клиента",
            "Презентация ценности продукта",
            "Работа с возражениями",
            "Закрытие и согласование следующих шагов",
        ]

        feedback = (
            "Сфокусируйтесь на выявлении потребностей через открытые вопросы, "
            "фиксируйте ключевые возражения и предлагайте варианты решения. "
            "Завершайте разговор явным согласованием следующих шагов."
        )

        return ConversationAnalysis(
            score=score,
            strengths=strengths,
            areas_for_improvement=improvements,
            specific_feedback=feedback,
            key_moments=key_moments,
        )
