import re
import json
import httpx
from .base import BaseSource, TrendingItem

_SKILLS_URL = "https://skills.sh/?sort=trending"
_BASE_URL = "https://skills.sh"


class SkillsShSource(BaseSource):
    name = "skills.sh"
    enabled = True

    def fetch(self) -> list[TrendingItem]:
        response = httpx.get(_SKILLS_URL, timeout=30, follow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        html = response.text

        # Data is embedded in Next.js RSC payload: __next_f.push([1,"..."])
        # The inner string has escaped quotes (\"), so we extract and unescape it
        skills = self._extract_skills(html)
        if not skills:
            return []

        items = []
        for skill in skills[:25]:
            skill_id = skill.get("skillId", "")
            source = skill.get("source", "")
            installs = skill.get("installs", 0)
            name = skill.get("name") or skill_id

            url = f"{_BASE_URL}/{source}/{skill_id}" if source else f"{_BASE_URL}/{skill_id}"

            if installs >= 1_000_000:
                installs_label = f"{installs / 1_000_000:.1f}M"
            elif installs >= 1_000:
                installs_label = f"{installs / 1_000:.1f}K"
            else:
                installs_label = str(installs)

            items.append(TrendingItem(
                title=name,
                url=url,
                description=source or None,
                stars=installs,
                extra={"installs_label": installs_label},
            ))

        return items

    def _extract_skills(self, html: str) -> list[dict]:
        # Find the __next_f.push segment containing initialSkills
        push_matches = re.finditer(r'__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', html)
        for m in push_matches:
            # Unescape the inner JSON string
            inner = m.group(1).encode().decode("unicode_escape")
            if "initialSkills" not in inner:
                continue
            # Extract the initialSkills array from the unescaped content
            arr_match = re.search(r'"initialSkills"\s*:\s*(\[.*?\])\s*[,}]', inner, re.DOTALL)
            if arr_match:
                try:
                    return json.loads(arr_match.group(1))
                except json.JSONDecodeError:
                    pass

        # Fallback: find skill objects directly via escaped pattern
        idx = html.find('"initialSkills"')
        if idx == -1:
            idx = html.find('\\"initialSkills\\"')
            if idx == -1:
                return []
            # Unescape the surrounding chunk
            chunk = html[idx - 2:idx + 50_000].replace('\\"', '"').replace('\\\\', '\\')
            arr_match = re.search(r'"initialSkills"\s*:\s*(\[.*?\])\s*[,}]', chunk, re.DOTALL)
        else:
            arr_match = re.search(r'"initialSkills"\s*:\s*(\[.*?\])\s*[,}]', html[idx:idx + 50_000], re.DOTALL)

        if arr_match:
            try:
                return json.loads(arr_match.group(1))
            except json.JSONDecodeError:
                pass

        return []
