"""Jobs shown only when the seeker already knows someone at the company."""

from __future__ import annotations

import re
from typing import Any, Iterable

_STRIP = re.compile(r"\b(incorporated|corporation|company|labs?|inc|llc|ltd|corp|co)\b")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")

ALIASES = {
    "alphabet": "google",
    "googlellc": "google",
    "meta": "meta",
    "facebook": "meta",
    "instagram": "meta",
    "x": "x",
    "twitter": "x",
    "openai": "openai",
    "microsoft": "microsoft",
    "msft": "microsoft",
    "amazon": "amazon",
    "aws": "amazon",
    "apple": "apple",
    "netflix": "netflix",
    "airbnb": "airbnb",
    "stripe": "stripe",
    "shopify": "shopify",
    "nvidia": "nvidia",
    "notion": "notion",
    "figma": "figma",
    "spotify": "spotify",
    "uber": "uber",
}

CATALOG: list[dict[str, Any]] = [
    {"id": "google-swe", "company": "Google", "title": "Software Engineer", "location": "Mountain View / Remote", "url": "https://careers.google.com", "blurb": "Build products used by billions. Strong CS fundamentals and shipped work."},
    {"id": "google-sre", "company": "Google", "title": "Site Reliability Engineer", "location": "New York / Remote", "url": "https://careers.google.com", "blurb": "Keep production boring. On-call, automation, and capacity planning."},
    {"id": "google-pm", "company": "Google", "title": "Product Manager", "location": "Seattle / Hybrid", "url": "https://careers.google.com", "blurb": "Own a slice of a consumer surface. Metrics, narrative, and engineering partnership."},
    {"id": "meta-swe", "company": "Meta", "title": "Software Engineer, Product", "location": "Menlo Park / Remote", "url": "https://www.metacareers.com", "blurb": "Ship social product. Move fast with reviewable diffs and clear impact."},
    {"id": "meta-ml", "company": "Meta", "title": "Machine Learning Engineer", "location": "New York", "url": "https://www.metacareers.com", "blurb": "Ranking and retrieval at scale. PyTorch and production instincts."},
    {"id": "meta-design", "company": "Meta", "title": "Product Designer", "location": "London / Hybrid", "url": "https://www.metacareers.com", "blurb": "Craft flows people touch every day. Systems thinking plus taste."},
    {"id": "stripe-swe", "company": "Stripe", "title": "Backend Engineer", "location": "Remote — Americas", "url": "https://stripe.com/jobs", "blurb": "Payments infrastructure. APIs that other companies bet their business on."},
    {"id": "stripe-fe", "company": "Stripe", "title": "Frontend Engineer, Dashboard", "location": "San Francisco / Remote", "url": "https://stripe.com/jobs", "blurb": "The Dashboard is the product. TypeScript, accessibility, and money UX."},
    {"id": "stripe-pm", "company": "Stripe", "title": "Product Manager, Connect", "location": "Seattle / Hybrid", "url": "https://stripe.com/jobs", "blurb": "Platforms that let other platforms take payments. Precision over slogans."},
    {"id": "netflix-swe", "company": "Netflix", "title": "Senior Software Engineer", "location": "Los Gatos / Remote", "url": "https://jobs.netflix.com", "blurb": "Streaming systems and studio tools. High freedom, high accountability."},
    {"id": "netflix-data", "company": "Netflix", "title": "Data Engineer", "location": "Los Angeles", "url": "https://jobs.netflix.com", "blurb": "Pipelines behind personalization. Reliability matters more than novelty."},
    {"id": "airbnb-swe", "company": "Airbnb", "title": "Full Stack Engineer", "location": "San Francisco / Remote", "url": "https://careers.airbnb.com", "blurb": "Host and guest product. End-to-end ownership on a consumer marketplace."},
    {"id": "airbnb-pm", "company": "Airbnb", "title": "Product Manager, Search", "location": "New York / Hybrid", "url": "https://careers.airbnb.com", "blurb": "Help people find a place to stay. Ranking, trust, and conversion."},
    {"id": "shopify-swe", "company": "Shopify", "title": "Software Engineer", "location": "Remote — North America", "url": "https://www.shopify.com/careers", "blurb": "Commerce OS for merchants. Ruby, React, and operational empathy."},
    {"id": "nvidia-swe", "company": "NVIDIA", "title": "Systems Software Engineer", "location": "Santa Clara / Hybrid", "url": "https://nvidia.wd5.myworkdayjobs.com", "blurb": "CUDA, drivers, and the stack under AI. Low-level work with huge leverage."},
    {"id": "nvidia-ml", "company": "NVIDIA", "title": "Deep Learning Engineer", "location": "Austin / Hybrid", "url": "https://nvidia.wd5.myworkdayjobs.com", "blurb": "Train and serve models on GPUs you also help design."},
    {"id": "openai-swe", "company": "OpenAI", "title": "Software Engineer, API", "location": "San Francisco", "url": "https://openai.com/careers", "blurb": "The API is the product. Latency, reliability, and developer experience."},
    {"id": "openai-research", "company": "OpenAI", "title": "Research Engineer", "location": "San Francisco", "url": "https://openai.com/careers", "blurb": "Sit between research and production. Experiments that have to ship."},
    {"id": "microsoft-swe", "company": "Microsoft", "title": "Software Engineer II", "location": "Redmond / Remote", "url": "https://careers.microsoft.com", "blurb": "Cloud and developer tools. Large surface area, real customers."},
    {"id": "amazon-sde", "company": "Amazon", "title": "Software Development Engineer", "location": "Seattle / Arlington", "url": "https://www.amazon.jobs", "blurb": "Ownership in a two-pizza team. Write the design, then the service."},
    {"id": "apple-swe", "company": "Apple", "title": "Software Engineer, Platform", "location": "Cupertino", "url": "https://jobs.apple.com", "blurb": "Frameworks other Apple products stand on. Privacy and craft are the bar."},
    {"id": "notion-swe", "company": "Notion", "title": "Software Engineer", "location": "New York / SF / Remote", "url": "https://www.notion.com/careers", "blurb": "A doc that became an OS for work. Performance and multiplayer editing."},
    {"id": "figma-swe", "company": "Figma", "title": "Product Engineer", "location": "San Francisco / Remote", "url": "https://www.figma.com/careers", "blurb": "Browser-native design tools. Rendering, collab, and taste in the pixels."},
    {"id": "spotify-swe", "company": "Spotify", "title": "Backend Engineer", "location": "Stockholm / New York", "url": "https://www.lifeatspotify.com", "blurb": "Recommendations and playback. Music at scale, with editorial partners."},
    {"id": "uber-swe", "company": "Uber", "title": "Software Engineer, Marketplace", "location": "San Francisco / Remote", "url": "https://www.uber.com/careers", "blurb": "Matching, pricing, and reliability when the city is moving."},
]


def company_key(name: str) -> str:
    raw = _STRIP.sub(" ", (name or "").lower())
    compact = _NON_ALNUM.sub("", raw)
    return ALIASES.get(compact, compact)


def jobs_through_people(
    contacts: Iterable[dict[str, Any]],
    *,
    hidden_ids: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Return swipe cards for jobs at companies where the user knows someone."""
    hidden = set(hidden_ids or [])
    cards: list[dict[str, Any]] = []
    seen: set[str] = set()

    for contact in contacts:
        person = str(contact.get("name") or "").strip()
        company = str(contact.get("company") or "").strip()
        if not person or not company:
            continue
        key = company_key(company)
        if not key:
            continue
        relation = str(contact.get("relation") or "knows").strip() or "knows"
        matches = [job for job in CATALOG if company_key(job["company"]) == key]
        if matches:
            for job in matches:
                card_id = f"{job['id']}@{contact.get('id')}"
                if card_id in hidden or card_id in seen:
                    continue
                seen.add(card_id)
                cards.append(
                    {
                        **job,
                        "id": card_id,
                        "catalog_id": job["id"],
                        "kind": "role",
                        "through": {
                            "id": contact.get("id"),
                            "name": person,
                            "company": company,
                            "relation": relation,
                        },
                    }
                )
        else:
            card_id = f"intro-{contact.get('id')}"
            if card_id in hidden or card_id in seen:
                continue
            seen.add(card_id)
            cards.append(
                {
                    "id": card_id,
                    "catalog_id": card_id,
                    "kind": "intro",
                    "company": company,
                    "title": f"Ask {person} about openings",
                    "location": company,
                    "url": "",
                    "blurb": (
                        f"{person} is your link at {company}. "
                        "There isn’t a public posting in our deck — swipe right to treat this as an intro to ask for."
                    ),
                    "through": {
                        "id": contact.get("id"),
                        "name": person,
                        "company": company,
                        "relation": relation,
                    },
                }
            )
    return cards
