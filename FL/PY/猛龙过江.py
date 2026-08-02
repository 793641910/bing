# -*- coding: utf-8 -*-

import sys, re, json, uuid, base64, urllib.request, urllib.parse, urllib.error, ssl, datetime
from base.spider import Spider

HOST = "https://hfdxwttfeq3.com:520"
API_BASE = HOST + "/jbapi"

# 手动 token（留空则自动获取）
TOKEN = ""

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; M2102J2SC Build/TKQ1.221114.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.7499.3 Mobile Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": HOST + "/ui_ojbk/h5/",
    "Origin": HOST,
    "X-Requested-With": "XMLHttpRequest",
}

CATE_MAP = {
    "10041": "推荐",
    "10105": "最热",
    "10103": "新主播",
    "10042": "中国",
    "10106": "日本",
    "10102": "乌克兰",
}

_CATE_BY_NAME = {}
for _k, _v in CATE_MAP.items():
    _CATE_BY_NAME[_k] = _k
    _CATE_BY_NAME[_v] = _k
_CATE_BY_NAME.update({
    "recommend": "10041",
    "hot": "10105",
    "new": "10103",
    "cn": "10042",
    "jp": "10106",
    "ua": "10102",
})


def _ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _decode_token_data(raw):

    if not raw:
        return None
    try:
        raw = raw.strip()
        pad = (-len(raw) % 4)
        if pad:
            raw += "=" * pad
        step1 = base64.b64decode(raw).decode("utf-8", errors="ignore")
        step2 = step1[::-1]
        pad2 = (-len(step2) % 4)
        if pad2:
            step2 += "=" * pad2
        step3 = base64.b64decode(step2).decode("utf-8", errors="ignore")
        return json.loads(step3)
    except Exception as e:
        print("[ojbk] decode token error:", e)
        return None


def _resolve_cid(cid):
    if not cid:
        return "10041"
    cid = str(cid).strip()
    if cid in CATE_MAP:
        return cid
    if cid in _CATE_BY_NAME:
        return _CATE_BY_NAME[cid]
    if re.match(r"^\d+$", cid):
        return cid
    return "10041"

class Spider(Spider):

    def getName(self):
        return "OJBK"

    def init(self, extend=""):
        super().init(extend)
        self._token = TOKEN.strip()
        self._client_id = ""
        self._ctx = _ssl_ctx()
        if not self._token:
            self._ensure_token()

    def destroy(self):
        self._token = ""

    def isVideoFormat(self, url):
        return True

    def manualVideoCheck(self):
        pass

    def _fetch(self, url, headers=None):
        h = dict(HEADERS)
        if self._token:
            h["token"] = self._token
        if headers:
            h.update(headers)
        last_err = None
        for i in range(3):
            try:
                req = urllib.request.Request(url, headers=h, method="GET")
                with urllib.request.urlopen(req, timeout=15, context=self._ctx) as resp:
                    return resp.read().decode("utf-8", errors="ignore")
            except Exception as e:
                last_err = e
        print("[ojbk] request error (%s): %s" % (url[:80], last_err))
        return None

    def _fetch_json(self, url, headers=None):
        text = self._fetch(url, headers)
        if not text:
            return None
        try:
            return json.loads(text)
        except Exception as e:
            print("[ojbk] json parse error:", e)
            return None

    def _ensure_token(self):
        if self._token:
            return True
        if not self._client_id:
            self._client_id = "%s-%s" % (
                datetime.datetime.now().strftime("%Y%m%d"),
                str(uuid.uuid4()),
            )
        url = "%s/user/autoUser/null/%s/null" % (API_BASE, urllib.parse.quote(self._client_id))
        res = self._fetch_json(url, headers={"token": ""})
        if not res:
            return False
        if res.get("code") != 200:
            print("[ojbk] autoUser failed:", res.get("msg"))
            return False
        decoded = _decode_token_data(res.get("data", ""))
        if not decoded:
            return False
        self._token = decoded.get("token", "")
        uid = decoded.get("dataUser", {}).get("id") if isinstance(decoded, dict) else ""
        print("[ojbk] token acquired, uid=%s" % uid)
        return bool(self._token)

    def _api(self, path):
        if not self._ensure_token():
            return None
        url = API_BASE + path
        res = self._fetch_json(url)
        if res and res.get("code") == 302:
            print("[ojbk] token expired, refreshing...")
            self._token = ""
            if self._ensure_token():
                res = self._fetch_json(url)
        return res

    def _fmt_vod(self, item):
        vid = str(item.get("id", ""))
        name = item.get("username") or item.get("name") or "直播间"
        pic = item.get("snapshot") or item.get("pic") or ""
        viewers = item.get("viewersCount") or item.get("viewers") or 0
        stream = item.get("stream") or ""
        vod_id = "@@".join([vid, stream, name.replace("@@", "_")])
        return {
            "vod_id": vod_id,
            "vod_name": name,
            "vod_pic": pic,
            "vod_remarks": "👁 %s" % viewers,
            "vod_content": "",
        }

    def _list_from_res(self, res):
        if not res or res.get("code") != 200:
            return []
        data = res.get("data") or {}
        if isinstance(data, dict):
            return data.get("list", [])
        if isinstance(data, list):
            return data
        return []

    def homeContent(self, filter):
        classes = [{"type_id": k, "type_name": v} for k, v in CATE_MAP.items()]
        home_list = self.homeVideoContent().get("list", [])
        return {"class": classes, "list": home_list}

    def homeVideoContent(self):
        res = self._api("/local_live/fldata/10041/1/20")
        return {"list": [self._fmt_vod(it) for it in self._list_from_res(res)]}

    def categoryContent(self, cid, pg, filter, ext):
        try:
            pg = int(pg)
        except Exception:
            pg = 1
        cid = _resolve_cid(cid)

        path = "/local_live/fldata/%s/%d/20" % (cid, pg)
        res = self._api(path)
        items = [self._fmt_vod(it) for it in self._list_from_res(res)]

        if not items and pg == 1:
            path2 = "/local_live/fldata/%s/2/20" % cid
            res2 = self._api(path2)
            items = [self._fmt_vod(it) for it in self._list_from_res(res2)]

        return {
            "list": items,
            "page": pg,
            "pagecount": 999,
            "limit": 20,
            "total": 9999,
        }

    def detailContent(self, ids):
        did = ids[0] if isinstance(ids, list) else ids
        parts = did.split("@@")
        if len(parts) < 2:
            return {"list": []}
        vid, stream = parts[0], parts[1]
        name = parts[2] if len(parts) > 2 else ""
        vod = {
            "vod_id": did,
            "vod_name": name,
            "vod_pic": "",
            "type_name": "直播",
            "vod_content": "",
            "vod_play_from": "直播源",
            "vod_play_url": "%s$%s" % (name, stream) if stream else "",
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        return {
            "parse": 0,
            "playUrl": "",
            "url": id,
            "header": HEADERS,
        }

    def searchContent(self, key, quick):
        return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

    def localProxy(self, params):
        return None