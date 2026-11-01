#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 蜗牛出品

import sys
import re
import json
import base64
import html
import os
from urllib.parse import quote, unquote, urljoin

try:
    from base.spider import Spider as BaseSpider
except ImportError:
    class BaseSpider:
        pass

try:
    import requests
    import urllib3
    urllib3.disable_warnings()
except ImportError:
    requests = None


class Spider(BaseSpider):

    AD_KEYWORDS = [
        'popads', 'exoclick', 'juancdn', '1xbet', 'bet365', 'casino',
        'propellerads', 'trafficjunky', 'popunder', 'adsterra', 'doubleclick',
        'yandex', 'google-analytics', 'landing', 'promo', 'banner', 'adserver',
        'syndication', 'playhub', 'playhubconnect', 'juicyads', 'huanzi',
        'alternative', '-alt.mp4', '/alt.', 'adtago', 'clksite', 'ad-delivery',
        'clammyendearedkeg', 'winksullenwaistcoat', 'javdoe.sh', 'p3adult',
        'vast', 'ima3', 'googlesyndication', 'javtop.fun/trailers',
        'streaming1.javtop', 'streaming2.javtop', 'streaming3.javtop',
        'streaming4.javtop', 'streaming5.javtop', '/bn/alternative/',
        'popads.net', 'exoclick.com', 'trafficjunky.net'
    ]

    PREVIEW_KEYWORDS = [
        'trailer', 'trailers', 'freepv', 'preview', 'sample',
        'litevideo', 'convert.mp4', 'short', 'promo', 'teaser', '试看',
        '/pv/', 'mmb_convert', '_preview', 'sample.mp4'
    ]

    TRUSTED_EMBED_HOSTS = [
        'mycloudz.cc', 'cloudwish.xyz', 'turbovid.vip', 'turboviplay.com',
        'streamhg.com', 'streambeast', 'f4scdn.com', 'lulust.com',
        'streamtape', 'dooood.com', 'dood'
    ]

    EMBED_HOSTS = TRUSTED_EMBED_HOSTS + [
        'filelions', 'vidhide', 'mixdrop', 'javhdz.today', 'savedvids.com',
        'streamtape.net', 'upn.one'
    ]

    FIXED_CLASSES = [
        {'type_id': 'chinese-subtitle', 'type_name': '中文字幕'},
        {'type_id': 'uncensored-jav', 'type_name': '无码'},
        {'type_id': 'reducing-mosaic', 'type_name': '无码破解'},
        {'type_id': 'amateur', 'type_name': '素人自拍'},
        {'type_id': 'jav-sub', 'type_name': '日文字幕'},
        {'type_id': 'creampie', 'type_name': '中出'},
        {'type_id': 'big-tits', 'type_name': '巨乳'},
        {'type_id': 'beautiful-girl', 'type_name': '美少女'},
        {'type_id': 'recent', 'type_name': '最新更新'},
        {'type_id': 'releaseday', 'type_name': '发行日期'},
    ]

    def __init__(self):
        super().__init__()
        self.host = 'https://javhd.name'
        self.DOMAIN_CANDIDATES = [
            'https://javhd.name',
            'https://javhd.net',
            'https://javhd.org',
            'https://javhd.today'
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.host + '/'
        }
        self.session = requests.Session() if requests else None
        if self.session:
            self.session.headers.update(self.headers)
            self.session.verify = False
        self.cache = {}

    def getName(self):
        return "JAVHD_Spider_v26_FixPlay"

    def isVideoFormat(self, url):
        if not url or self._is_bad_media(url):
            return False
        return bool(re.search(r'\.(m3u8|mp4)(\?|$)', str(url), re.I))

    def manualVideoCheck(self):
        return False

    def init(self, extend=""):
        try:
            self._discover_domain()
        except Exception:
            pass

    def _is_ad(self, url_or_str):
        if not url_or_str:
            return True
        check_str = str(url_or_str).lower()
        if any(kw in check_str for kw in self.AD_KEYWORDS):
            return True
        if re.search(r'(-alt\.mp4|/alternative/|playhubconnect|/bn/alt)', check_str):
            return True
        return False

    def _is_preview(self, url_or_str):
        if not url_or_str:
            return False
        check_str = str(url_or_str).lower()
        if any(kw in check_str for kw in self.PREVIEW_KEYWORDS):
            return True
        if re.search(r'(trailers?/|/pv/|convert\.mp4|sample\.mp4)', check_str):
            return True
        return False

    def _is_bad_media(self, url):
        return self._is_ad(url) or self._is_preview(url)

    def _is_embed_host(self, url):
        if not url:
            return False
        u = str(url).lower()
        return any(h in u for h in self.EMBED_HOSTS)

    def _is_trusted_embed(self, url):
        if not url:
            return False
        u = str(url).lower()
        return any(h in u for h in self.TRUSTED_EMBED_HOSTS)

    def _discover_domain(self):
        if not self.session:
            return
        for domain in self.DOMAIN_CANDIDATES:
            try:
                r = self.session.get(domain, timeout=4, allow_redirects=True)
                if r.status_code == 200 and len(r.text) > 300:
                    self.host = domain.rstrip('/')
                    self.headers['Referer'] = self.host + '/'
                    self.session.headers.update({'Referer': self.host + '/'})
                    break
            except Exception:
                continue

    def _get(self, url, retry=2, referer=''):
        if not self.session:
            return ""
        headers = self.headers.copy()
        if referer:
            headers['Referer'] = referer
        for i in range(retry + 1):
            try:
                r = self.session.get(url, headers=headers, timeout=10, allow_redirects=True)
                if r.status_code == 200:
                    if self._is_ad(r.url) and not self._is_embed_host(r.url):
                        return ""
                    r.encoding = 'utf-8'
                    return r.text
            except Exception:
                if i == retry:
                    return ""
        return ""

    def _get_ajax(self, url):
        """分类页 AJAX：GET ?ajax=1 → {html, pagination, total}"""
        if not self.session:
            return None
        headers = self.headers.copy()
        headers.update({
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': url.split('?')[0]
        })
        try:
            r = self.session.get(url, headers=headers, timeout=10, allow_redirects=True)
            if r.status_code != 200:
                return None
            text = r.text.strip()
            if not text.startswith('{'):
                return None
            data = json.loads(text)
            if isinstance(data, dict) and 'html' in data:
                return data
        except Exception:
            pass
        return None

    def homeContent(self, filter):
        return {'class': self.FIXED_CLASSES}

    def homeVideoContent(self):
        return self.categoryContent("chinese-subtitle", "1", False, {})

    def categoryContent(self, tid, pg, filter, extend):
        pg = str(pg) if pg else "1"
        videos = []
        total = 0
        page_count = 50

        # 分类由前端 fetch('?ajax=1') 加载
        # 第1页: /{tid}/?ajax=1
        # 第N页: /{tid}/recent/{pg}/?ajax=1
        if pg == "1":
            ajax_urls = [
                f"{self.host}/{tid}/?ajax=1",
                f"{self.host}/{tid}/recent/?ajax=1",
            ]
        else:
            ajax_urls = [
                f"{self.host}/{tid}/recent/{pg}/?ajax=1",
                f"{self.host}/{tid}/{pg}/?ajax=1",
            ]

        for u in ajax_urls:
            data = self._get_ajax(u)
            if not data or not data.get('html'):
                continue
            videos = self._extract_videos(data['html'])
            total = int(data.get('total') or 0)
            page_count = self._extract_pagecount(data.get('pagination') or '') or page_count
            if total > 0 and videos:
                per_page = max(len(videos), 28)
                page_count = max(page_count, (total + per_page - 1) // per_page)
            if videos:
                break

        if not videos:
            if pg == "1":
                fallback = [f"{self.host}/{tid}/", f"{self.host}/recent/", f"{self.host}/"]
            else:
                fallback = [
                    f"{self.host}/{tid}/recent/{pg}/",
                    f"{self.host}/recent/{pg}/",
                ]
            for u in fallback:
                html_str = self._get(u)
                if html_str and len(html_str) > 500:
                    videos = self._extract_videos(html_str)
                    page_count = self._extract_pagecount(html_str) or page_count
                    if videos:
                        break

        if total <= 0:
            total = page_count * max(len(videos), 28)

        return {
            'list': videos,
            'page': int(pg),
            'pagecount': page_count,
            'limit': len(videos),
            'total': total
        }

    def _extract_videos(self, html_str):
        videos = []
        if not html_str:
            return videos

        html_str = html_str.replace('\\/', '/')

        seen = set()
        blocks = re.findall(
            r'<li\s+id=["\']video-(\d+)["\'][^>]*>(.*?)</li>',
            html_str, re.S | re.I
        )

        for vid, block in blocks:
            href_m = re.search(r'<a\s+[^>]*href=["\']([^"\']+)["\']', block, re.I)
            if not href_m:
                continue
            v_url = self._fix_url(href_m.group(1))
            if not v_url or v_url in seen or self._is_ad(v_url):
                continue
            if not re.search(r'/\d+/', v_url):
                continue

            title = ""
            title_m = re.search(r'class=["\']video-title["\'][^>]*>(.*?)</span>', block, re.S | re.I)
            if title_m:
                title = self._clean_title(title_m.group(1))
            if not title:
                title_m = re.search(r'title=["\']([^"\']+)["\']', block, re.I)
                title = self._clean_title(title_m.group(1)) if title_m else ""
            if not title or len(title) < 2:
                continue

            pic = self._extract_pic(block)
            if not pic:
                continue

            remarks = ""
            rem_m = re.search(r'class=["\']video-overlay[^"\']*["\'][^>]*>(.*?)</span>', block, re.S | re.I)
            if rem_m:
                remarks = self._clean_title(rem_m.group(1))

            seen.add(v_url)
            videos.append({
                'vod_id': v_url,
                'vod_name': title,
                'vod_pic': pic,
                'vod_remarks': remarks
            })

        return videos

    def _extract_pagecount(self, html_str):
        if not html_str:
            return 50
        found = re.findall(r'/(\d+)/["\']?', html_str)
        nums = [int(x) for x in found if str(x).isdigit() and int(x) > 1]
        return max(nums) if nums else 50

    def _extract_pic(self, content_str):
        img_m = re.search(r'<img[^>]+>', content_str, re.I)
        if img_m:
            img_tag = img_m.group(0)
            for attr in ['data-src', 'data-original', 'srcset', 'src']:
                pm = re.search(fr'{attr}=["\']([^"\']+)["\']', img_tag, re.I)
                if pm:
                    raw_pic = pm.group(1).split(',')[0].split(' ')[0].strip()
                    if raw_pic and not any(x in raw_pic.lower() for x in ['logo', 'avatar', 'placeholder', 'blank', 'data:image']):
                        return self._fix_url(raw_pic)
        return ""

    def _extract_description(self, html_str):
        """从详情页提取影片描述（简介）"""
        if not html_str:
            return ""
        # 1. 尝试 meta description
        meta = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', html_str, re.I)
        if meta:
            desc = meta.group(1).strip()
            if desc and len(desc) > 10:
                return self._clean_title(desc)

        # 2. 尝试常见的描述容器（class/content/itemprop）
        patterns = [
            r'<div\s+class=["\']description["\'][^>]*>(.*?)</div>',
            r'<div\s+class=["\']content["\'][^>]*>(.*?)</div>',
            r'<div\s+itemprop=["\']description["\'][^>]*>(.*?)</div>',
            r'<p\s+class=["\']description["\'][^>]*>(.*?)</p>',
            r'<div\s+class=["\']entry-content["\'][^>]*>(.*?)</div>',  # WordPress 常见
            r'<div\s+class=["\']post-content["\'][^>]*>(.*?)</div>',
        ]
        for pat in patterns:
            m = re.search(pat, html_str, re.S | re.I)
            if m:
                desc = self._clean_title(m.group(1))
                if desc and len(desc) > 10:
                    return desc

        # 3. 尝试查找较长的段落（可能包含剧情）
        # 但为避免误抓广告，我们只取包含特定关键词的段落
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html_str, re.S | re.I)
        for p in paragraphs:
            text = self._clean_title(p)
            if len(text) > 50 and any(kw in text.lower() for kw in ['剧情', '故事', '简介', '演员', '导演', '片商', '番号']):
                return text

        # 4. 如果没有，返回空字符串
        return ""

    def detailContent(self, ids):
        v_url = ids[0] if isinstance(ids, list) else ids
        if v_url in self.cache:
            return {'list': [self.cache[v_url]]}

        html_str = self._get(v_url)
        if not html_str:
            return {'list': []}

        tm = re.search(r'<h1[^>]*>(.*?)</h1>', html_str, re.S | re.I)
        title = self._clean_title(tm.group(1)) if tm else ''
        if not title:
            tm = re.search(r'<title>(.*?)</title>', html_str, re.S | re.I)
            title = self._clean_title(tm.group(1).split('|')[0] if tm else 'Video')

        pic = self._extract_pic(html_str)

        # 提取描述
        description = self._extract_description(html_str)
        if not description:
            description = title  # 备用：没有描述时使用标题

        vid_m = re.search(r'/(\d+)/', v_url)
        vid = vid_m.group(1) if vid_m else ''

        # 优先从详情页直接提取 data-embeds / data-embed
        routes = self._extract_embed_routes(html_str)

        # 兜底：再请求 /embed/{vid}/
        if not routes and vid:
            embed_url = f"{self.host}/embed/{vid}/"
            embed_html = self._get(embed_url, referer=v_url)
            routes = self._extract_embed_routes(embed_html)

        if not routes and vid:
            routes.append(('默认线路', f"{self.host}/embed/{vid}/"))

        play_from = '$$$'.join([r[0] for r in routes])
        play_url = '$$$'.join([f"正片${r[1]}" for r in routes])

        vod_detail = {
            'vod_id': v_url,
            'vod_name': title,
            'vod_pic': pic,
            'vod_play_from': play_from,
            'vod_play_url': play_url,
            'vod_content': description
        }
        self.cache[v_url] = vod_detail
        return {'list': [vod_detail]}

    def _extract_embed_routes(self, html_str):
        """从详情页/embed页提取播放线路。
        新结构：data-embeds="base64(JSON数组)" + 多个 data-embed="base64(url)"
        旧结构：playEmbed(atob(...)) / atob(...)
        """
        routes = []
        if not html_str:
            return routes

        host_name_map = {
            'mycloudz': 'ML',
            'cloudwish': 'CL',
            'turbovid': 'Turbovid',
            'turboviplay': 'Turbovid',
            'streambeast': 'StreamBeast',
            'streamhg': 'StreamHG',
            'dood': 'Dood',
            'dooood': 'Dood',
            'streamtape': 'Streamtape',
            'f4scdn': 'F4S',
            'lulust': 'Lulu',
            'javhdz': 'JAVHDZ',
            'savedvids': 'SavedVids',
            'upn.one': 'StreamBeast',
        }

        seen = set()
        trusted = []
        others = []

        def _add(url):
            if not url or not url.startswith('http'):
                return
            url = url.strip()
            if url in seen or self._is_bad_media(url):
                return
            # 跳过 embed_server* 变体，只保留主 embed.php
            low = url.lower()
            if 'embed_server' in low:
                return
            seen.add(url)
            name = '线路'
            for key, label in host_name_map.items():
                if key in low:
                    name = label
                    break
            if self._is_trusted_embed(url):
                trusted.append((name, url))
            else:
                others.append((name, url))

        # 1) data-embeds = base64(JSON list of urls)
        for m in re.finditer(r'data-embeds=["\']([A-Za-z0-9+/=]+)["\']', html_str, re.I):
            try:
                raw = base64.b64decode(m.group(1)).decode('utf-8', errors='ignore')
                data = json.loads(raw)
                if isinstance(data, list):
                    for u in data:
                        _add(str(u))
            except Exception:
                continue

        # 2) data-embed = base64(single url)
        for m in re.finditer(r'data-embed=["\']([A-Za-z0-9+/=]+)["\']', html_str, re.I):
            try:
                decoded = base64.b64decode(m.group(1)).decode('utf-8', errors='ignore').strip()
                _add(decoded)
            except Exception:
                continue

        # 3) 旧 playEmbed(atob(...)) / atob(...)
        b64_list = re.findall(
            r"playEmbed\s*\(\s*atob\s*\(\s*['\"]([A-Za-z0-9+/=]+)['\"]\s*\)\s*\)",
            html_str, re.I
        )
        b64_list += re.findall(r"atob\s*\(\s*['\"]([A-Za-z0-9+/=]+)['\"]\s*\)", html_str, re.I)
        for b64 in b64_list:
            try:
                decoded = base64.b64decode(b64).decode('utf-8', errors='ignore').strip()
                _add(decoded)
            except Exception:
                continue

        # 同类 hard host 最多保留 3 条，避免线路爆炸
        hard_limit = {'JAVHDZ': 0, 'SavedVids': 0}
        filtered = []
        for name, url in trusted + others:
            if name in hard_limit:
                if hard_limit[name] >= 3:
                    continue
                hard_limit[name] += 1
            filtered.append((name, url))

        final = []
        used_names = {}
        for name, url in filtered:
            if name in used_names:
                used_names[name] += 1
                name = f"{name}-{used_names[name]}"
            else:
                used_names[name] = 1
            final.append((name, url))
        return final

    def playerContent(self, flag, id, vipFlags=None):
        play_url = id
        headers = {
            'User-Agent': self.headers['User-Agent'],
            'Referer': self.host + '/'
        }

        if self._is_bad_media(play_url):
            return {"parse": 0, "url": "", "header": headers}

        if self.isVideoFormat(play_url):
            return {"parse": 0, "url": play_url, "header": headers}

        # javhdz / savedvids 常 403，优先交给客户端嗅探
        low = play_url.lower()
        if any(h in low for h in ('javhdz.today', 'savedvids.com')):
            return {
                "parse": 1,
                "url": play_url,
                "header": {
                    'User-Agent': self.headers['User-Agent'],
                    'Referer': self.host + '/'
                }
            }

        if play_url.startswith('http'):
            real = self._resolve_real_media(play_url)
            if real and not self._is_bad_media(real):
                return {
                    "parse": 0,
                    "url": real,
                    "header": {
                        'User-Agent': self.headers['User-Agent'],
                        'Referer': play_url
                    }
                }

        if iframe_html := self._get(play_url, referer=self.host + '/'):
            routes = self._extract_embed_routes(iframe_html)
            for _name, route_url in routes:
                if self._is_bad_media(route_url):
                    continue
                # 子线路若是 hard host，直接 parse=1
                rlow = route_url.lower()
                if any(h in rlow for h in ('javhdz.today', 'savedvids.com')):
                    return {
                        "parse": 1,
                        "url": route_url,
                        "header": {
                            'User-Agent': self.headers['User-Agent'],
                            'Referer': self.host + '/'
                        }
                    }
                real = self._resolve_real_media(route_url)
                if real and not self._is_bad_media(real):
                    return {
                        "parse": 0,
                        "url": real,
                        "header": {
                            'User-Agent': self.headers['User-Agent'],
                            'Referer': route_url
                        }
                    }
            real_media = self._deep_extract_media(iframe_html)
            if real_media and not self._is_bad_media(real_media):
                return {
                    "parse": 0,
                    "url": real_media,
                    "header": {
                        'User-Agent': self.headers['User-Agent'],
                        'Referer': play_url
                    }
                }

        # 最后兜底：交给客户端解析
        if play_url.startswith('http'):
            return {
                "parse": 1,
                "url": play_url,
                "header": headers
            }
        return {"parse": 0, "url": "", "header": headers}

    def _resolve_real_media(self, embed_url):
        if not embed_url or self._is_bad_media(embed_url):
            return ""

        html_str = self._get(embed_url, referer=self.host + '/')
        if not html_str:
            return ""

        real = self._unpack_and_find_m3u8(html_str)
        if real and not self._is_bad_media(real):
            return real

        real = self._deep_extract_media(html_str)
        if real and not self._is_bad_media(real):
            return real

        return ""

    def _unpack_and_find_m3u8(self, text):
        if not text or 'eval(function(p,a,c,k,e,d)' not in text:
            return ""

        m = re.search(
            r"eval\(function\(p,a,c,k,e,d\)\{while\(c--\)if\(k\[c\]\)p=p\.replace\(new RegExp\('\\\\b'\+c\.toString\(a\)\+'\\\\b','g'\),k\[c\]\);return p\}"
            r"\('((?:\\.|[^'\\])*)',(\d+),(\d+),'((?:\\.|[^'\\])*)'\.split\('\|'\)\)\)",
            text, re.S
        )
        if not m:
            m = re.search(
                r"eval\(function\(p,a,c,k,e,d\)\{.*?\}"
                r"\('((?:\\.|[^'\\])*)',(\d+),(\d+),'((?:\\.|[^'\\])*)'\.split\('\|'\)\)\)",
                text, re.S
            )
        if not m:
            return ""

        try:
            p = m.group(1)
            a = int(m.group(2))
            c = int(m.group(3))
            k = m.group(4).split('|')
            decoded = self._packer_unpack(p, a, c, k)
        except Exception:
            return ""

        candidates = []
        for mm in re.finditer(r'"(hls\d?)"\s*:\s*"(https?://[^"]+)"', decoded, re.I):
            candidates.append(mm.group(2))
        for u in re.findall(r'https?://[^\s"\'<>\\]+', decoded):
            if re.search(r'\.(m3u8|mp4|txt)(\?|$)', u, re.I) or 'urlset' in u or 'master' in u:
                candidates.append(u)

        for u in candidates:
            u = u.replace('\\/', '/')
            if self._is_bad_media(u):
                continue
            if '.m3u8' in u.lower():
                return u
        for u in candidates:
            u = u.replace('\\/', '/')
            if not self._is_bad_media(u) and re.search(r'\.(m3u8|mp4)(\?|$)', u, re.I):
                return u
        return ""

    def _packer_unpack(self, p, a, c, k):
        def to_base(n, base):
            if n == 0:
                return '0'
            digits = '0123456789abcdefghijklmnopqrstuvwxyz'
            s = ''
            while n:
                s = digits[n % base] + s
                n //= base
            return s

        while c > 0:
            c -= 1
            if c < len(k) and k[c]:
                p = re.sub(r'\b' + re.escape(to_base(c, a)) + r'\b', k[c], p)
        return p

    def _deep_extract_media(self, text):
        if not text:
            return ""

        real = self._unpack_and_find_m3u8(text)
        if real and not self._is_bad_media(real):
            return real

        direct = self._find_m3u8(text)
        if direct:
            return direct

        b64_matches = re.findall(r'aHR0cD[a-zA-Z0-9+/=]{20,}', text)
        for b64 in b64_matches:
            try:
                decoded = base64.b64decode(b64).decode('utf-8', errors='ignore')
                if re.search(r'\.(m3u8|mp4)', decoded, re.I) and not self._is_bad_media(decoded):
                    return decoded
            except Exception:
                continue

        file_match = re.search(
            r'(?:file|src|source)\s*[:=]\s*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']',
            text, re.I
        )
        if file_match:
            cand = file_match.group(1).replace('\\/', '/')
            if not self._is_bad_media(cand):
                return cand

        return ""

    def _find_m3u8(self, text):
        if not text:
            return ""
        matches = re.findall(
            r'(https?://[^\s"\'<>]+\.(?:m3u8|mp4)[^\s"\'<>]*)',
            text, re.I
        )
        for m in matches:
            clean_m = m.replace('\\/', '/')
            if not self._is_bad_media(clean_m):
                return clean_m
        return ""

    def searchContent(self, key, quick, pg="1"):
        pg = str(pg) if pg else "1"
        videos = []
        total = 0
        page_count = 10

        if pg == "1":
            urls = [
                f"{self.host}/?s={quote(key)}&ajax=1",
                f"{self.host}/?s={quote(key)}",
            ]
        else:
            urls = [
                f"{self.host}/page/{pg}/?s={quote(key)}&ajax=1",
                f"{self.host}/page/{pg}/?s={quote(key)}",
            ]

        for u in urls:
            if 'ajax=1' in u:
                data = self._get_ajax(u)
                if data and data.get('html'):
                    videos = self._extract_videos(data['html'])
                    total = int(data.get('total') or 0)
                    page_count = self._extract_pagecount(data.get('pagination') or '') or page_count
                    if videos:
                        break
            else:
                html_str = self._get(u)
                videos = self._extract_videos(html_str)
                page_count = self._extract_pagecount(html_str) or page_count
                if videos:
                    break

        return {
            'list': videos,
            'page': int(pg),
            'pagecount': page_count,
            'total': total or page_count * max(len(videos), 20)
        }

    def _clean_title(self, raw):
        if not raw:
            return ''
        text = re.sub(r'<[^>]+>', '', raw)
        text = html.unescape(text)
        return re.sub(r'\s+', ' ', text).strip()

    def _fix_url(self, url, base_url=''):
        if not url:
            return ''
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            return self.host + url
        if not url.startswith('http'):
            return urljoin(base_url or self.host, url)
        return url