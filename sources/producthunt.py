import os
import httpx
from scrapling import Fetcher
from .base import BaseSource, TrendingItem


class ProductHuntSource(BaseSource):
    name = "Product Hunt"
    enabled = True

    def fetch(self) -> list[TrendingItem]:
        api_key = os.environ.get("PRODUCTHUNT_API_KEY", "").strip()
        if api_key:
            return self._fetch_api(api_key)
        return self._fetch_scrape()

    def _fetch_api(self, api_key: str) -> list[TrendingItem]:
        query = """
        {
          posts(order: VOTES, first: 20) {
            edges {
              node {
                name
                tagline
                url
                votesCount
                website
              }
            }
          }
        }
        """
        response = httpx.post(
            "https://api.producthunt.com/v2/api/graphql",
            json={"query": query},
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        edges = data.get("data", {}).get("posts", {}).get("edges", [])
        items = []
        for edge in edges:
            node = edge["node"]
            items.append(TrendingItem(
                title=node["name"],
                url=node["url"],
                description=node.get("tagline"),
                stars=node.get("votesCount"),
            ))
        return items

    def _fetch_scrape(self) -> list[TrendingItem]:
        page = Fetcher.get("https://www.producthunt.com", timeout=30)

        items = []
        # Try to find post items
        posts = page.css("[data-test='post-item']")
        if not posts:
            # Fallback selector
            posts = page.css("li[class*='item']")

        for post in posts[:20]:
            title_el = post.css("h3") or post.css("strong")
            if not title_el:
                continue
            title = title_el[0].text.strip()

            link_el = post.css("a[href*='/posts/']")
            if not link_el:
                continue
            href = link_el[0].attrib.get("href", "")
            if href.startswith("/"):
                url = f"https://www.producthunt.com{href}"
            else:
                url = href

            desc_el = post.css("span[class*='tagline']") or post.css("p")
            description = desc_el[0].text.strip() if desc_el else None

            items.append(TrendingItem(
                title=title,
                url=url,
                description=description,
            ))

        return items
