"""
X (Twitter) 爆款内容抓取器
用法: python x_scraper.py [--limit 20] [--min-likes 500]
输出: data/tasks/<timestamp>_raw.json
"""
import asyncio
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import cfg

AUTH_STATE = cfg.data_dir / "x_auth_state.json"


async def login_if_needed(page, ctx):
    if AUTH_STATE.exists():
        return
    await page.goto("https://x.com/login", wait_until="networkidle")
    await page.fill('input[name="text"]', cfg.x_username)
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(1500)
    # 处理可能出现的手机号/用户名二次确认
    if await page.locator('input[name="text"]').count() > 0:
        await page.fill('input[name="text"]', cfg.x_username)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(1000)
    await page.fill('input[name="password"]', cfg.x_password)
    await page.keyboard.press("Enter")
    await page.wait_for_url("**/home", timeout=20000)
    await ctx.storage_state(path=str(AUTH_STATE))
    print("[scraper] 登录成功，已保存登录态")


async def scrape_timeline(limit: int = 20, min_likes: int = 500) -> list[dict]:
    results = []
    ctx_kwargs = {}
    if AUTH_STATE.exists():
        ctx_kwargs["storage_state"] = str(AUTH_STATE)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            **ctx_kwargs,
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await ctx.new_page()
        await login_if_needed(page, ctx)

        await page.goto("https://x.com/home", wait_until="networkidle")
        await page.wait_for_timeout(2000)

        seen_ids: set[str] = set()
        scroll_count = 0

        while len(results) < limit and scroll_count < 20:
            tweets = await page.query_selector_all('article[data-testid="tweet"]')
            for tweet in tweets:
                try:
                    tweet_id = await _extract_tweet_id(tweet)
                    if not tweet_id or tweet_id in seen_ids:
                        continue
                    seen_ids.add(tweet_id)

                    text = await _safe_text(tweet, '[data-testid="tweetText"]')
                    author = await _safe_text(tweet, '[data-testid="User-Name"]')
                    likes = await _parse_count(tweet, '[data-testid="like"] span')
                    retweets = await _parse_count(tweet, '[data-testid="retweet"] span')
                    replies = await _parse_count(tweet, '[data-testid="reply"] span')

                    if likes < min_likes:
                        continue

                    results.append({
                        "id": tweet_id,
                        "text": text,
                        "author": author,
                        "likes": likes,
                        "retweets": retweets,
                        "replies": replies,
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                        "url": f"https://x.com/i/web/status/{tweet_id}",
                    })
                except Exception:
                    continue

            await page.evaluate("window.scrollBy(0, 1200)")
            await page.wait_for_timeout(1800)
            scroll_count += 1

        await browser.close()

    results.sort(key=lambda x: x["likes"] + x["retweets"] * 3, reverse=True)
    return results[:limit]


async def _extract_tweet_id(tweet) -> str | None:
    link = await tweet.query_selector('a[href*="/status/"]')
    if not link:
        return None
    href = await link.get_attribute("href") or ""
    parts = href.split("/status/")
    return parts[1].split("/")[0] if len(parts) > 1 else None


async def _safe_text(el, selector: str) -> str:
    node = await el.query_selector(selector)
    return (await node.inner_text()).strip() if node else ""


async def _parse_count(el, selector: str) -> int:
    node = await el.query_selector(selector)
    if not node:
        return 0
    text = (await node.inner_text()).strip().replace(",", "")
    if not text:
        return 0
    for suffix, mult in [("K", 1000), ("M", 1_000_000)]:
        if text.upper().endswith(suffix):
            return int(float(text[:-1]) * mult)
    try:
        return int(text)
    except ValueError:
        return 0


def save_raw(data: list[dict]) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = cfg.tasks_dir / f"{ts}_raw.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"[scraper] 保存 {len(data)} 条推文 → {out}")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--min-likes", type=int, default=500)
    args = parser.parse_args()
    data = asyncio.run(scrape_timeline(args.limit, args.min_likes))
    save_raw(data)
