"""
Web Scraping Data Source for Consumer Goods.

抓取京东/天猫/淘宝/1688 的商品价格历史数据。
依赖: requests, beautifulsoup4

注意：
- 本模块仅用于个人研究学习，请遵守各平台 robots.txt 和使用条款。
- 京东/天猫价格页有反爬机制，生产环境建议用官方 API（需企业认证）。
"""

import re
import time
import json
from datetime import date, datetime
from typing import Optional
import requests
from bs4 import BeautifulSoup

from price_reasoner.models import CompetitorPricePoint


class WebScrapingDataSource:
    """
    通过爬虫抓取电商平台商品价格历史。

    支持平台：
    - 1688（最宽松，适合批发品）
    - 京东（需要较完整的 headers）
    - 天猫/淘宝（反爬最严）

    使用方式：
        ds = WebScrapingDataSource()
        prices = ds.get_price_history_jd(sku_id="100012043456", days=90)
    """

    # 常用 User-Agent 轮换
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]

    def __init__(self, timeout: int = 10, delay: float = 2.0):
        """
        Args:
            timeout: 请求超时（秒）
            delay: 请求间隔（秒），用于控制抓取频率
        """
        self.timeout = timeout
        self.delay = delay
        self._session = requests.Session()
        self._last_request_time = 0.0

    def _headers(self) -> dict:
        """生成随机轮换的请求头。"""
        import random
        return {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "DNT": "1",
        }

    def _get(self, url: str, params=None) -> Optional[requests.Response]:
        """带频率控制的 GET 请求。"""
        time.sleep(max(0, self.delay - (time.time() - self._last_request_time)))
        try:
            resp = self._session.get(url, params=params, headers=self._headers(), timeout=self.timeout)
            self._last_request_time = time.time()
            resp.raise_for_status()
            return resp
        except Exception as e:
            print(f"[WebScrapingDataSource] Request failed: {url} -> {e}")
            return None

    # ── 1688 ────────────────────────────────────────────────────────────────

    def get_price_history_1688(self, product_id: str, days: int = 90) -> list[CompetitorPricePoint]:
        """
        抓取1688商品价格走势。

        1688 有部分公开的价格曲线数据页面。
        注意：部分商品可能没有历史价格数据。

        Args:
            product_id: 1688 商品ID（链接中 ?offerId= 后面的数字）
            days: 抓取最近多少天的数据
        """
        # 1688 价格曲线 API（公开接口，部分商品可用）
        # https://offer.1688.com/service/price_chart_data.htm?offerId=xxx
        url = "https://offer.1688.com/service/price_chart_data.htm"
        params = {"offerId": product_id}

        resp = self._get(url, params=params)
        if not resp:
            return []

        try:
            # 1688 返回的是 JavaScript 回调格式
            text = resp.text
            # 去掉 JSONP 包装
            match = re.search(r'\{".*\}', text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                points = []
                for item in data.get("data", []):
                    price = float(item.get("price", 0))
                    dt = datetime.fromtimestamp(item.get("time", 0) / 1000).date()
                    if price > 0:
                        points.append(CompetitorPricePoint(
                            date=dt,
                            price=price,
                            currency="CNY",
                            source="1688",
                        ))
                return points
        except Exception as e:
            print(f"[1688] Parse error: {e}")

        return []

    # ── 京东 ────────────────────────────────────────────────────────────────

    def get_price_history_jd(self, sku_id: str, days: int = 90) -> list[CompetitorPricePoint]:
        """
        抓取京东商品历史价格。

        使用京东移动端接口（反爬比 PC 端宽松）。
        返回每日价格（如果有数据）。

        Args:
            sku_id: 京东 SKU ID（商品链接中 skuId 或 item.jd.com/数字）
            days: 抓取天数
        """
        # 京东移动端价格接口
        url = f"https://m.jd.com/services/repast/v1/priceHistory/queryBySku"
        params = {"skuId": sku_id}

        resp = self._get(url, params=params)
        if not resp:
            return []

        try:
            data = resp.json()
            price_list = data.get("data", [])
            points = []
            for item in price_list:
                try:
                    dt_str = item.get("date", "")
                    price = float(item.get("price", 0))
                    if price > 0 and dt_str:
                        dt = datetime.strptime(dt_str, "%Y-%m-%d").date()
                        points.append(CompetitorPricePoint(
                            date=dt,
                            price=price,
                            currency="CNY",
                            source="jd",
                        ))
                except Exception:
                    continue
            return points[-days:] if len(points) > days else points
        except Exception as e:
            print(f"[JD] Parse error: {e}")

        return []

    def get_product_info_jd(self, sku_id: str) -> Optional[dict]:
        """
        获取京东商品基本信息（名称、价格、店铺名）。

        Returns:
            dict: {"name": "...", "shop": "...", "price": 0.0, "category": "..."}
        """
        # 京东商品详情移动接口
        url = f"https://m.jd.com/services/product/v1/detail/basicInfo"
        params = {"skuId": sku_id}

        resp = self._get(url, params=params)
        if not resp:
            return None

        try:
            data = resp.json()
            info = data.get("data", {})
            return {
                "name": info.get("name", ""),
                "shop": info.get("shopName", ""),
                "price": float(info.get("jdPrice", info.get("price", 0))),
                "category": info.get("category", ""),
            }
        except Exception as e:
            print(f"[JD info] Parse error: {e}")
        return None

    # ── 慢慢买（通过 Chrome 插件数据接口） ─────────────────────────────────

    def get_price_history_manmanmai(self, url: str, days: int = 90) -> list[CompetitorPricePoint]:
        """
        通过慢慢买插件的接口抓取任意电商商品历史价格。

        慢慢买本身是一个比价平台，它会缓存各平台商品的历史价格。
        通过找到商品在慢慢买的对应对应，可以绕过直接爬取的反爬问题。

        Args:
            url: 京东/天猫/淘宝/1688 的任意商品链接
            days: 抓取天数
        """
        # 慢慢买有一个公开的比价跳转接口
        # 这里需要先调用 慢慢买 的搜索/匹配 API 获取 mmbSkuId
        # 然后再调用价格历史接口

        # Step 1: 获取慢慢买商品ID
        match_url = "https://www.manmanbuy.com/tools/ajax.ashx"
        params = {
            "method": "getmmb",
            "t": int(time.time() * 1000),
            "url": url,
        }

        resp = self._get(match_url, params=params)
        if not resp:
            return []

        try:
            mmb_data = resp.json()
            mmb_id = mmb_data.get("mmbid") or mmb_data.get("mmbId")
            if not mmb_id:
                return []

            # Step 2: 获取历史价格
            history_url = "https://www.manmanbuy.com/tools/ajax.ashx"
            history_params = {
                "method": "gethistory",
                "t": int(time.time() * 1000),
                "mmbid": mmb_id,
            }

            hist_resp = self._get(history_url, params=history_params)
            if not hist_resp:
                return []

            hist_data = hist_resp.json()
            points = []
            for item in hist_data.get("data", []):
                try:
                    price = float(item.get("price", 0))
                    dt_str = item.get("date", "")
                    if price > 0 and dt_str:
                        dt = datetime.strptime(dt_str, "%Y-%m-%d").date()
                        points.append(CompetitorPricePoint(
                            date=dt,
                            price=price,
                            currency="CNY",
                            source="manmanmai",
                        ))
                except Exception:
                    continue
            return points[-days:] if len(points) > days else points

        except Exception as e:
            print(f"[ManManMai] error: {e}")

        return []

    # ── 淘宝/天猫（通过 taobao 移动端） ─────────────────────────────────────

    def get_price_history_taobao(self, item_id: str, platform: str = "taobao") -> list[CompetitorPricePoint]:
        """
        抓取淘宝/天猫商品历史价格。

        通过手机端接口尝试获取，价格可能需要登录。

        Args:
            item_id: 淘宝商品ID（链接中 id= 后面的数字）
            platform: "taobao" 或 "tmall"
        """
        # 手机淘宝价格历史接口
        api_map = {
            "taobao": "https://h5.m.taobao.com/awp/mtb/price-history/price-query.json",
            "tmall": "https://pages.tmall.com/wow/awcp/act/price-history/query.json",
        }
        url = api_map.get(platform, api_map["taobao"])
        params = {"itemId": item_id}

        resp = self._get(url, params=params)
        if not resp:
            return []

        try:
            data = resp.json()
            items = data.get("items", []) or data.get("data", {}).get("items", [])
            points = []
            for item in items:
                price = float(item.get("price", 0))
                dt_str = item.get("date", "") or item.get("time", "")
                if price > 0 and dt_str:
                    try:
                        dt = datetime.strptime(dt_str[:10], "%Y-%m-%d").date()
                        points.append(CompetitorPricePoint(
                            date=dt,
                            price=price,
                            currency="CNY",
                            source=platform,
                        ))
                    except Exception:
                        continue
            return points
        except Exception as e:
            print(f"[Taobao] Parse error: {e}")

        return []

    # ── 通用 URL 识别 ───────────────────────────────────────────────────────

    def parse_product_url(self, url: str) -> dict:
        """
        从商品 URL 中自动识别平台和商品ID。

        Returns:
            {"platform": "jd"|"taobao"|"tmall"|"1688"|"unknown",
             "product_id": "...",
             "original_url": "..."}
        """
        info = {"platform": "unknown", "product_id": "", "original_url": url}

        if "jd.com" in url:
            m = re.search(r"(\d{6,})", url)
            info["platform"] = "jd"
            info["product_id"] = m.group(1) if m else ""
        elif "taobao.com" in url or "tb.cn" in url:
            m = re.search(r"id=(\d+)", url)
            info["platform"] = "taobao"
            info["product_id"] = m.group(1) if m else ""
        elif "tmall.com" in url:
            m = re.search(r"id=(\d+)", url)
            info["platform"] = "tmall"
            info["product_id"] = m.group(1) if m else ""
        elif "1688.com" in url:
            m = re.search(r"offerId=(\d+)", url)
            info["platform"] = "1688"
            info["product_id"] = m.group(1) if m else ""

        return info

    def get_price_history_auto(self, url: str, days: int = 90) -> list[CompetitorPricePoint]:
        """
        自动识别平台并抓取历史价格。

        推荐入口，只提供一个 URL，剩下的自动处理。
        """
        parsed = self.parse_product_url(url)
        platform = parsed["platform"]
        product_id = parsed["product_id"]

        if not product_id:
            print(f"[WebScrapingDataSource] Could not parse product ID from: {url}")
            return []

        fetchers = {
            "jd": lambda: self.get_price_history_jd(product_id, days),
            "taobao": lambda: self.get_price_history_taobao(product_id, "taobao"),
            "tmall": lambda: self.get_price_history_taobao(product_id, "tmall"),
            "1688": lambda: self.get_price_history_1688(product_id, days),
        }

        fetcher = fetchers.get(platform)
        if fetcher:
            print(f"[WebScrapingDataSource] Fetching {platform} product {product_id} ...")
            return fetcher()

        # 兜底：尝试慢慢买
        print(f"[WebScrapingDataSource] Trying manmanmai fallback for: {url}")
        return self.get_price_history_manmanmai(url, days)
