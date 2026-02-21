"""
Email Content Generator - Module 3.
Generates subject lines, preview text, and email body copy
that is brand-voice-aligned and conversion-optimized.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import structlog

log = structlog.get_logger()


@dataclass
class EmailContent:
    subject_lines: list[dict]
    preview_text: str
    body_html: str
    body_plain: str
    cta_text: str
    predicted_open_rates: list[float] = field(default_factory=list)


class EmailGenerator:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.log = log.bind(component="EmailGenerator")

    def generate(
        self,
        brief: str,
        brand_voice_constraint: str,
        segment_name: str,
        offer_type: Optional[str] = None,
        offer_value: Optional[float] = None,
        personalization_tokens: Optional[dict] = None,
        n_subject_variants: int = 3,
    ) -> EmailContent:
        self.log.info("Generating email content", segment=segment_name)

        subject_lines = self._generate_subject_lines(
            brief=brief,
            brand_voice=brand_voice_constraint,
            n_variants=n_subject_variants,
            offer_type=offer_type,
            offer_value=offer_value,
        )

        preview = self._generate_preview_text(brief=brief, subject=subject_lines[0]["text"])
        body_plain = self._generate_body(
            brief=brief,
            brand_voice=brand_voice_constraint,
            segment=segment_name,
            offer_type=offer_type,
            offer_value=offer_value,
            personalization=personalization_tokens,
        )
        body_html = self._plain_to_html(body_plain)
        cta = self._generate_cta(brief=brief, offer_type=offer_type)

        return EmailContent(
            subject_lines=subject_lines,
            preview_text=preview,
            body_html=body_html,
            body_plain=body_plain,
            cta_text=cta,
        )

    def _generate_subject_lines(
        self,
        brief: str,
        brand_voice: str,
        n_variants: int,
        offer_type: Optional[str],
        offer_value: Optional[float],
    ) -> list[dict]:
        if self.llm_client:
            return self._llm_subject_lines(brief, brand_voice, n_variants, offer_type, offer_value)

        templates = [
            {"type": "urgency", "text": f"Don't miss out - {brief[:40]}"},
            {"type": "curiosity", "text": f"Here's something special just for you"},
            {"type": "direct", "text": f"Your exclusive offer is waiting"},
        ]
        if offer_type == "percentage_discount" and offer_value:
            templates[0]["text"] = f"Save {int(offer_value)}% today only"
            templates[1]["text"] = f"Your {int(offer_value)}% off is ready"
            templates[2]["text"] = f"Limited time: {int(offer_value)}% off for you"

        return templates[:n_variants]

    def _llm_subject_lines(self, brief, brand_voice, n, offer_type, offer_value) -> list[dict]:
        prompt = f"""Generate {n} email subject line variants.
Brief: {brief}
Brand voice: {brand_voice}
Offer: {offer_type} {offer_value if offer_value else ''}
Return as numbered list. Each should be under 60 characters.
Use different psychological hooks: urgency, curiosity, direct benefit."""
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            )
            raw = response.choices[0].message.content
            lines = [l.strip().lstrip("123456789. ") for l in raw.split("\n") if l.strip()]
            return [{"type": "variant", "text": line} for line in lines[:n]]
        except Exception as e:
            self.log.error("LLM call failed", error=str(e))
            return [{"type": "fallback", "text": brief[:60]}]

    def _generate_preview_text(self, brief: str, subject: str) -> str:
        return f"{brief[:80]}..."

    def _generate_body(
        self,
        brief: str,
        brand_voice: str,
        segment: str,
        offer_type: Optional[str],
        offer_value: Optional[float],
        personalization: Optional[dict],
    ) -> str:
        name_token = personalization.get("first_name", "there") if personalization else "there"
        offer_str = ""
        if offer_type and offer_value:
            offer_str = f"\n\nHere's your exclusive offer: {int(offer_value)}% off your next purchase."

        return f"""Hi {name_token},

{brief}
{offer_str}

We'd love to see you back.

Best,
The Team"""

    def _plain_to_html(self, plain: str) -> str:
        paragraphs = plain.strip().split("\n\n")
        html_parts = ["<html><body>"]
        for para in paragraphs:
            html_parts.append(f"<p>{para.replace(chr(10), '<br>')}</p>")
        html_parts.append("</body></html>")
        return "\n".join(html_parts)

    def _generate_cta(self, brief: str, offer_type: Optional[str]) -> str:
        cta_map = {
            "percentage_discount": "Claim My Discount",
            "free_shipping": "Shop with Free Shipping",
            "free_gift": "Claim My Free Gift",
            "bogo": "Shop Now",
        }
        return cta_map.get(offer_type or "", "Shop Now")
