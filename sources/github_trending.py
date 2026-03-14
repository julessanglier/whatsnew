from scrapling import Fetcher
from .base import BaseSource, TrendingItem


class GitHubTrendingSource(BaseSource):
    name = "GitHub Trending"
    enabled = True

    def fetch(self) -> list[TrendingItem]:
        page = Fetcher.get("https://github.com/trending", timeout=30)

        items = []
        for repo in page.css("article.Box-row"):
            # Repo name
            name_el = repo.css("h2.h3 a")
            if not name_el:
                continue
            href = name_el[0].attrib.get("href", "")
            title = href.lstrip("/").replace("/", " / ")
            url = f"https://github.com{href}"

            # Description
            desc_el = repo.css("p.col-9")
            description = desc_el[0].text.strip() if desc_el else None

            # Language
            lang_el = repo.css("[itemprop='programmingLanguage']")
            language = lang_el[0].text.strip() if lang_el else None

            # Stars today
            stars = None
            star_els = repo.css("span.d-inline-block.float-sm-right")
            if star_els:
                parts = star_els[0].text.strip().replace(",", "").split()
                if parts:
                    try:
                        stars = int(parts[0])
                    except ValueError:
                        pass

            items.append(TrendingItem(
                title=title,
                url=url,
                description=description,
                language=language,
                stars=stars,
            ))

        return items
