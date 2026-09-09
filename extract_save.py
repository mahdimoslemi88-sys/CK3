# -*- coding: utf-8 -*-
"""
extract_save.py — ابزار جامع و اصلاح‌شده دیوان برای استخراج وضعیت بازی Crusader Kings 3.
نسخه کاملاً اصلاح‌شده: شمارش دقیق و بدون خطای ولایات مستقیم (فقط شهرستان‌های c_...).

مرحلهٔ ۱ از بازطراحی استخراج سیو:
- Parser ساختاری و مستقل (بدون Regex سراسری برای کل سیو)
- API داخلی روشن (root/child/scalar/list/object-list)
- ایمن‌سازی ورودی فایل (path traversal، پسوند، symlink)
- فیلتر autosave_exit در انتخاب خودکار سیو
"""

import os
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
RAKALY = os.path.join(APP_DIR, "tools", "rakaly.exe")
REPORTS_DIR = os.path.join(APP_DIR, "reports")
SAVE_DIR = os.path.expanduser(
    "~/Documents/Paradox Interactive/Crusader Kings III/save games"
)

TIER_FA = {0: "بارون", 1: "کنت (والی)", 2: "دوک (امیر)", 3: "پادشاه (سلطان)", 4: "امپراتور (شاهنشاه)"}

TITLE_TRANSLATIONS = {
    "d_soghd": "دوک‌نشین سغد",
    "c_bukhara": "بخارا",
    "c_firabr": "فرابر",
    "c_samarkand": "سمرقند",
    "c_nakhshab": "نخشب",
    "c_khojand": "خجند",
    "c_dabusiya": "دابوسیه",
    "c_ferghana": "فرغانه",
    "c_isfara": "اسفره",
    "c_nasaiya": "نسف",
    "c_nasrabad": "نصرآباد",
    "c_uzgend": "اوزگند",
    "c_uzgend_KARA": "اوزگند",
    "c_balkh": "بلخ",
    "c_khiva": "خیوه",
    "c_kath": "کاث",
    "c_urgend": "گرگانج",
    "c_taraz": "طراز",
    "c_otrar": "اترار",
    "c_farab": "فاراب",
    "c_chach": "چاچ (تاشکند)",
    "c_merv": "مرو",
    "c_amul": "آمل",
    "c_gurgan": "گرگان",
    "b_bukhara": "قلعه بخارا",
    "b_samarkand": "قلعه سمرقند",
    "b_khojand": "قلعه خجند",
    "b_nakhshab": "قلعه نخشب",
    "b_dabusiya": "قلعه دابوسیه",
    "b_paykend": "شهر پیکند"
}

BUILDING_TRANSLATIONS = {
    "cereal_fields": "مزارع غلات 🌾",
    "pastoral_lands": "چراگاه‌ها 🐄",
    "farms_and_fields": "مزارع و باغات 🌾",
    "hill_farms": "مزارع تپه‌ای 🌾",
    "quarries": "معادن سنگ ⛏️",
    "guild_halls": "تالار اصناف و بازار 🏛️",
    "monastic_schools": "مدارس دینی و مذهبی 📚",
    "hunting_grounds": "شکارگاه‌ها 🏹",
    "barracks": "پادگان پیاده‌نظام 🛡️",
    "camps": "اردوگاه نظامی ⛺",
    "stables": "اصطبل‌ها 🐎",
    "blacksmiths": "آهنگری ⚒️",
    "city": "مرکز شهر 🏙️",
    "temple": "مسجد/معبد 🕌",
    "castle": "استحکامات قلعه 🏰",
    "hill_forts": "قلعه‌های تپه‌ای 🏰",
    "walls_and_towers": "دیوار و برج‌ها 🧱",
    "watchtowers": "برج دیده‌بانی 👁️"
}


def _fix_persian(s: str) -> str:
    if not s or not re.search(r"[\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFF]", s):
        return s
    tokens = s.split()
    fixed = ["".join(reversed(t)) for t in tokens]
    return " ".join(reversed(fixed))


# ============================================================
# Parser ساختاری (مرحلهٔ ۱) — مستقل از indentation، حفظ ترتیب
# ============================================================

_TRUE = {"yes": True, "no": False}


class Node:
    """یک گره از درخت سیو: scalar، list ساده، یا block با childهای نام‌دار.

    - scalar: مقدار رشته/عدد/yes-no
    - list: list ساده یا object-list (هر عضو یک Node)
    - block: dict نام→Node (اولین تکرار هر نام نگه داشته می‌شود؛
      تکرارها در same_name برای blockهای تکرارشونده با شناسه حفظ می‌شوند)
    """

    __slots__ = ("kind", "value", "children", "same_name")

    def __init__(self, kind: str):
        self.kind = kind          # "scalar" | "list" | "block"
        self.value = None         # برای scalar
        self.children = None      # برای list: [Node]، برای block: dict[str, Node]
        self.same_name = None     # برای block: [Node] تکرارهای هم‌نام (خودش اولین است)

    # ---- scalar ----
    def as_str(self):
        return self.value if self.kind == "scalar" else None

    def as_int(self):
        if self.kind != "scalar" or self.value is None:
            return None
        try:
            return int(str(self.value))
        except ValueError:
            return None

    def as_float(self):
        if self.kind != "scalar" or self.value is None:
            return None
        try:
            return float(str(self.value))
        except ValueError:
            return None

    def as_bool(self):
        if self.kind != "scalar":
            return None
        if isinstance(self.value, bool):
            return self.value
        return _TRUE.get(str(self.value).lower()) if self.value is not None else None

    # ---- ساختار ----
    def get(self, name: str):
        """اولین child با این نام، یا None (نبودن فیلد قابل تشخیص است)."""
        if self.kind != "block" or not self.children:
            return None
        return self.children.get(name)

    def get_all(self, name: str):
        """همهٔ childهای هم‌نام (blockهای تکرارشونده با شناسه)."""
        if self.kind != "block" or not self.children:
            return []
        first = self.children.get(name)
        if first is None:
            return []
        extra = self.same_name.get(name, []) if self.same_name else []
        return [first] + list(extra)

    def items(self):
        if self.kind == "block" and self.children:
            return list(self.children.items())
        return []

    def as_list(self):
        """عضوهای list (ساده یا object-list)؛ برای scalar/block خالی."""
        if self.kind == "list" and self.children is not None:
            return list(self.children)
        return []

    def __repr__(self):  # دیباگ
        if self.kind == "scalar":
            return f"Node(scalar={self.value!r})"
        if self.kind == "list":
            return f"Node(list[{len(self.children or [])}])"
        return f"Node(block[{len(self.children or {})}])"


_ESCAPES = {'"': '"', "\\": "\\", "n": "\n", "t": "\t", "r": "\r"}


class SaveParser:
    """Parser تو‌در‌تو برای متن ذوب‌شدهٔ سیو (خروجی rakaly stringify).

    - braceهای تو‌در‌تو را با شمارنده می‌خواند (بدون Regex برای بدنهٔ block)
    - quote و escape را مدیریت می‌کند بدون خراب‌کردن مقدار
    - ترتیب داده‌ها و blockهای تکرارشونده با شناسه حفظ می‌شود
    """

    def __init__(self, text: str):
        self.text = text
        self.n = len(text)

    def parse(self) -> Node:
        root = Node("block")
        root.children = {}
        self._i = 0
        self._parse_block_body(root, top=True)
        return root

    # -- ابزارهای سطح پایین --
    def _skip_ws(self):
        t, n = self.text, self.n
        i = self._i
        while i < n:
            c = t[i]
            if c in " \t\r\n":
                i += 1
            elif c == "#":  # کامنت تا پایان خط
                while i < n and t[i] != "\n":
                    i += 1
            else:
                break
        self._i = i

    def _read_quoted(self) -> str:
        """مقدار داخل quote با مدیریت escape؛ موقعیت را بعد از quote می‌برد."""
        t, n = self.text, self.n
        i = self._i + 1  # رد کردن quote افتتاح
        out = []
        while i < n:
            c = t[i]
            if c == "\\" and i + 1 < n:
                nxt = t[i + 1]
                out.append(_ESCAPES.get(nxt, nxt))
                i += 2
                continue
            if c == '"':
                self._i = i + 1
                return "".join(out)
            out.append(c)
            i += 1
        self._i = i
        return "".join(out)  # quote بسته‌نشده: تا انتها

    def _read_bare(self) -> str:
        """توکن بدون quote (عدد، شناسه، yes/no، c_bukhara و ...)."""
        t, n = self.text, self.n
        i = self._i
        start = i
        while i < n and t[i] not in " \t\r\n={}":
            i += 1
        self._i = i
        return t[start:i]

    def _convert_scalar(self, raw: str):
        """رشتهٔ خام را به int/float/bool تبدیل می‌کند؛ در غیر این صورت رشته."""
        if raw == "":
            return raw
        try:
            return int(raw)
        except ValueError:
            pass
        try:
            return float(raw)
        except ValueError:
            pass
        low = raw.lower()
        if low in _TRUE:
            return _TRUE[low]
        return raw

    def _read_value(self) -> Node:
        """یک مقدار کامل می‌خواند: block، list، یا scalar."""
        self._skip_ws()
        t, n = self.text, self.n
        if self._i >= n:
            return Node("scalar")
        c = t[self._i]
        if c == "{":
            return self._read_brace_group()
        if c == '"':
            node = Node("scalar")
            node.value = self._read_quoted()
            return node
        raw = self._read_bare()
        node = Node("scalar")
        node.value = self._convert_scalar(raw)
        return node

    def _read_brace_group(self) -> Node:
        """{ ... } را می‌خواند و تشخیص می‌دهد block است یا list ساده/object-list."""
        self._skip_ws()
        t, n = self.text, self.n
        if self._i >= n or t[self._i] != "{":
            return Node("scalar")
        self._i += 1  # رد کردن {

        # پیش‌خوانی: آیا اولین توکنِ غیر-brace با = دنبال می‌شود؟ (block) یا نه (list)
        probe = self._i
        depth = 0
        is_block = False
        while probe < n:
            c = t[probe]
            if c == "{":
                depth += 1
            elif c == "}":
                if depth == 0:
                    break
                depth -= 1
            elif depth == 0 and c == "=":
                is_block = True
                break
            elif depth == 0 and c not in " \t\r\n":
                # توکن در سطح اول — ادامه بده تا = یا } دیده شود
                pass
            probe += 1

        if not is_block:
            node = Node("list")
            node.children = []
            while self._i < n:
                self._skip_ws()
                if self._i >= n:
                    break
                c = t[self._i]
                if c == "}":
                    self._i += 1
                    return node
                if c == "{":
                    node.children.append(self._read_brace_group())
                else:
                    node.children.append(self._read_value())
            return node

        # block نام‌دار
        node = Node("block")
        node.children = {}
        self._parse_block_body(node)
        return node

    def _parse_block_body(self, node: Node, top: bool = False):
        """بدنهٔ block را تا } (یا انتها در سطح بالا) می‌خواند."""
        t, n = self.text, self.n
        while self._i < n:
            self._skip_ws()
            if self._i >= n:
                return
            c = t[self._i]
            if c == "}":
                # بستن block؛ در سطح ریشه فقط رد کن و ادامه بده —
                # یک } سرگردان نباید بقیهٔ parse را بکشد
                self._i += 1
                if top:
                    continue
                return
            # مقدار بی‌نام در سطح فیلد (مثل دنبالهٔ color=rgb { 181 87 216 })
            if c == "{":
                group = self._read_brace_group()
                self._store(node, "__anon__", group)
                continue
            # نام فیلد
            if c == '"':
                name = self._read_quoted()
            else:
                name = self._read_bare()
            if name == "":
                # کاراکتر غیرمنتظره — یک گام جلو تا گیر نکنیم
                self._i += 1
                continue
            self._skip_ws()
            if self._i < n and t[self._i] == "=":
                self._i += 1
                value = self._read_value()
            else:
                # نام بدون مقدار (مثل عضو list درون block) — scalar بدون مقدار
                value = Node("scalar")
                value.value = self._convert_scalar(name)
                name = "__anon__"
            self._store(node, name, value)

    def _store(self, node: Node, name: str, value: Node):
        children = node.children
        if name in children:
            node.same_name = node.same_name or {}
            node.same_name.setdefault(name, []).append(value)
        else:
            children[name] = value


def parse_save(text: str) -> Node:
    """متن ذوب‌شدهٔ سیو را به درخت Node تبدیل می‌کند (ریشه: block ریشه)."""
    return SaveParser(text).parse()


# ============================================================
# ایمن‌سازی ورودی فایل (مرحلهٔ ۱)
# ============================================================

class SavePathError(Exception):
    """ورودی نامعتبر/ناامن برای فایل سیو."""


def resolve_save_path(save_name: str) -> str:
    """نام سیو را فقط داخل SAVE_DIR resolve می‌کند و مسیر امن برمی‌گرداند.

    - path traversal با ``..`` و مسیر مطلق خارج از SAVE_DIR رد می‌شود
    - فقط پسوند ``.ck3`` پذیرفته می‌شود
    - symlink/junction به خارج از SAVE_DIR بدون اجازه خوانده نمی‌شود
    """
    if not save_name or save_name.strip() == "":
        raise SavePathError("نام فایل سیو خالی است.")
    if "\x00" in save_name:
        raise SavePathError("نام فایل سیو شامل نویسهٔ null است.")

    candidate = os.path.abspath(os.path.join(SAVE_DIR, save_name))
    save_root = os.path.abspath(SAVE_DIR)
    # مقایسهٔ canonical: مسیر باید داخل SAVE_DIR بماند
    if os.path.normcase(candidate) != save_root and not os.path.normcase(candidate).startswith(
        os.path.normcase(save_root) + os.sep
    ):
        raise SavePathError("مسیر فایل سیو خارج از پوشهٔ سیو است: " + save_name)

    if os.path.splitext(candidate)[1].lower() != ".ck3":
        raise SavePathError("فقط فایل‌های .ck3 پذیرفته می‌شوند: " + save_name)

    if not os.path.exists(candidate):
        raise SavePathError("فایل سیو پیدا نشد: " + save_name)

    # symlink/junction: مقصد واقعی هم باید داخل SAVE_DIR بماند
    real = os.path.realpath(candidate)
    real_root = os.path.realpath(save_root)
    if os.path.normcase(real) != os.path.normcase(candidate) and not os.path.normcase(real).startswith(
        os.path.normcase(real_root) + os.sep
    ):
        raise SavePathError("فایل سیو symlink/junction به خارج از پوشهٔ سیو است: " + save_name)

    if not os.path.isfile(candidate):
        raise SavePathError("مسیر سیو یک فایل معمولی نیست: " + save_name)
    return candidate


def _autosave_filtered(saves):
    """سیوهای پیشنهادی بدون autosave_exit (طبق AGENTS.md)."""
    return [f for f in saves if f.lower() != "autosave_exit.ck3"]


# ============================================================
# API داخلی روشن (مرحلهٔ ۱) — روی درخت Node
# ============================================================

def find_root(root: Node) -> Node:
    """ریشهٔ درخت (خود root؛ برای شفافیت API)."""
    return root


def find_child(node: Node, name: str):
    """اولین child با نام داده‌شده، یا None (نبودن فیلد قابل تشخیص است)."""
    return node.get(name)


def find_child_by_id(node: Node, name: str, ident):
    """child هم‌نام که شناسهٔ داده‌شده (scalar int یا key رشته‌ای) دارد."""
    for child in node.get_all(name):
        if ident is None:
            continue
        for id_field in ("id", "key", "character", "title"):
            idn = child.get(id_field)
            if idn is None:
                continue
            if isinstance(ident, int):
                if idn.as_int() == ident:
                    return child
            elif str(idn.as_str()) == str(ident):
                return child
    return None


def read_scalar(node: Node, name: str, default=None):
    """scalar نام‌دار؛ اگر فیلد نباشد default (نبودن با صفر قاطی نمی‌شود)."""
    child = node.get(name)
    if child is None:
        return default
    v = child.as_str()
    return default if v is None else v


def read_list(node: Node, name: str):
    """list ساده (اعداد/رشته‌ها)؛ فیلد نبودن → None، لیست خالی واقعی → []."""
    child = node.get(name)
    if child is None:
        return None
    return [m.value for m in child.as_list()]


def read_object_list(node: Node, name: str):
    """object-list مثل members={ { character=123 faction=456 } }؛ نبودن → None."""
    child = node.get(name)
    if child is None:
        return None
    return child.as_list()


# ============================================================
# Stage-2 structural extractors — domain, county, province, holding, building
# ============================================================

def _get_node(root: Node, *path: str):
    """Walk a structural path from root; return the final Node or None."""
    cur = root
    for key in path:
        if cur is None or cur.kind != "block":
            return None
        cur = cur.children.get(key)
    return cur


def _scalar_val(node: Node):
    """Return the scalar value of a Node, or None if not scalar."""
    if node is not None and node.kind == "scalar":
        return node.value
    return None


def _list_items(node: Node):
    """Return the children of a list Node (object-list items), or []."""
    if node is None or node.kind != "list":
        return []
    if node.children is None:
        return []
    if isinstance(node.children, list):
        return node.children
    return list(node.children.values())


def extract_domain(root: Node) -> list:
    """Extract player domain from living.<player_id>.landed_data.domain,
    mapping each ID through landed_titles to get key/tier/holder/name.
    Returns a list of dicts. domain_count counts only c_... county titles."""
    result = []
    pc = _get_node(root, "played_character")
    if pc is None:
        return result
    pid_node = pc.children.get("character")
    pid = _scalar_val(pid_node)
    if pid is None:
        return result
    living = _get_node(root, "living")
    if living is None:
        return result
    ln = living.children.get(str(pid))
    if ln is None or ln.kind != "block":
        return result
    ld = ln.children.get("landed_data")
    if ld is None or ld.kind != "block":
        return result
    domain_node = ld.children.get("domain")
    if domain_node is None or domain_node.kind != "list":
        return result
    domain_ids = []
    for item in _list_items(domain_node):
        v = _scalar_val(item)
        if v is not None:
            domain_ids.append(str(v))
    lt = _get_node(root, "landed_titles", "landed_titles")
    if lt is None or lt.kind != "block":
        return result
    for did in domain_ids:
        t = lt.children.get(did)
        if t is None or t.kind != "block":
            result.append({"title_id": did, "key": None, "mapped": False})
            continue
        key_n = t.children.get("key")
        key = _scalar_val(key_n) if key_n else None
        holder_n = t.children.get("holder")
        holder = _scalar_val(holder_n) if holder_n else None
        name_n = t.children.get("name")
        name = _scalar_val(name_n) if name_n else None
        tier = key[:1] if key else None
        is_county = key.startswith("c_") if key else False
        result.append({
            "title_id": did,
            "key": key,
            "tier": tier,
            "name": name,
            "holder": holder,
            "is_county": is_county,
            "is_domain": holder is not None and str(holder) == str(pid),
            "mapped": True,
        })
    return result


def extract_counties(root: Node, domain_title_ids=None) -> list:
    """اطلاعات شهرستان‌ها از county_manager.counties.

    حالت پیش‌فرض (domain_title_ids=None): فقط شهرستان‌های دامنهٔ بازیکن + تجمیع جهانی —
    ۲۶۵۲ ردیفِ کل دنیا خروجی JSON را ۷۱٪ پر می‌کرد؛ حالا خروجیِ ردیفی = دامنهٔ بازیکن
    و آمار کل دنیا در quality.counts می‌ماند (counties_world / development_world_avg).
    هر county در county_manager با کلید c_... است و به landed_titles از طریق
    title_id عددی وصل می‌شود (index یک‌بار ساخته می‌شود — بدون جستجوی تکراری)."""
    result = []
    cm = _get_node(root, "county_manager", "counties")
    if cm is None or cm.kind != "block":
        return result
    lt = _get_node(root, "landed_titles", "landed_titles")

    # ایندکس یک‌باره: کلید c_ (کلید مشترک با county_manager) -> title_id/holder/capital/de_jure
    lt_index = {}
    if lt is not None and lt.kind == "block":
        for tk, tn in lt.children.items():
            if tn is None or tn.kind != "block":
                continue
            kn = tn.children.get("key")
            key = _scalar_val(kn) if kn is not None else None
            if key is None or not str(key).startswith("c_"):
                continue
            hn = tn.children.get("holder")
            capn = tn.children.get("capital")
            djn = tn.children.get("de_jure_liege")
            lt_index[str(key)] = {
                "title_id": str(tk),
                "holder": _scalar_val(hn) if hn is not None else None,
                "capital": _scalar_val(capn) if capn is not None else None,
                "de_jure_liege": _scalar_val(djn) if djn is not None else None,
            }
    dom_ids = {str(t) for t in (domain_title_ids or [])}

    world_dev = []
    world_ctrl = []
    for ckey, cn in cm.children.items():
        if cn is None or cn.kind != "block":
            continue
        entry = {
            "county_key": ckey,
            "development": _scalar_val(cn.children.get("development")),
            "development_progress": _scalar_val(cn.children.get("development_progress")),
            "county_control": _scalar_val(cn.children.get("county_control")),
            "culture": _scalar_val(cn.children.get("culture")),
            "faith": _scalar_val(cn.children.get("faith")),
        }
        title = lt_index.get(str(ckey))
        if title is None:
            entry["title_id"] = None
            entry["mapped"] = False
        else:
            entry.update(title)
            entry["mapped"] = True
            entry["county_key"] = ckey  # کلید county_manager مرجع است
        dev = entry.get("development")
        ctrl = entry.get("county_control")
        if isinstance(dev, (int, float)):
            world_dev.append(dev)
        if isinstance(ctrl, (int, float)):
            world_ctrl.append(ctrl)
        is_domain = (entry.get("title_id") in dom_ids) if dom_ids else None
        if dom_ids and not is_domain:
            continue  # خارج از دامنهٔ بازیکن — فقط در تجمیع جهانی شمرده شد
        result.append(entry)

    # تجمیع جهانی روی خودِ تابع (بدون حدس — میانگین از دادهٔ موجود)
    extract_counties.world_total = len(world_dev)
    extract_counties.world_dev_avg = round(sum(world_dev) / len(world_dev), 2) if world_dev else None
    extract_counties.world_ctrl_avg = round(sum(world_ctrl) / len(world_ctrl), 2) if world_ctrl else None
    return result


# سطح ساختمان از پسوند نوع ساختمان در سیو (castle_01 → سطح ۱) — الگوی خود داده
_BLEVEL_RE = re.compile(r"_(\d{1,2})$")


def extract_provinces(root: Node, domain_county_keys: list) -> list:
    """Extract holding/province/building data for provinces that are the capital
    of a domain county (or all provinces if domain_county_keys is empty)."""
    result = []
    provs = _get_node(root, "provinces")
    if provs is None or provs.kind != "block":
        return result
    lt = _get_node(root, "landed_titles", "landed_titles")
    # Build capital province ID -> county key mapping for domain counties
    cap_to_key = {}
    if lt is not None and lt.kind == "block" and domain_county_keys:
        for tk, tn in lt.children.items():
            if tn is None or tn.kind != "block":
                continue
            kn = tn.children.get("key")
            if kn is None:
                continue
            key = _scalar_val(kn)
            if key in domain_county_keys:
                cap = _scalar_val(tn.children.get("capital"))
                if cap is not None:
                    cap_to_key[str(cap)] = key
    for pk, pn in provs.children.items():
        if pn is None or pn.kind != "block":
            continue
        h = pn.children.get("holding")
        if h is None or h.kind != "block":
            continue
        # Filter: only include provinces that are capitals of domain counties
        # (or all if no domain filter)
        if domain_county_keys and pk not in cap_to_key:
            continue
        entry = {
            "province_id": pk,
            "county_key": cap_to_key.get(pk),
            "winter_severity": _scalar_val(pn.children.get("winter_severity")),
            "next_winter_target_date": _scalar_val(pn.children.get("next_winter_target_date")),
            "holding_type": _scalar_val(h.children.get("type")),
            "holding_owner": _scalar_val(h.children.get("owner")),
            "income": _scalar_val(h.children.get("income")),
            "levy": _scalar_val(h.children.get("levy")),
            "garrison": _scalar_val(h.children.get("garrison")),
            "fort_level": _scalar_val(pn.children.get("fort_level")),
            "buildings": [],
            "constructions": [],
        }
        # ساختمان‌های تکمیل‌شده: level از پسوند نوع (_01/_02/_10) — از دادهٔ سیو، بدون حدس
        b = h.children.get("buildings")
        if b is not None and b.kind == "list":
            for item in _list_items(b):
                if item is None:
                    continue
                # اسلات خالی ({ }) ممکن است block یا list خالی پارس شود — هر دو «بدون نوع»اند
                btype = _scalar_val(item.children.get("type")) if item.kind == "block" else None
                level = None
                if btype is not None:
                    m = _BLEVEL_RE.search(str(btype))
                    if m:
                        level = int(m.group(1))
                entry["buildings"].append({"type": btype, "level": level})
        # ساخت‌وسازهای در حال انجام: در سیو واقعی داخل holding است (building/index/start_time/days/cost)
        # — get_all برای چند سازهٔ هم‌زمان؛ construction سطح province فقط fallbackِ سازگاری است
        for cons in h.get_all("constructions"):
            if cons is None or cons.kind != "block":
                continue
            cost_n = cons.children.get("cost")
            entry["constructions"].append({
                "building": _scalar_val(cons.children.get("building")),
                "index": _scalar_val(cons.children.get("index")),
                "start_time": _scalar_val(cons.children.get("start_time")),
                "days": _scalar_val(cons.children.get("days")),
                "cost_gold": _scalar_val(cost_n.children.get("gold")) if cost_n is not None and cost_n.kind == "block" else None,
                "cost_prestige": _scalar_val(cost_n.children.get("prestige")) if cost_n is not None and cost_n.kind == "block" else None,
                "character": _scalar_val(cons.children.get("character")),
            })
        cons_p = pn.children.get("construction")
        if cons_p is not None and cons_p.kind == "block" and not entry["constructions"]:
            entry["constructions"].append({
                "building": _scalar_val(cons_p.children.get("type")),
                "completion_date": _scalar_val(cons_p.children.get("completion_date")),
            })
        result.append(entry)
    return result


def build_economy_report(domain: list, counties: list, provinces: list) -> str:
    """Build the stage-2 economy report section (appended to state_report.txt)."""
    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("ECONOMY & DOMAIN (Stage 2)")
    lines.append("=" * 60)
    lines.append("")

    # domain summary
    lines.append("--- Domain Summary ---")
    mapped = [d for d in domain if d.get("mapped")]
    c_titles = [d for d in mapped if d.get("is_county")]
    lines.append(f"Domain title IDs: {len(domain)}")
    lines.append(f"Mapped titles: {len(mapped)}")
    lines.append(f"County (c_) titles: {len(c_titles)}")
    lines.append(f"domain_count (c_ only): {len(c_titles)}")
    lines.append("")
    for d in domain:
        key = d.get("key") or "unmapped"
        tier = d.get("tier") or "?"
        name = d.get("name") or "?"
        is_dom = d.get("is_domain", False)
        lines.append(f"  {key} [{tier}] name={name} direct_domain={'yes' if is_dom else 'no'}")
    lines.append("")

    # county table (فقط دامنهٔ بازیکن — آمار کل دنیا در JSON: quality.counts)
    lines.append("--- Counties (player domain) ---")
    lines.append(f"Domain county rows: {len(counties)} (world entries: {getattr(extract_counties, 'world_total', '?')})")
    lines.append("")
    lines.append(f"{'County':<20} {'Dev':>6} {'Control':>10} {'Culture':>8} {'Faith':>6} {'Holder':>10}")
    for c in counties:
        dev = c.get("development")
        dev_s = str(dev) if dev is not None else "missing"
        ctrl = c.get("county_control")
        ctrl_s = f"{ctrl:.1f}" if ctrl is not None else "missing"
        cul = c.get("culture")
        cul_s = str(cul) if cul is not None else "missing"
        fai = c.get("faith")
        fai_s = str(fai) if fai is not None else "missing"
        holder = c.get("holder")
        holder_s = str(holder) if holder is not None else "missing"
        lines.append(f"{c['county_key']:<20} {dev_s:>6} {ctrl_s:>10} {cul_s:>8} {fai_s:>6} {holder_s:>10}")
    lines.append("")

    # holdings
    lines.append("--- Holdings & Provinces ---")
    lines.append(f"Provinces with holding data: {len(provinces)}")
    total_buildings = sum(len(p["buildings"]) for p in provinces)
    lines.append(f"Total building instances: {total_buildings}")
    lines.append("")
    for p in provinces:
        pid = p["province_id"]
        htype = p.get("holding_type") or "missing"
        income = p.get("income")
        income_s = str(income) if income is not None else "missing"
        levy = p.get("levy")
        levy_s = str(levy) if levy is not None else "missing"
        garr = p.get("garrison")
        garr_s = str(garr) if garr is not None else "missing"
        blist = p["buildings"]
        btypes = ", ".join(b["type"] or "unknown" for b in blist) if blist else "none"
        lines.append(f"  province[{pid}] type={htype} income={income_s} levy={levy_s} garrison={garr_s} buildings=[{btypes}]")
    lines.append("")

    # missing data
    lines.append("--- Missing / Unknown Data ---")
    missing_count = 0
    for c in counties:
        for f in ["development", "county_control", "culture", "faith"]:
            if c.get(f) is None:
                missing_count += 1
    for p in provinces:
        if p.get("holding_type") is None:
            missing_count += 1
        if p.get("income") is None:
            missing_count += 1
    unmapped = [d for d in domain if not d.get("mapped")]
    lines.append(f"Unmapped domain IDs: {len(unmapped)}")
    lines.append(f"Missing county fields: {missing_count}")
    lines.append(f"Building level: unknown (not determinable from save structure)")
    lines.append("")

    return "\n".join(lines)


# ============================================================
# استخراج سیاست داخلی و جانشینی (مرحلهٔ ۳) — فقط Parser ساختاری
# ============================================================

def _all_values(node: Node, name: str) -> list:
    """همهٔ مقادیر یک نام — children[name] + تکرارها در same_name (بدون از دست دادن ترتیب)."""
    if node is None or node.kind != "block":
        return []
    out = []
    if name in node.children:
        out.append(node.children[name])
    if node.same_name and name in node.same_name:
        out.extend(node.same_name[name])
    return out


def _age_from(root: Node, birth) -> int:
    """سن از تاریخ بازی ریشه و تاریخ تولد؛ اگر قابل محاسبه نیست None."""
    try:
        y, m, d = (int(x) for x in str(root.children["date"].value).split("."))
        by, bm, bd = (int(x) for x in str(birth).split("."))
        age = y - by
        if (m, d) < (bm, bd):
            age -= 1
        return age
    except Exception:
        return None


def _character_summary(root: Node, cid, living, dead) -> dict:
    """خلاصهٔ ساختاری یک شخصیت با ID دقیق؛ زنده/مرده از محل بلوک تشخیص داده می‌شود."""
    key = str(cid)
    src = living.children.get(key) if living is not None else None
    alive = True
    if src is None:
        src = dead.children.get(key) if dead is not None else None
        alive = False if src is not None else None  # None = نه زنده نه مردهٔ شناخته‌شده (unmapped)
    if src is None:
        return {"id": cid, "mapped": False}
    birth = _scalar_val(src.children.get("birth"))
    summary = {
        "id": cid,
        "mapped": True,
        "alive": alive,
        "name": _scalar_val(src.children.get("first_name")),
        "birth": birth,
        "age": _age_from(root, birth) if birth is not None else None,
        "female": _scalar_val(src.children.get("female")),
        "culture": _scalar_val(src.children.get("culture")),
        "faith": _scalar_val(src.children.get("faith")),  # در این سیو برای بازیکن موجود نیست
        "dynasty_house": _scalar_val(src.children.get("dynasty_house")),
        "skills": _skill_list(src),
        "traits": _id_list(src, "traits"),
        "landed": src.children.get("landed_data") is not None,
    }
    asrc = src.children.get("alive_data")
    summary["stress"] = _scalar_val(asrc.children.get("stress")) if asrc is not None else None
    summary["health"] = _scalar_val(asrc.children.get("health")) if asrc is not None else None
    summary["fertility"] = _scalar_val(asrc.children.get("fertility")) if asrc is not None else None
    summary["lifestyle_xp"] = _scalar_val(src.children.get("lifestyle_xp"))
    return summary


def _skill_list(src: Node):
    sk = src.children.get("skill")
    if sk is None:
        return None
    if sk.kind == "list":
        return [x.value for x in sk.children]
    return sk.value


def _id_list(src: Node, name: str):
    v = src.children.get(name)
    if v is None:
        return None
    if v.kind == "list":
        return [x.value for x in v.children]
    return [v.value]


def _resources_block(ad: Node) -> dict:
    """بلوک منابع بازیکن (فاز عملیاتی‌سازی) — توان پرداخت هر اقدام از همین‌جا چک می‌شود.
    ساختار سیو: gold.value / piety.currency+accumulated / prestige.currency+accumulated.
    هر فیلدِ غایب None می‌ماند (missing ≠ صفر)."""
    if ad is None or ad.kind != "block":
        return {}
    out = {}
    gold = ad.children.get("gold")
    out["gold"] = _scalar_val(gold.children.get("value")) if gold is not None else None
    for res in ("piety", "prestige"):
        node = ad.children.get(res)
        out[res] = _scalar_val(node.children.get("currency")) if node is not None else None
        out[f"{res}_accumulated"] = (
            _scalar_val(node.children.get("accumulated")) if node is not None else None
        )
    return out


def extract_player_and_family(root: Node) -> dict:
    """بازیکن، خانواده و آمار حیاتی — از living/<pid> با مسیر ساختاری دقیق."""
    pc = root.children.get("played_character")
    pid_node = pc.children.get("character") if pc is not None else None
    if pid_node is None:
        return {}
    pid = str(pid_node.value)
    living = root.children.get("living")
    dead = root.children.get("dead_unprunable")
    pblock = living.children.get(pid) if living is not None else None
    if pblock is None:
        return {"id": pid, "mapped": False}

    player = _character_summary(root, pid, living, dead)
    player["nickname"] = _scalar_val(pblock.children.get("nickname"))
    ad = pblock.children.get("alive_data")
    if ad is not None:
        gold = ad.children.get("gold")
        piety = ad.children.get("piety")
        prestige = ad.children.get("prestige")
        player["stress"] = _scalar_val(ad.children.get("stress"))
        player["health"] = _scalar_val(ad.children.get("health"))
        player["fertility"] = _scalar_val(ad.children.get("fertility"))
        player["income"] = _scalar_val(ad.children.get("income"))
        player["gold"] = _scalar_val(gold.children.get("value")) if gold is not None else None
        player["piety"] = _scalar_val(piety.children.get("currency")) if piety is not None else None
        player["prestige"] = _scalar_val(prestige.children.get("currency")) if prestige is not None else None
        player["resources"] = _resources_block(ad)  # بلوک توان پرداخت (فلز/تقوا/شکوه)
        player["heir_raw"] = _id_list(ad, "heir")  # خام؛ اعتبارسنجی وارث در extract_succession

    ld = pblock.children.get("landed_data")
    if ld is not None:
        player["laws"] = _id_list(ld, "laws")
        player["government"] = _scalar_val(ld.children.get("government"))
        player["realm_capital"] = _scalar_val(ld.children.get("realm_capital"))
        player["domain_limit"] = _scalar_val(ld.children.get("domain_limit"))
        player["vassal_power_value"] = _scalar_val(ld.children.get("vassal_power_value"))
        player["dread"] = _scalar_val(ld.children.get("dread"))
        player["tyranny"] = _scalar_val(ld.children.get("tyranny"))
        player["succession_ids_raw"] = _id_list(ld, "succession")
        contract_ids = []
        for vc in _all_values(ld, "vassal_contracts"):
            if vc.kind == "list":
                contract_ids.extend(x.value for x in vc.children)
            else:
                contract_ids.append(vc.value)
        player["vassal_contract_ids"] = contract_ids

    fd = pblock.children.get("family_data")
    family = {"primary_spouse": None, "spouses": [], "former_spouses": [], "children": []}
    if fd is not None:
        ps = _all_values(fd, "primary_spouse")
        if ps:
            family["primary_spouse"] = ps[0].value
        seen = set()
        for f in ps + _all_values(fd, "spouse"):
            if f.value not in seen:
                seen.add(f.value)
                family["spouses"].append(f.value)
        fs = fd.children.get("former_spouses")
        if fs is not None and fs.kind == "list":
            family["former_spouses"] = [x.value for x in fs.children]
        ch = fd.children.get("child")
        if ch is not None and ch.kind == "list":
            family["children"] = [x.value for x in ch.children]
    pd = pblock.children.get("playable_data")
    if pd is not None:
        player["legitimacy"] = _scalar_val(pd.children.get("legitimacy"))
        player["diarchy_successor"] = _scalar_val(pd.children.get("diarchy_successor"))

    player["family"] = family
    return player


def extract_characters(root: Node, ids) -> dict:
    """خلاصهٔ شخصیت‌ها برای مجموعهٔ ID داده‌شده (خانواده + رعایا + رهبران فکشن)."""
    living = root.children.get("living")
    dead = root.children.get("dead_unprunable")
    out = {}
    for cid in ids:
        key = str(cid)
        if key in out:
            continue
        out[key] = _character_summary(root, cid, living, dead)
    return out


def extract_vassals(root: Node, player: dict) -> list:
    """رعایا از vassal_contracts.database با ID دقیق؛ سطوح قرارداد خام می‌ماند
    (نقشهٔ سطح→درصد مالیات/سرباز در دادهٔ سیو موجود نیست و حدس زده نمی‌شود)."""
    db = _get_node(root, "vassal_contracts", "database")
    if db is None or db.kind != "block":
        return []
    out = []
    for cid in player.get("vassal_contract_ids", []):
        c = db.children.get(str(cid))
        if c is None or c.kind != "block":
            out.append({"contract_id": cid, "mapped": False})
            continue
        levels = c.children.get("levels")
        out.append({
            "contract_id": cid,
            "mapped": True,
            "vassal": _scalar_val(c.children.get("vassal")),
            "liege": _scalar_val(c.children.get("liege")),
            "contract_group": _scalar_val(c.children.get("contract_group")),
            "levels_raw": [x.value for x in levels.children] if levels is not None and levels.kind == "list" else None,
            "war_with_liege": _scalar_val(c.children.get("war_with_liege")),
        })
    return out


def extract_factions(root: Node) -> list:
    """فکشن‌های فعال از faction_manager.factions — هر فکشن با ID دقیق؛
    اعضا با character ID map می‌شوند؛ جنگ‌های تاریخچه اینجا خوانده نمی‌شود.
    اتصال قابل‌اثبات (فاز عملیاتی‌سازی):
    - target_kind: هدف، character است یا title (بررسی عضویت کلید، بدون حدس)
    - target_is_player: آیا هدف مستقیم فکشن، خودِ بازیکن است
    - is_civil_war: آیا warِ فکشن به یک جنگِ فعال وصل است (ID جنگ در wars.active_wars)"""
    factions = _get_node(root, "faction_manager", "factions")
    if factions is None or factions.kind != "block":
        return []
    living = _get_node(root, "living")
    lt = _get_node(root, "landed_titles", "landed_titles")
    active_wars = _get_node(root, "wars", "active_wars")
    war_ids = set(str(k) for k in active_wars.children.keys()) if (
        active_wars is not None and active_wars.children) else set()
    pc = _get_node(root, "played_character")
    pid_node = pc.children.get("character") if pc is not None else None
    player_id = _scalar_val(pid_node)
    out = []
    for fid, f in factions.children.items():
        if f is None or f.kind != "block":
            continue
        members = []
        m = f.children.get("members")
        if m is not None:
            for item in m.children:
                if item is not None and item.kind == "block":
                    ch = item.children.get("character")
                    if ch is not None:
                        members.append(ch.value)
                elif item is not None and item.kind == "scalar":
                    members.append(item.value)
        title_members = []
        tm = f.children.get("title_members")
        if tm is not None:
            for item in tm.children:
                if item is not None and item.kind == "block":
                    for cand in ("title", "county", "title_id"):
                        t = item.children.get(cand)
                        if t is not None:
                            title_members.append(t.value)
                            break
        power = _scalar_val(f.children.get("power"))
        threshold = _scalar_val(f.children.get("power_threshold"))
        danger = None
        if isinstance(power, (int, float)) and isinstance(threshold, (int, float)) and threshold:
            danger = power > threshold
        target = _no_sentinel(_scalar_val(f.children.get("target")))
        target_str = str(target) if target is not None else None
        if target_str is not None and living is not None and living.children and target_str in living.children:
            target_kind = "character"
        elif target_str is not None and lt is not None and lt.children and target_str in lt.children:
            target_kind = "title"
        else:
            target_kind = None
        war_ref = f.children.get("war")
        war_val = _no_sentinel(_scalar_val(war_ref)) if war_ref is not None else None
        out.append({
            "faction_id": fid,
            "type": _scalar_val(f.children.get("type")),
            "target": target,
            "target_kind": target_kind,
            "target_is_player": (
                True if (player_id is not None and target_str is not None and str(player_id) == target_str)
                else (False if target_str is not None else None)
            ),
            "is_civil_war": (
                (str(war_val) in war_ids) if war_val is not None and war_ids else (False if war_val is None else None)
            ),
            "leader": _no_sentinel(_scalar_val(f.children.get("leader"))),
            "power": power,
            "power_threshold": threshold,
            "power_over_threshold": danger,  # True/False/None(دادهٔ ناقص)
            "discontent": _scalar_val(f.children.get("discontent")),
            "update_day": _scalar_val(f.children.get("update_day")),
            "date": _scalar_val(f.children.get("date")),
            "members": members,
            "title_members": title_members,
            "war": war_val,
            "special_character": _scalar_val(f.children.get("special_character")),
            "special_title": _scalar_val(f.children.get("special_title")),
        })
    return out


def _faith_culture_names(root: Node) -> tuple:
    """دو دیکشنری lookup: faith_id→tag و culture_id→template (نام موجود در سیو)."""
    faith_names, culture_names = {}, {}
    fa = _get_node(root, "religion", "faiths")
    if fa is not None and fa.kind == "block":
        for fid, fb in fa.children.items():
            if fb is not None and fb.kind == "block":
                tag = fb.children.get("tag")
                if tag is not None:
                    faith_names[fid] = tag.value
    cu = _get_node(root, "culture_manager", "cultures")
    if cu is not None and cu.kind == "block":
        for cuid, cb in cu.children.items():
            if cb is not None and cb.kind == "block":
                tpl = cb.children.get("culture_template")
                if tpl is not None:
                    culture_names[cuid] = tpl.value
    return faith_names, culture_names


def extract_faith_culture(root: Node, player: dict, characters: dict, counties: list) -> dict:
    """دین و فرهنگ با نام lookup؛ اگر نام در سیو نیست، فقط ID — بدون نام ساختگی."""
    faith_names, culture_names = _faith_culture_names(root)
    player_faith = player.get("faith")
    player_culture = player.get("culture")
    out = {
        "player_faith": player_faith,
        "player_faith_name": faith_names.get(str(player_faith)) if player_faith is not None else None,
        "player_faith_available": player_faith is not None,  # در این فرمت سیو روی بلوک بازیکن نیست
        "player_culture": player_culture,
        "player_culture_name": culture_names.get(str(player_culture)) if player_culture is not None else None,
        "county_faith_culture": [],
        "mismatches": [],
    }
    for c in counties:
        entry = {
            "county_key": c.get("county_key"),
            "faith": c.get("faith"),
            "faith_name": faith_names.get(str(c.get("faith"))) if c.get("faith") is not None else None,
            "culture": c.get("culture"),
            "culture_name": culture_names.get(str(c.get("culture"))) if c.get("culture") is not None else None,
        }
        out["county_faith_culture"].append(entry)
        if player_faith is not None and entry["faith"] is not None and entry["faith"] != player_faith:
            out["mismatches"].append({"kind": "player_county_faith", "county": entry["county_key"]})
    for cid, ch in characters.items():
        if not ch.get("mapped"):
            continue
        if player_faith is not None and ch.get("faith") is not None and ch["faith"] != player_faith:
            out["mismatches"].append({"kind": "player_character_faith", "character": cid})
        if player_culture is not None and ch.get("culture") is not None and ch["culture"] != player_culture:
            out["mismatches"].append({"kind": "player_character_culture", "character": cid})
    return out


def extract_succession(root: Node, player: dict, characters: dict) -> dict:
    """جانشینی: قوانین از landed_data.laws؛ ترتیب ذخیره‌شدهٔ بازی از landed_data.succession.
    ادعای وارث فقط بر اساس این ترتیبِ ذخیره‌شده گزارش می‌شود و محاسبهٔ مستقل
    الگوریتم بازی از دادهٔ خام سیو انجام نمی‌شود (صریحاً علامت‌گذاری می‌شود)."""
    order = player.get("succession_ids_raw") or []
    line = []
    for sid in order:
        ch = characters.get(str(sid)) or {}
        line.append({
            "id": sid,
            "name": ch.get("name") if ch.get("mapped") else None,
            "alive": ch.get("alive"),
            "mapped": ch.get("mapped", False),
        })
    heir = None
    if line and line[0]["mapped"] and line[0]["alive"]:
        heir = {"id": line[0]["id"], "name": line[0]["name"]}
    return {
        "laws": player.get("laws") or [],
        "gender_law": next((l for l in (player.get("laws") or []) if "law" in str(l) and ("male" in str(l) or "female" in str(l))), None),
        "succession_line": line,
        "first_in_line": heir,  # فقط اگر از ترتیب ذخیره‌شده قابل اثبات باشد
        "heir_raw_refs": player.get("heir_raw"),  # مرجع خام؛ اعتبارسنجی‌شده نیست
        "algorithm_recomputed": False,  # الگوریتم بازی بازسازی نشده — صادقانه
    }


def build_politics_report(player: dict, characters: dict, vassals: list,
                          factions: list, faith_culture: dict, succession: dict) -> str:
    """گزارش بخش سیاست داخلی (مرحلهٔ ۳) — به انتهای state_report.txt اضافه می‌شود."""
    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("INTERNAL POLITICS & SUCCESSION (Stage 3)")
    lines.append("=" * 60)
    lines.append("")

    # player & family
    lines.append("--- Player & Family ---")
    lines.append(f"Player: {player.get('name')} (id={player.get('id')}) age={player.get('age')} "
                 f"female={player.get('female')} culture={player.get('culture')} faith={player.get('faith') or 'missing'}")
    lines.append(f"  stress={player.get('stress')} health={player.get('health')} fertility={player.get('fertility')} income={player.get('income')}")
    fam = player.get("family", {})
    lines.append(f"  spouses={len(fam.get('spouses', []))} former_spouses={len(fam.get('former_spouses', []))} children={len(fam.get('children', []))}")
    for cid in fam.get("children", []):
        ch = characters.get(str(cid)) or {}
        nm = ch.get("name") if ch.get("mapped") else "unmapped"
        lines.append(f"    child {cid}: {nm} alive={ch.get('alive')}")
    lines.append("")

    # characters mapped
    mapped = [c for c in characters.values() if c.get("mapped")]
    lines.append(f"--- Characters (mapped {len(mapped)}/{len(characters)}) ---")
    for cid, ch in list(characters.items())[:20]:
        if not ch.get("mapped"):
            lines.append(f"  {cid}: unmapped (not in living/dead_unprunable)")
            continue
        lines.append(f"  {cid}: {ch.get('name')} age={ch.get('age')} female={ch.get('female')} "
                     f"culture={ch.get('culture')} faith={ch.get('faith') or 'missing'} alive={ch.get('alive')}")
    if len(characters) > 20:
        lines.append(f"  ... and {len(characters) - 20} more")
    lines.append("")

    # vassals
    lines.append(f"--- Vassals ({sum(1 for v in vassals if v.get('mapped'))}/{len(vassals)} mapped) ---")
    for v in vassals:
        if not v.get("mapped"):
            lines.append(f"  contract {v.get('contract_id')}: unmapped")
            continue
        vid = v.get("vassal")
        ch = characters.get(str(vid)) or {}
        nm = ch.get("name") if ch.get("mapped") else "unmapped"
        lines.append(f"  contract {v.get('contract_id')}: vassal={vid} ({nm}) group={v.get('contract_group')} "
                     f"levels_raw={v.get('levels_raw')} war_with_liege={v.get('war_with_liege')}")
    lines.append("  note: tax/levy percentages are NOT derivable from raw contract levels (game-data mapping absent from save)")
    lines.append("")

    # factions
    lines.append(f"--- Factions ({len(factions)} active) ---")
    danger_count = 0
    for f in factions:
        over = f.get("power_over_threshold")
        marker = ""
        if over is True:
            marker = "  ** OVER THRESHOLD **"
            danger_count += 1
        lines.append(f"  faction {f.get('faction_id')}: type={f.get('type')} target={f.get('target')} "
                     f"leader={f.get('leader')} power={f.get('power')} threshold={f.get('power_threshold')} "
                     f"discontent={f.get('discontent')} members={len(f.get('members', []))} "
                     f"title_members={len(f.get('title_members', []))} war={f.get('war')}{marker}")
    lines.append(f"  factions over power threshold (numeric criterion): {danger_count}")
    lines.append("")

    # faith & culture
    lines.append("--- Faith & Culture ---")
    if faith_culture.get("player_faith_available"):
        lines.append(f"  player faith: {faith_culture.get('player_faith')} ({faith_culture.get('player_faith_name')})")
    else:
        lines.append("  player faith: NOT STORED on player block in this save format (no guess made)")
    lines.append(f"  player culture: {faith_culture.get('player_culture')} ({faith_culture.get('player_culture_name')})")
    for m in faith_culture.get("mismatches", [])[:10]:
        lines.append(f"  mismatch: {m}")
    lines.append("")

    # succession
    lines.append("--- Succession ---")
    lines.append(f"  laws: {succession.get('laws')}")
    lines.append(f"  gender law: {succession.get('gender_law')}")
    heir = succession.get("first_in_line")
    if heir:
        lines.append(f"  first in stored succession line: {heir['name']} (id={heir['id']})")
    else:
        lines.append("  first in stored succession line: not provable from save data")
    line = succession.get("succession_line", [])
    lines.append(f"  stored succession line ({len(line)} entries, as saved by the game — not recomputed):")
    for s in line[:10]:
        nm = s.get("name") or "unmapped"
        lines.append(f"    {s.get('id')}: {nm} alive={s.get('alive')}")
    lines.append("  note: heir claims beyond the stored line, partition shares and title creation are NOT computable from this save (algorithm not reconstructed)")
    lines.append("")

    # missing / unmapped
    unmapped_chars = [cid for cid, ch in characters.items() if not ch.get("mapped")]
    lines.append("--- Missing / Unmapped (Stage 3) ---")
    lines.append(f"  unmapped character ids: {len(unmapped_chars)}")
    lines.append(f"  unmapped vassal contracts: {sum(1 for v in vassals if not v.get('mapped'))}")
    lines.append(f"  factions without mapped leader: {sum(1 for f in factions if f.get('leader') is not None and not (characters.get(str(f.get('leader'))) or {}).get('mapped'))}")
    lines.append(f"  opinion values: NOT present in save's active_opinions structure (owner/target only) — not reported")
    lines.append("")
    return "\n".join(lines)


# ============================================================
# استخراج جنگ، ارتش، شورا و دربار (مرحلهٔ ۴) — فقط Parser ساختاری
# ============================================================

SENTINEL_NONE = 4294967295  # اسلات/مرجع خالی در سیو — هرگز یک ID واقعی نیست


def _no_sentinel(value):
    """Sentinel سیو (4294967295) یعنی «خالی» — باید missing شود، نه ID و نه صفر."""
    if value == SENTINEL_NONE:
        return None
    return value


def _clean_war_name(raw):
    """نام جنگ در سیو با مارک‌آپ UI آلوده است (ONCLICK/TOOLTIP/کاراکتر کنترلی).
    خروجی: نام پاک‌شده برای نمایش + مراجع قابل‌اثبات (title/character ID) از خودِ مارک‌آپ.
    مراجع از دادهٔ سیو استخراج می‌شوند — حدس نیستند."""
    import re as _re
    if raw is None:
        return None, []
    text = str(raw)
    refs = []
    for m in _re.finditer(r"(?:ONCLICK|TOOLTIP):(TITLE|CHARACTER),(\d+)", text):
        kind, ident = m.group(1).lower(), m.group(2)
        entry = {"kind": kind, "id": int(ident)}
        if entry not in refs:
            refs.append(entry)
    cleaned = text.replace("\x15", " ")
    cleaned = _re.sub(r"(?:ONCLICK|TOOLTIP):[A-Z_]+,[A-Za-z_0-9]+", " ", cleaned)
    cleaned = _re.sub(r"[\x00-\x1f]", " ", cleaned)
    cleaned = _re.sub(r"(?<![A-Za-z])[LE](?![A-Za-z])", " ", cleaned)  # line-pick marker
    cleaned = cleaned.replace(";", " ").replace("!", " ")
    cleaned = _re.sub(r"(?<![A-Za-z])high(?![A-Za-z])", " ", cleaned)  # colour marker
    cleaned = _re.sub(r"\s+", " ", cleaned).strip()
    return (cleaned if cleaned else None), refs


def extract_wars(root: Node) -> list:
    """جنگ‌های فعال از wars.active_wars — فقط این ساختار فعال است؛
    تاریخچهٔ جنگ شخصیت‌ها (alive_data.wars شمارنده است) اینجا خوانده نمی‌شود.
    امتیاز جنگ از ticking_war_score طرفین و battle_results قابل اثبات است."""
    active = _get_node(root, "wars", "active_wars")
    if active is None or active.kind != "block":
        return []
    out = []
    for wid, w in active.children.items():
        if w is None or w.kind != "block":
            continue  # ورودی‌های 'none' = جنگ‌های حذف‌شده، نه جنگ فعال
        def side(node, role):
            if node is None or node.kind != "block":
                return None
            participants = []
            p = node.children.get("participants")
            if p is not None:
                for item in p.children:
                    if item is None or item.kind != "block":
                        continue
                    ch = item.children.get("character")
                    if ch is None:
                        continue
                    contrib = item.children.get("contribution")
                    participants.append({
                        "character": ch.value,
                        "contribution": [x.value for x in contrib.children] if contrib is not None and contrib.kind == "list" else None,
                    })
            score = _scalar_val(node.children.get("ticking_war_score"))
            return {
                "participants": participants,
                "ticking_war_score": score,
            }
        # primary attacker/defender از casus_belli (با فیلتر sentinel — خالی ≠ ID)
        cb = w.children.get("casus_belli")
        cb_att = _no_sentinel(_scalar_val(cb.children.get("attacker"))) if cb is not None else None
        cb_def = _no_sentinel(_scalar_val(cb.children.get("defender"))) if cb is not None else None
        name_raw = _scalar_val(w.children.get("name"))
        name_clean, name_refs = _clean_war_name(name_raw)
        attacker = side(w.children.get("attacker"), "attacker")
        defender = side(w.children.get("defender"), "defender")
        battles = []
        br = w.children.get("battle_results")
        if br is not None and br.kind == "list":
            for item in br.children:
                if item is None or item.kind != "block":
                    continue
                battles.append({
                    "province": _scalar_val(item.children.get("province")),
                    "war_score": _scalar_val(item.children.get("war_score")),
                    "attacker_won": _scalar_val(item.children.get("attacker_won")),
                })
        scores = [b["war_score"] for b in battles if isinstance(b["war_score"], (int, float))]
        out.append({
            "war_id": wid,
            "attacker": attacker,
            "defender": defender,
            "casus_belli": _scalar_val(cb.children.get("type")) if cb is not None else None,
            "cb_attacker": cb_att,
            "cb_defender": cb_def,
            "cb_claimant": _no_sentinel(_scalar_val(cb.children.get("claimant"))) if cb is not None else None,
            "start_date": _scalar_val(w.children.get("start_date")),
            "name_raw": name_raw,
            "name": name_clean,
            "name_refs": name_refs,
            "battles": battles,
            "war_score_sum": round(sum(scores), 3) if scores else None,
        })
    return out


def extract_military(root: Node, player_id) -> dict:
    """نیروی بازیکن: levies از landed_data؛ regiments از armies.regiments با owner دقیق؛
    knights فقط از شناسه‌های واقعی list (شمارش داخل block ممنوع).
    rally_points از played_character.rally_points (بلوک‌های province/color) — قابل‌اثبات.
    موقعیت ارتش: armies.armies.<id> با unit=<ref> به units.<ref> (location/owner/path) وصل می‌شود؛
    ارتشِ بازیکن = بلوکی که name.owner == player_id (رف مالک داخل name) یا commander == player_id.
    هر فیلد غایب None می‌ماند (missing ≠ صفر) — ارتش بدون رِف unit، بدون موقعیت گزارش می‌شود."""
    pid = str(player_id)
    living = root.children.get("living")
    pblock = living.children.get(pid) if living is not None else None
    out = {
        "current_strength": None, "total_strength": None, "levy": None,
        "regiments": [], "knights": [], "commanders": [], "rally_points": [], "armies": [],
    }
    if pblock is not None:
        ld = pblock.children.get("landed_data")
        if ld is not None:
            out["current_strength"] = _scalar_val(ld.children.get("current_strength"))
            out["total_strength"] = _scalar_val(ld.children.get("strength"))
            out["levy"] = _scalar_val(ld.children.get("levy"))
        pd = pblock.children.get("playable_data")
        if pd is not None:
            kn = pd.children.get("knights")
            if kn is not None and kn.kind == "list":
                out["knights"] = [x.value for x in kn.children]  # فقط شناسه‌های واقعی
    reg = _get_node(root, "armies", "regiments")
    if reg is not None and reg.kind == "block":
        for rk, r in reg.children.items():
            if r is None or r.kind != "block":
                continue
            owner = r.children.get("owner")
            if owner is None or str(owner.value) != str(player_id):
                continue
            out["regiments"].append({
                "regiment_id": rk,
                "type": _scalar_val(r.children.get("type")),
                "size": _scalar_val(r.children.get("size")),
                "max": _scalar_val(r.children.get("max")),
                "origin": _scalar_val(r.children.get("origin")),
                "source": _scalar_val(r.children.get("source")),
            })
    # rally points بازیکن — played_character.rally_points: list از {province, color}
    pc = root.children.get("played_character")
    rp = pc.children.get("rally_points") if pc is not None else None
    if rp is not None and rp.kind == "list":
        for item in rp.children:
            if item is None or item.kind != "block":
                continue
            out["rally_points"].append({
                "province": _scalar_val(item.children.get("province")),
                "color": _scalar_val(item.children.get("color")),
            })
    # موقعیت ارتش‌ها: join armies.armies → units (مسیر ساختاری، بدون regex)
    armies_outer = _get_node(root, "armies")
    armies_node = armies_outer.children.get("armies") if armies_outer is not None and armies_outer.kind == "block" else None
    units_node = _get_node(root, "units")
    gathering_node = armies_outer.children.get("gathering_armies") if armies_outer is not None and armies_outer.kind == "block" else None
    if armies_node is not None and armies_node.kind == "block":
        for ak, a in armies_node.children.items():
            if a is None or a.kind != "block":
                continue
            name_node = a.children.get("name")
            name_owner = _scalar_val(name_node.children.get("owner")) if name_node is not None and name_node.kind == "block" else None
            commander = _scalar_val(a.children.get("commander"))
            is_player_army = (
                (name_owner is not None and str(name_owner) == pid)
                or (commander is not None and str(commander) == pid)
            )
            if not is_player_army:
                continue
            entry = {
                "army_id": ak,
                "commander": commander,
                "name_owner": name_owner,
                "unit": _no_sentinel(_scalar_val(a.children.get("unit"))),
                "location": None, "movement_path": None, "arrival_date": None,
                "gathering": None, "unit_location_missing": False,
            }
            unit_ref = entry["unit"]
            if unit_ref is not None and units_node is not None and units_node.kind == "block":
                u = units_node.children.get(str(unit_ref))
                if u is not None and u.kind == "block":
                    loc = _scalar_val(u.children.get("location"))
                    if loc is None:
                        entry["unit_location_missing"] = True
                    entry["location"] = loc
                    path_n = u.children.get("path")
                    if path_n is not None and path_n.kind == "list":
                        entry["movement_path"] = [x.value for x in path_n.children]
                    entry["arrival_date"] = _scalar_val(u.children.get("arrival_date"))
                else:
                    entry["unit_location_missing"] = True
            elif unit_ref is None:
                entry["unit_location_missing"] = True
            if gathering_node is not None and gathering_node.kind == "list":
                entry["gathering"] = any(str(x.value) == str(ak) for x in gathering_node.children)
            out["armies"].append(entry)
    return out


def extract_council_court(root: Node, player_id) -> dict:
    """شورا و دربار: وظایف شورا فقط برای دربار بازیکن (court_owner دقیق)؛
    موقعیت‌های دربار فقط employer == بازیکن؛ تصمیم‌ها با وضعیت خام."""
    pid = str(player_id)
    out = {"council_tasks": [], "court_positions": [], "decisions": {}}
    tasks = _get_node(root, "council_task_manager", "active")
    if tasks is not None and tasks.kind == "block":
        for tid, t in tasks.children.items():
            if t is None or t.kind != "block":
                continue
            court_owner = t.children.get("court_owner")
            if court_owner is None or str(court_owner.value) != str(player_id):
                continue
            out["council_tasks"].append({
                "task_id": tid,
                "type": _scalar_val(t.children.get("type")),
                "owner": _scalar_val(t.children.get("owner")),
                "progress": _scalar_val(t.children.get("progress")),
            })
    cpdb = _get_node(root, "court_positions", "database")
    if cpdb is not None and cpdb.kind == "block":
        for cid, c in cpdb.children.items():
            if c is None or c.kind != "block":
                continue
            employer = c.children.get("employer")
            if employer is None or str(employer.value) != str(player_id):
                continue
            out["court_positions"].append({
                "position_id": cid,
                "court_position": _scalar_val(c.children.get("court_position")),
                "task_type": _scalar_val(c.children.get("task_type")),
                "employee": _scalar_val(c.children.get("employee")),
            })
    pc = root.children.get("played_character")
    dec = pc.children.get("important_decisions") if pc is not None else None
    if dec is not None and dec.kind == "block":
        for k, v in dec.children.items():
            # وضعیت خام: True/False بدون تفسیر به «قابل اجرا» یا «غیرقابل اجرا»
            out["decisions"][k] = v.value if v.kind == "scalar" else None
    return out


def extract_opinions(root: Node, player_id) -> dict:
    """نظرها بین بازیکن و دیگران از opinions.active_opinions — فقط ردیف‌های درگیرِ بازیکن.

    ساختار سیو: هر ردیف {owner, target, temporary_opinion*، scripted_relations?}؛
    owner صاحبِ نظر است و target موضوع آن. چند temporary_opinion هم‌نام در یک ردیف
    ممکن است (get_all الزامی — اولین کافی نیست). direction مشخص می‌کند بازیکن
    صاحبِ نظر است یا موضوع آن. جمعِ نظر = مجموع value فیلدهای temporary_opinion
    فقط وقتی همه عددند؛ بدون temporary، جمع None می‌ماند (missing ≠ صفر —
    رابطهٔ scripted بدون عدد هم missing است، نه صفر). modifier/reason خام می‌مانند.
    """
    op_root = _get_node(root, "opinions", "active_opinions")
    out = {"opinions": [], "total": 0}
    if op_root is None:
        return out
    if op_root.kind == "list":
        rows = list(op_root.children or [])
    elif op_root.kind == "block":
        rows = list((op_root.children or {}).values())
    else:
        rows = []
    pid = str(player_id)
    for row in rows:
        if row is None or row.kind != "block":
            continue
        out["total"] += 1
        owner = _scalar_val(row.children.get("owner"))
        target = _no_sentinel(_scalar_val(row.children.get("target")))
        owner_is_player = owner is not None and str(owner) == pid
        target_is_player = target is not None and str(target) == pid
        if not (owner_is_player or target_is_player):
            continue
        temps = []
        for t in row.get_all("temporary_opinion"):
            if t is None or t.kind != "block":
                continue
            temps.append({
                "modifier": _scalar_val(t.children.get("modifier")),
                "value": _scalar_val(t.children.get("value")),
                "expiration_date": _scalar_val(t.children.get("expiration_date")),
            })
        total = None
        if temps and all(isinstance(t["value"], (int, float)) for t in temps):
            total = round(sum(t["value"] for t in temps), 2)
        scripted = []
        sr = row.children.get("scripted_relations")
        if sr is not None and sr.kind == "block":
            # ساختار سیو: scripted_relations={ friend={flags, reason} , rival={...} } —
            # کلیدِ سطح اول، نوع رابطه است (نه عضو بی‌نام)
            for kind_key, sblock in sr.children.items():
                if sblock is None or sblock.kind != "block":
                    continue
                scripted.append({
                    "kind": kind_key,
                    "reason": _scalar_val(sblock.children.get("reason")),
                    "involved_character": _no_sentinel(_scalar_val(sblock.children.get("involved_character"))),
                })
        elif sr is not None and sr.kind == "list":
            for s in sr.children:
                if s is None or s.kind != "block":
                    continue
                for kind_key, sblock in s.children.items():
                    if sblock is None or sblock.kind != "block":
                        continue
                    scripted.append({
                        "kind": kind_key,
                        "reason": _scalar_val(sblock.children.get("reason")),
                        "involved_character": _no_sentinel(_scalar_val(sblock.children.get("involved_character"))),
                    })
        direction = "both" if (owner_is_player and target_is_player) else (
            "held_by_player" if owner_is_player else "about_player")
        out["opinions"].append({
            "owner": owner,
            "target": target,
            "direction": direction,
            "temporary": temps,
            "total": total,
            "scripted_relations": scripted,
        })
    return out


def build_war_military_report(wars: list, military: dict, council: dict, opinions_data: dict = None) -> str:
    """گزارش بخش جنگ/ارتش/شورا (مرحلهٔ ۴) — به انتهای گزارش اضافه می‌شود."""
    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("WARS, MILITARY & COURT (Stage 4)")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"--- Active Wars ({len(wars)}) ---")
    lines.append("  note: from wars.active_wars only; character war history (alive_data.wars) is a counter, NOT war ids")
    pid_s = str(military.get("player_id")) if military.get("player_id") is not None else None
    for w in wars:
        att, dfe = w.get("attacker") or {}, w.get("defender") or {}
        cb_a, cb_d = w.get("cb_attacker"), w.get("cb_defender")
        involves = pid_s is not None and (str(cb_a) == pid_s or str(cb_d) == pid_s)
        inv = "  <-- involves player" if involves else ""
        lines.append(f"  war {w.get('war_id')}: cb={w.get('casus_belli')} att={w.get('cb_attacker')} "
                     f"def={w.get('cb_defender')} start={w.get('start_date')} "
                     f"score(att tick={att.get('ticking_war_score')}, def tick={dfe.get('ticking_war_score')}, "
                     f"battles sum={w.get('war_score_sum')}){inv}")
    lines.append("")
    lines.append("--- Military (player) ---")
    lines.append(f"  current_strength={military.get('current_strength')} total_strength={military.get('total_strength')} levy={military.get('levy')}")
    regs = military.get("regiments", [])
    lines.append(f"  Men-at-Arms regiments: {len(regs)}")
    for r in regs:
        lines.append(f"    {r.get('type')}: size={r.get('size')} max={r.get('max')} source={r.get('source') or 'maa'}")
    lines.append(f"  knights (real id list): {len(military.get('knights', []))} -> {military.get('knights')}")
    rps = military.get("rally_points", [])
    if rps:
        lines.append(f"  rally points: {len(rps)} -> " + ", ".join(f"province {r.get('province')}" for r in rps))
    else:
        lines.append("  rally points: none in played_character.rally_points")
    armies = military.get("armies", [])
    lines.append(f"  player armies (armies.armies join units): {len(armies)}")
    for a in armies:
        loc = a.get("location") if a.get("location") is not None else "unknown"
        gath = " [gathering]" if a.get("gathering") else ""
        lines.append(f"    army {a.get('army_id')}: commander={a.get('commander')} location={loc}{gath}")
        path = a.get("movement_path")
        if path:
            lines.append(f"      moving via: {' -> '.join(str(p) for p in path)} (arrival {a.get('arrival_date')})")
    lines.append("")
    lines.append("--- Council & Court ---")
    lines.append(f"  council tasks (player's court): {len(council.get('council_tasks', []))}")
    for t in council.get("council_tasks", []):
        lines.append(f"    {t.get('type')} owner={t.get('owner')} progress={t.get('progress')}")
    lines.append(f"  court positions (player's court): {len(council.get('court_positions', []))}")
    for c in council.get("court_positions", []):
        lines.append(f"    {c.get('court_position')} task={c.get('task_type')} employee={c.get('employee')}")
    dec = council.get("decisions", {})
    lines.append(f"  decisions (raw flags — 'no' NOT reported as available): {len(dec)}")
    for k, v in dec.items():
        lines.append(f"    {k} = {v}")
    lines.append("")
    ops = (opinions_data or {}).get("opinions", [])
    lines.append(f"--- Opinions involving player (of {(opinions_data or {}).get('total', 0)} opinion rows) ---")
    if ops:
        for o in ops:
            other = o.get("target") if o.get("direction") == "held_by_player" else o.get("owner")
            lines.append(f"    char {other} ({o.get('direction')}): total={o.get('total')}"
                         + (" " + ", ".join(s.get("kind") for s in o.get("scripted_relations", [])) if o.get("scripted_relations") else ""))
            for t in o.get("temporary", []):
                lines.append(f"      {t.get('modifier')}: {t.get('value')} (until {t.get('expiration_date')})")
    else:
        lines.append("    none")
    lines.append("")
    return "\n".join(lines)


def build_state_json(root: Node, player: dict, characters: dict, vassals: list,
                     factions: list, faith_culture: dict, succession: dict,
                     domain: list, counties: list, provinces: list,
                     wars: list, military: dict, council: dict,
                     schemes_data: dict, secrets_data: dict, relations_data: dict, 
                     dynasties_data: dict, artifacts_data: dict, opinions_data: dict,
                     meta: dict) -> dict:
    """خروجی machine-readable نهایی — reports/state_report.json؛
    هر بخش با شاخص کیفیت: missing/unmapped/منبع داده/زمان."""
    import time as _time
    import os as _os
    meta_out = dict(meta) if meta else {}
    if meta_out.get("save_file"):
        meta_out["save_file"] = _os.path.basename(str(meta_out["save_file"]))  # بدون افشای مسیر
    tl = root.children.get("traits_lookup")
    if tl is not None and tl.kind == "list":
        # نام صفت با اندیس: traits_lookup[trait_id] — از دادهٔ خود سیو، بدون حدس
        meta_out["traits_lookup"] = [x.value for x in tl.children]
    out = {
        "meta": meta_out,
        "player": player,
        "domain": domain,
        "counties": counties,
        "holdings": provinces,
        "characters": list(characters.values()),
        "vassals": vassals,
        "factions": factions,
        "succession": succession,
        "wars": wars,
        "military": military,
        "court": council,
        "schemes": schemes_data.get("schemes", []),
        "secrets": secrets_data.get("secrets", []),
        "relations": relations_data.get("relations", []),
        "dynasty": dynasties_data.get("dynasty", {}),
        "artifacts": artifacts_data.get("artifacts", []),
        "opinions": opinions_data.get("opinions", []),
        "quality": {},
    }
    mapped_chars = [c for c in characters.values() if c.get("mapped")]
    missing_fields = []
    for c in counties:
        for f in ("development", "county_control", "culture", "faith"):
            if c.get(f) is None:
                missing_fields.append(f"county.{f}:{c.get('county_key')}")
    for p in provinces:
        if p.get("holding_type") is None:
            missing_fields.append(f"holding.holding_type:{p.get('province_id')}")
        if p.get("income") is None:
            missing_fields.append(f"holding.income:{p.get('province_id')}")
    if player.get("faith") is None:
        missing_fields.append("player.faith")
    unmapped_ids = []
    for c in characters.values():
        if not c.get("mapped"):
            unmapped_ids.append(f"character:{c.get('id')}")
    for v in vassals:
        if not v.get("mapped"):
            unmapped_ids.append(f"vassal_contract:{v.get('contract_id')}")
    unmapped_ids.extend(
        f"faction_leader:{f.get('leader')}" for f in factions
        if f.get("leader") is not None
        and not any(ch.get("mapped") and ch.get("id") == f.get("leader") for ch in mapped_chars)
    )
    warnings = []
    if succession.get("first_in_line") is None:
        warnings.append("succession.first_in_line not provable from save data")
    if not faith_culture.get("player_faith_available"):
        warnings.append("player faith not stored in this save format; faith mismatches incomputable")
    for f in factions:
        if f.get("power_over_threshold") is None:
            warnings.append(f"faction {f.get('faction_id')}: power_threshold missing; danger not provable")
            break
    out["quality"] = {
        "save_file_name": meta_out.get("save_file"),
        "extraction_time": _time.strftime("%Y-%m-%d %H:%M:%S"),
        "missing_fields": missing_fields,
        "missing_counts": {
            "schemes_missing_type": schemes_data.get("missing_type", 0),
            "artifacts_missing_owner": artifacts_data.get("missing_owner", 0),
        },
        "unmapped_ids": unmapped_ids,
        "warnings": warnings,
        "counts": {
            "root_unique_names": len(root.children),
            "domain_titles": len(domain),
            "domain_count": sum(1 for d in domain if d.get("is_county") and d.get("mapped")),
            "counties": len(counties),
            "counties_world": getattr(extract_counties, "world_total", None),
            "development_world_avg": getattr(extract_counties, "world_dev_avg", None),
            "control_world_avg": getattr(extract_counties, "world_ctrl_avg", None),
            "holdings": len(provinces),
            "characters_mapped": len(mapped_chars),
            "characters_unmapped": len(characters) - len(mapped_chars),
            "vassal_contracts": len(vassals),
            "factions": len(factions),
            "active_wars": len(wars),
            "maa_regiments": len(military.get("regiments", [])),
            "knights": len(military.get("knights", [])),
            "player_armies": len(military.get("armies", [])),
            "rally_points": len(military.get("rally_points", [])),
            "player_opinions": len(opinions_data.get("opinions", [])),
            "opinions_total": opinions_data.get("total", 0),
            "council_tasks": len(council.get("council_tasks", [])),
            "court_positions": len(council.get("court_positions", [])),
            "schemes_total": schemes_data.get("total", 0),
            "secrets_total": secrets_data.get("total", 0),
            "relations_total": relations_data.get("total", 0),
            "dynasties_total": dynasties_data.get("total", 0),
            "artifacts_total": artifacts_data.get("total", 0),
        },
        "sources": {
            "player": "living/<pid> via played_character.character",
            "domain": "landed_data.domain via landed_titles",
            "counties": "county_manager + landed_titles (row data: player domain; world stats in counts)",
            "holdings": "provinces (domain-capital filtered)",
            "characters": "living + dead_unprunable (alive status from block location)",
            "vassals": "vassal_contracts.database via landed_data.vassal_contracts",
            "factions": "faction_manager.factions",
            "succession": "landed_data.laws + stored landed_data.succession line",
            "wars": "wars.active_wars (active only)",
            "military": "landed_data levies + armies.regiments(owner) + playable_data.knights + played_character.rally_points + armies.armies→units join",
            "court": "council_task_manager.active(court_owner) + court_positions.database(employer) + played_character.important_decisions",
            "opinions": "opinions.active_opinions (rows where player is owner or target)",
            "schemes": "schemes.active",
            "secrets": "secrets.secrets",
            "relations": "relations.active_relations",
            "dynasty": "dynasties.dynasties",
            "artifacts": "artifacts.artifacts",
        }
    }
    return out


def save_state_snapshot(state_json: dict, reports_dir: str = REPORTS_DIR) -> str:
    """فاز ۱ — ذخیرهٔ اسنپ‌شات وضعیت در reports/history/ (خوراک تحلیل‌گر روند).

    نام فایل فقط از game_date ساخته می‌شود (snapshot_<game_date>.json) تا re-extract
    همان سیو روی همان فایل بنویسد و هر سیو تازه (تاریخ جدید) فایل جدید بسازد.
    اگر game_date در سیو نباشد، اسنپ‌شات نوشته نمی‌شود و مسیر خالی برمی‌گردد —
    بدون ساخت فایل بی‌نام. هرگز exception بالا نمی‌دهد.
    """
    try:
        import json as _sj
        import time as _st
        raw = (state_json.get("meta") or {}).get("game_date")
        if not isinstance(raw, str) or not raw.strip():
            return ""
        stamp = raw.replace(".", "_").replace(":", "_").replace(" ", "_")
        if not stamp:
            return ""
        hist = os.path.join(reports_dir, "history")
        os.makedirs(hist, exist_ok=True)
        out = os.path.join(hist, "snapshot_%s.json" % stamp)
        with open(out, "w", encoding="utf-8") as f:
            _sj.dump(state_json, f, ensure_ascii=False, indent=1)
        return out
    except Exception:
        return ""


def _find_block(text: str, needle: str, from_pos: int = 0) -> str:
    start = text.find(needle, from_pos)
    if start < 0:
        return ""
    brace = text.find("{", start)
    if brace < 0:
        return ""
    depth = 0
    i = brace
    n = len(text)
    while i < n:
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[brace:i + 1]
        i += 1
    return text[brace:]


def _first(pattern: str, block: str):
    m = re.search(pattern, block)
    return m.group(1) if m else None


def _int_list(pattern: str, block: str):
    m = re.search(pattern, block, re.S)
    if not m:
        return []
    return [int(x) for x in re.findall(r"-?\d+", m.group(1))]


def _name_list(pattern: str, block: str):
    m = re.search(pattern, block, re.S)
    if not m:
        return []
    return m.group(1).split()


def melt_save(save_path: str) -> str:
    if not os.path.exists(RAKALY):
        raise FileNotFoundError("rakaly پیدا نشد: " + RAKALY)
    if not os.path.exists(save_path):
        raise FileNotFoundError("فایل ذخیره پیدا نشد: " + save_path)
    cmd = [RAKALY, "melt", save_path, "-u", "stringify", "-c"]
    proc = subprocess.run(cmd, capture_output=True, timeout=180)
    if proc.returncode != 0 and not proc.stdout:
        raise RuntimeError("خطای rakaly: " + proc.stderr.decode("utf-8", "replace")[:500])
    return proc.stdout.decode("utf-8", "replace")


def extract_state(text: str) -> dict:
    st: dict = {}
    st["date"] = _first(r"meta_date=([0-9.]+)", text) or "?"
    st["player_name"] = _fix_persian(_first(r'meta_player_name="([^"]*)"', text) or "?")
    st["title_name"] = _fix_persian(_first(r'meta_title_name="([^"]*)"', text) or "?")
    st["house_name"] = _fix_persian(_first(r'meta_house_name="([^"]*)"', text) or "?")
    st["tier"] = int(_first(r"meta_player_tier=(\d+)", text) or "0")

    m_p = re.search(r'played_character=\{\s*name="[^"]*"\s*character=(\d+)', text)
    if not m_p:
        st["error"] = "شناسهٔ کاراکتر بازیکن در سیو یافت نشد."
        return st
    pid = m_p.group(1)
    st["player_id"] = pid

    # پیدا کردن بلوک واقعی کاراکتر بازیکن
    m_block = re.search(r'\n(\t*)' + pid + r'=\{\s*\n\t*first_name=.*?(?=\n\1\d+=\{\s*\n\t*first_name=|\Z)', text, re.DOTALL)
    if not m_block:
        m_block = re.search(r'\n' + pid + r'=\{\s*\n\t*first_name=.*?(?=\n\d+=\{\s*\n\t*first_name=|\Z)', text, re.DOTALL)
    if not m_block:
        st["error"] = "بلوک کاراکتر بازیکن در فایل سیو یافت نشد."
        return st

    block = m_block.group(0)
    alive = _find_block(block, "alive_data={")
    landed = _find_block(block, "landed_data={")
    playable = _find_block(block, "playable_data={")

    st["first_name"] = _first(r'first_name="?([^"\s\n]+)"?', block) or "?"
    birth = _first(r"birth=([0-9.]+)", block)
    st["birth"] = birth
    st["age"] = None
    if birth and st["date"] != "?":
        try:
            by, bm, bd = (int(x) for x in birth.split("."))
            dy, dm, dd = (int(x) for x in st["date"].split("."))
            age = dy - by
            if (dm, dd) < (bm, bd):
                age -= 1
            st["age"] = age
        except Exception:
            st["age"] = None

    skills = _int_list(r"skill=\{\s*([^\}]+)\}", block)
    skill_names = ["دیپلماسی", "نظامی", "مباشرت", "توطئه", "دانش", "دلاوری"]
    st["skills"] = {skill_names[i]: skills[i] for i in range(min(len(skills), 6))}

    tl_block = _find_block(text, "traits_lookup=")
    trait_names = tl_block.strip("{} \n\t").split() if tl_block else []
    trait_ids = _int_list(r"traits=\{\s*([^\}]+)\}", block)
    st["traits"] = [trait_names[t].replace("_", " ") for t in trait_ids if 0 <= t < len(trait_names)]

    # همسران
    spouses = re.findall(r'\bspouse=(\d+)', block)
    st["spouse_ids"] = list(set(spouses))
    st["spouse_count"] = len(st["spouse_ids"])
    st["primary_spouse"] = _first(r"primary_spouse=(\d+)", block)
    st["betrothed"] = re.findall(r'\bbetrothed=(\d+)', block)

    # فرزندان و جنسیت دقیق
    children_match = re.search(r'child=\{\s*([^\}]+)\}', block)
    st["children"] = []
    st["sons_count"] = 0
    st["daughters_count"] = 0
    if children_match:
        for cid in children_match.group(1).split():
            cm = re.search(r'\n(\t*)' + cid + r'=\{\s*\n\t*first_name="?([^"\s\n]+)"?.*?(?=\n\1\d+=\{\s*\n\t*first_name=|\Z)', text, re.DOTALL)
            if cm:
                c_body = cm.group(0)
                cname = re.search(r'first_name="?([^"\s\n]+)"?', c_body).group(1)
                cbirth = re.search(r'birth=([0-9.]+)', c_body)
                is_female = bool(re.search(r'\bfemale=yes\b', c_body[:350]))
                gender_str = "دختر" if is_female else "پسر (وارث)"
                if is_female:
                    st["daughters_count"] += 1
                else:
                    st["sons_count"] += 1
                st["children"].append({
                    "id": cid,
                    "name": cname,
                    "birth": cbirth.group(1) if cbirth else "?",
                    "is_female": is_female,
                    "gender": gender_str
                })
    st["children_count"] = len(st["children"])

    # آمار مالی و روانی
    st["stress"] = _first(r"\bstress=(-?[\d.]+)", alive) or "0"
    st["fertility"] = _first(r"\bfertility=(-?[\d.]+)", alive)
    st["health"] = _first(r"\bhealth=(-?[\d.]+)", alive)
    st["gold"] = _first(r"gold=\{\s*\n\s*value=(-?[\d.]+)", alive) or "0"
    st["piety"] = _first(r"piety=\{\s*\n\s*currency=(-?[\d.]+)", alive) or "0"
    st["prestige"] = _first(r"prestige=\{\s*\n\s*currency=(-?[\d.]+)", alive) or "0"
    st["focus"] = _first(r'focus=\{\s*\n\s*type="?([^\s\"\n]+)"?', alive)
    st["perks"] = _name_list(r"perk=\{\s*([^\}]+)\}", alive)
    st["modifiers"] = re.findall(r'modifier=([a-zA-Z0-9_]+)', alive)

    # ادعاها
    claims_raw = re.findall(r'title=(\d+)\s*\n\t*pressed=(yes|no)', block)
    st["claims"] = []
    st["claims_pressed_count"] = 0
    for tid, pressed in claims_raw:
        if pressed == "yes":
            st["claims_pressed_count"] += 1
        tm = re.search(r'\n' + tid + r'=\{\s*\n\t*key="?([^\s\"\n]+)"?', text)
        tkey = tm.group(1) if tm else f"Title_{tid}"
        fa_name = TITLE_TRANSLATIONS.get(tkey, tkey)
        st["claims"].append({
            "id": tid,
            "key": tkey,
            "name": fa_name,
            "pressed": pressed == "yes"
        })

    # استخراج دقیق قلمرو مستقیم (فقط شهرستان‌ها c_...)
    domain_ids = _int_list(r"domain=\{\s*([^\}]+)\}", landed)
    st["domain_ids"] = domain_ids
    st["domain_limit"] = int(_first(r"\bdomain_limit=(\d+)", landed) or "6")

    st["counties"] = []
    st["holdings_detail"] = []
    for did in domain_ids:
        # جستجوی کلید عنوان
        p = text.find(f'\n{did}={{')
        if p >= 0:
            chunk = text[p:p+300]
            m_key = re.search(r'key=([^\s\n]+)', chunk)
            if m_key:
                tkey = m_key.group(1).strip('"')
                fa = TITLE_TRANSLATIONS.get(tkey, tkey)
                # فقط شهرستان‌ها به عنوان اسلات قلمرو شمرده می‌شوند
                if tkey.startswith("c_"):
                    st["counties"].append((tkey, fa))

    st["domain_count"] = len(st["counties"])

    # قوانین، سپاه و قدرت
    laws_block = _find_block(landed, "laws={")
    st["laws"] = re.findall(r'(\w+)', laws_block.strip("{} \n\t")) if laws_block else []
    st["current_strength"] = _first(r"\bcurrent_strength=(\d+)", landed) or "0"
    st["strength"] = _first(r"\bstrength=(\d+)", landed) or "0"
    st["levy"] = _first(r"\blevy=(\d+)", landed) or "0"
    st["balance"] = _first(r"\bbalance=(-?[\d.]+)", landed) or "0"
    st["income"] = _first(r"\bincome=(-?[\d.]+)", alive) or st["balance"]
    st["government"] = _first(r'government="?([^\s\"\n]+)"?', landed) or "clan_government"
    st["vassal_power_value"] = _first(r"\bvassal_power_value=(-?[\d.]+)", landed) or "0"
    st["vassal_count"] = len(_int_list(r"vassal_contracts=\{\s*([^\}]+)\}", landed))
    st["active_wars"] = _int_list(r"wars=\{\s*([^\}]+)\}", landed)

    knight_block = _find_block(playable, "knights={")
    st["knights_count"] = len(re.findall(r"\d+", knight_block)) if knight_block else 0
    st["legitimacy"] = _first(r"legitimacy=([\d.]+)", playable)

    return st


def build_report(st: dict) -> str:
    if st.get("error"):
        return f"❌ خطای دیوان: {st['error']}"

    lines = []
    lines.append("📜 [دیوان عالی بخارا - گزارش جامع و دقیق وضعیت قلمرو]")
    lines.append("======================================================")
    lines.append(f"📅 تاریخ بازی: {st['date']}")
    tier = TIER_FA.get(st.get("tier", 0), "امیر")
    lines.append(f"👤 حاکم: {st['player_name']} (شناسه: {st['player_id']}) — رتبه: {tier} — عنوان: {st['title_name']} — خانه: {st['house_name']}")
    if st.get("age") is not None:
        lines.append(f"🎂 سن: {st['age']} سال (متولد {st['birth']})")
    if st.get("legitimacy"):
        lines.append(f"👑 مشروعیت: {float(st['legitimacy']):.1f}")

    lines.append("\n💰 [۱. وضعیت مالی و خزانه‌داری]")
    lines.append("------------------------------------------------------")
    gold_val = float(st.get("gold", 0))
    lines.append(f"🪙 موجودی خزانه: {gold_val:.1f} سکه طلا")
    lines.append(f"📈 درآمد ناخالص: +{float(st.get('income', 0)):.2f}  |  سود خالص ماهانه: +{float(st.get('balance', 0)):.2f}")
    lines.append(f"🕋 تقوا (Piety): {float(st.get('piety', 0)):.1f}  |  📯 آبرو (Prestige): {float(st.get('prestige', 0)):.1f}")
    if st.get("focus"):
        lines.append(f"🎯 تمرکز سبک زندگی: {st['focus'].replace('_', ' ')}")
    if st.get("perks"):
        lines.append(f"✨ پرک‌های فعال ({len(st['perks'])}): " + "، ".join(st["perks"]))

    lines.append("\n🏰 [۲. مدیریت قلمرو و املاک مستقیم]")
    lines.append("------------------------------------------------------")
    limit = st.get("domain_limit", 6)
    count = st.get("domain_count", 0)
    over_warn = " ⚠️ تجاوز از سقف قلمرو!" if count > limit else f" (ظرفیت خالی: {limit - count} ولایت 🎯)"
    c_names = "، ".join(fa for _, fa in st.get("counties", [])) or "فاقد شهرستان"
    lines.append(f"🏰 ولایات مستقیم: {count} از {limit}{over_warn}  [{c_names}]")
    lines.append(f"🧑‍🤝‍🧑 تعداد رعایا: {st.get('vassal_count', 0)} نفر  |  قدرت رعایا: {float(st.get('vassal_power_value', 0)):.1f}")

    lines.append("\n🛡 [۳. نیروهای مسلح و جنگ]")
    lines.append("------------------------------------------------------")
    lines.append(f"🛡 نیروی نظامی آماده: {st.get('current_strength', 0)} نفر (سربازان وظیفه: {st.get('levy', 0)})")
    lines.append(f"⚔️ تعداد شوالیه‌ها: {st.get('knights_count', 0)} نفر")
    active_w = st.get("active_wars", [])
    lines.append(f"🚩 جنگ فعال: {'بله (' + str(len(active_w)) + ' نبرد)' if active_w else 'خیر (در حالت صلح)'}")
    if st.get("modifiers"):
        lines.append("🎖 وضعیت‌های نظامی فعال: " + "، ".join(st["modifiers"]))

    # ادعاهای برتر
    pressed_claims = [c for c in st.get("claims", []) if c["pressed"]]
    if pressed_claims:
        top_c = "، ".join(f"{c['name']} ({c['key']})" for c in pressed_claims[:5])
        lines.append(f"🗡 ادعاهای فشرده قانونی ({len(pressed_claims)} مورد): {top_c}")

    lines.append("\n🩸 [۴. خانواده، همسران و خط جانشینی]")
    lines.append("------------------------------------------------------")
    sp_count = st.get("spouse_count", 0)
    lines.append(f"💍 تعداد همسران: {sp_count} (سقف شرعی تکمیل)")

    sons = st.get("sons_count", 0)
    daughters = st.get("daughters_count", 0)
    lines.append(f"👶 فرزندان ({st.get('children_count', 0)} نفر): 👑 {sons} فرزند پسر (وارث مستقیم)  |  👧 {daughters} فرزند دختر")
    if st.get("children"):
        c_list_str = "، ".join(f"{c['name']} ({c['gender']})" for c in st["children"])
        lines.append(f"   • اسامی فرزندان: {c_list_str}")

    if st.get("laws"):
        lines.append("📜 قوانین حکومت و ارث: " + "، ".join(st["laws"]))
    lines.append(f"😖 استرس: {st.get('stress', '0')}  |  ❤️ سلامت: {float(st.get('health', 4.0)):.2f}")
    if st.get("skills"):
        s_text = "  |  ".join(f"{k}: {v}" for k, v in st["skills"].items())
        lines.append(f"🏹 مهارت‌ها: {s_text}")

    lines.append("======================================================")
    return "\n".join(lines)


def get_latest_save() -> str:
    """جدیدترین سیوی که autosave_exit نباشد؛ اگر فقط autosave_exit موجود باشد '' برمی‌گردد."""
    if not os.path.isdir(SAVE_DIR):
        return ""
    saves = [f for f in os.listdir(SAVE_DIR) if f.lower().endswith(".ck3")]
    saves.sort(key=lambda f: os.path.getmtime(os.path.join(SAVE_DIR, f)), reverse=True)
    filtered = _autosave_filtered(saves)
    return filtered[0] if filtered else ""


def cmd_list() -> int:
    if not os.path.isdir(SAVE_DIR):
        print("پوشهٔ سیو پیدا نشد:", SAVE_DIR)
        return 1
    saves = [f for f in os.listdir(SAVE_DIR) if f.lower().endswith(".ck3")]
    saves.sort(key=lambda f: os.path.getmtime(os.path.join(SAVE_DIR, f)), reverse=True)
    if not saves:
        print("هیچ فایلی در پوشهٔ سیو نیست.")
        return 1
    print("سیوهای موجود (جدیدترین اول؛ autosave_exit به‌صورت پیش‌فرض پیشنهاد نمی‌شود):")
    for i, f in enumerate(saves, 1):
        size = os.path.getsize(os.path.join(SAVE_DIR, f)) // (1024 * 1024)
        marker = "  (حذف‌شده از انتخاب خودکار)" if f.lower() == "autosave_exit.ck3" else ""
        print(f"  {i}. {f}  ({size} MB){marker}")
    return 0



def build_intrigue_relations_report(schemes, secrets, relations, dynasty, artifacts):
    lines = ["", "-- [5. Intrigue, Relations, Dynasty & Artifacts] --", "-"*54]
    
    sc = schemes.get("schemes", [])
    lines.append(f"  Schemes (active): {len(sc)} - missing type: {schemes.get('missing_type', 0)}")
    
    sec = secrets.get("secrets", [])
    lines.append(f"  Secrets (known): {len(sec)}")
    
    rel = relations.get("relations", [])
    lines.append(f"  Relations (family hooks/alliances): {len(rel)}")
    
    dyn = dynasty.get("dynasty", {})
    if dyn:
        lines.append(f"  Dynasty: {dyn.get('id')} - Prestige: {dyn.get('prestige')} - Head: {dyn.get('dynasty_head')}")
        
    art = artifacts.get("artifacts", [])
    lines.append(f"  Artifacts (family owned): {len(art)} - missing owner: {artifacts.get('missing_owner', 0)}")
    
    return "\n".join(lines) + "\n"

def cmd_extract(save_name: str = "") -> int:
    try:
        path = resolve_save_path(save_name) if save_name else _auto_pick_save()
    except SavePathError as e:
        print("ورودی نامعتبر:", e)
        return 1
    try:
        text = melt_save(path)
    except Exception as e:
        print("خطا در خواندن سیو:", e)
        return 1
    st = extract_state(text)
    report = build_report(st)

    # Stage 2: structural economy extraction (appended to report)
    try:
        root = parse_save(text)
        economy_domain = extract_domain(root)
        domain_c_title_ids = [d["title_id"] for d in economy_domain if d.get("is_county") and d.get("title_id")]
        domain_c_keys = [d["key"] for d in economy_domain if d.get("is_county") and d.get("key")]
        economy_counties = extract_counties(root, domain_c_title_ids)
        economy_provinces = extract_provinces(root, domain_c_keys)
        report += build_economy_report(economy_domain, economy_counties, economy_provinces)

        # Stage 3: internal politics & succession (appended to report;
        # reuses the same parsed tree — the file is parsed once per run)
        player = extract_player_and_family(root)
        fam = player.get("family", {})
        family_ids = (fam.get("children", []) + fam.get("spouses", [])
                      + fam.get("former_spouses", []))
        character_ids = list(dict.fromkeys(family_ids))
        politics_factions = extract_factions(root)
        for f in politics_factions:
            character_ids.extend(f.get("members", []))
            leader = f.get("leader")
            if leader is not None:
                character_ids.append(leader)
            sc = f.get("special_character")
            if sc is not None:
                character_ids.append(sc)
        politics_vassals = extract_vassals(root, player)
        for v in politics_vassals:
            if v.get("vassal") is not None:
                character_ids.append(v["vassal"])
        character_ids = list(dict.fromkeys(character_ids))
        politics_characters = extract_characters(root, character_ids)
        faith_culture = extract_faith_culture(root, player, politics_characters, economy_counties)
        succession = extract_succession(root, player, politics_characters)
        report += build_politics_report(player, politics_characters, politics_vassals,
                                         politics_factions, faith_culture, succession)

        # Stage 4: wars, military, council/court (appended to report;
        # same parsed tree — still a single parse per run)
        wars = extract_wars(root)
        player_id = player.get("id")
        military = extract_military(root, player_id)
        military["player_id"] = player_id
        council = extract_council_court(root, player_id)
        opinions_data = extract_opinions(root, player_id)
        report += build_war_military_report(wars, military, council, opinions_data)

        # Stage 4: machine-readable output (reports/state_report.json)
        import json as _json
        import time as _time

        # Stage 5: Intrigue, Relations, Dynasty, Artifacts
        player_family_ids = set(family_ids)
        if player.get("id") is not None:
            player_family_ids.add(player.get("id"))

        c_player = politics_characters.get(str(player.get("id"))) if politics_characters else None
        p_dyn_id = player.get("dynasty_house")
        if p_dyn_id is None and c_player is not None:
            p_dyn_id = c_player.get("dynasty_house")

        s5_schemes = extract_schemes(root, list(player_family_ids))
        s5_secrets = extract_secrets(root, list(player_family_ids))
        s5_relations = extract_relations(root, list(player_family_ids))
        s5_dynasties = extract_dynasties(root, p_dyn_id)
        s5_artifacts = extract_artifacts(root, list(player_family_ids))

        state_json = build_state_json(
            root, player, politics_characters, politics_vassals,
            politics_factions, faith_culture, succession,
            economy_domain, economy_counties, economy_provinces,
            wars, military, council,
            s5_schemes, s5_secrets, s5_relations, s5_dynasties, s5_artifacts,
            opinions_data,
            meta={
                "save_file": os.path.basename(str(path)),
                "game_date": str(root.children.get("date").value) if root.children.get("date") else None,
            },
        )
        report += build_intrigue_relations_report(s5_schemes, s5_secrets, s5_relations, s5_dynasties, s5_artifacts)
        with open(os.path.join(REPORTS_DIR, "state_report.json"), "w", encoding="utf-8") as jf:
            _json.dump(state_json, jf, ensure_ascii=False, indent=1)
        # فاز ۱: اسنپ‌شات وضعیت برای تحلیل‌گر روند (reports/history/)
        snap = save_state_snapshot(state_json)
        if snap:
            print("اسنپ‌شات وضعیت:", snap)
    except Exception as e:
        import traceback
        traceback.print_exc()  # additive extraction; never break the legacy report

    os.makedirs(REPORTS_DIR, exist_ok=True)
    out = os.path.join(REPORTS_DIR, "state_report.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(report)
    print("گزارش وضعیت:")
    print("--------")
    print(report)
    print("--------")
    print("ذخیره شد در:", out)
    if st.get("error"):
        print("خطا:", st["error"])
        return 1
    return 0


def _auto_pick_save() -> str:
    """انتخاب خودکار سیو: جدیدترین غیر-autosave؛ اگر فقط autosave_exit باشد صریحاً گزارش بده."""
    if not os.path.isdir(SAVE_DIR):
        raise SavePathError("پوشهٔ سیو پیدا نشد: " + SAVE_DIR)
    saves = [f for f in os.listdir(SAVE_DIR) if f.lower().endswith(".ck3")]
    saves.sort(key=lambda f: os.path.getmtime(os.path.join(SAVE_DIR, f)), reverse=True)
    filtered = _autosave_filtered(saves)
    if not filtered:
        if saves:
            raise SavePathError(
                "فقط autosave_exit.ck3 موجود است و به‌صورت خودکار انتخاب نمی‌شود؛ "
                "نام فایل را صریح بده."
            )
        raise SavePathError("هیچ فایل .ck3 در پوشهٔ سیو نیست.")
    return os.path.join(SAVE_DIR, filtered[0])


def cmd_melt(save_name: str = "") -> int:
    try:
        path = resolve_save_path(save_name) if save_name else _auto_pick_save()
    except SavePathError as e:
        print("ورودی نامعتبر:", e)
        return 1
    try:
        text = melt_save(path)
    except Exception as e:
        print("خطا در خواندن سیو:", e)
        return 1
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out = os.path.join(REPORTS_DIR, "melted.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print("متن ذوب‌شده ذخیره شد در:", out, f"({len(text)} نویسه)")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        return cmd_extract()
    cmd = sys.argv[1]
    arg = sys.argv[2] if len(sys.argv) >= 3 else ""
    if cmd == "list":
        return cmd_list()
    if cmd == "extract":
        return cmd_extract(arg)
    if cmd == "melt":
        return cmd_melt(arg)
    print("فرمان ناشناخته:", cmd)
    return 2


# ============================================================
# توابع استخراج مرحله ۵
def extract_schemes(root, player_family_ids):
    schemes_node = root.get("schemes")
    if not schemes_node: return {"schemes": [], "missing_type": 0, "total": 0}
    active = schemes_node.get("active")
    if not active: return {"schemes": [], "missing_type": 0, "total": 0}
    related_schemes = []
    missing_type_count = 0
    total_schemes = 0
    family_set = set(player_family_ids)
    
    def get_all_nodes(node, key):
        if not node or not node.children: return []
        res = []
        if key in node.children: res.append(node.children[key])
        if getattr(node, 'same_name', None) and key in node.same_name: res.extend(node.same_name[key])
        return res
        
    for sid, snode in active.items():
        total_schemes += 1
        owner = snode.get("owner")
        target = snode.get("target")
        stype = snode.get("type")
        
        target_id = None
        target_type = None
        if target:
            tt = target.get("type")
            ti = target.get("target")
            target_type = str(tt.value) if tt else None
            target_id = ti.as_int() if ti else None
            
        owner_id = owner.as_int() if owner else None
        
        agent_slots = []
        for ag in get_all_nodes(snode, "agent_slots"):
            char = ag.get("character")
            char_id = char.as_int() if char else None
            if char_id is not None and char_id != 4294967295:
                st = ag.get("type")
                cont = ag.get("contribution")
                agent_slots.append({
                    "type": str(st.value) if st else None,
                    "character": char_id,
                    "contribution": cont.as_float() if cont else None
                })
                
        is_related = False
        if owner_id in family_set: is_related = True
        if target_type == "character" and target_id in family_set: is_related = True
        for a in agent_slots:
            if a["character"] in family_set: is_related = True
            
        if not stype:
            missing_type_count += 1
            stype_val = "missing"
        else:
            stype_val = str(stype.value)

        if is_related:
            prog = snode.get("progress")
            secr = snode.get("secrecy")
            opps = snode.get("opportunities")
            rsc = snode.get("ramping_success_chance")
            se = snode.get("scheme_exposed")
            
            related_schemes.append({
                "id": sid,
                "type": str(stype_val),
                "target": target_id,
                "target_type": target_type,
                "owner": owner_id,
                "progress": prog.as_float() if prog else None,
                "secrecy": secr.as_float() if secr else None,
                "opportunities": opps.as_int() if opps else None,
                "ramping_success_chance": rsc.as_float() if rsc else None,
                "scheme_exposed": bool(se.as_bool() if hasattr(se, 'as_bool') and se else (se.value if se else False)),
                "agents": agent_slots
            })
            
    return {"schemes": related_schemes, "missing_type": missing_type_count, "total": total_schemes}

def extract_secrets(root, player_family_ids):
    secrets_node = root.get("secrets")
    if not secrets_node: return {"secrets": [], "total": 0}
    secrets = secrets_node.get("secrets")
    if not secrets: return {"secrets": [], "total": 0}
    
    family_set = set(player_family_ids)
    related = []
    total = 0
    
    # Check if it's a list or block
    iterator = secrets.as_list() if secrets.kind == "list" else [s for k, s in secrets.items()]
    
    for snode in iterator:
        total += 1
        participants_node = snode.get("participants")
        parts = []
        if participants_node:
            if participants_node.kind == "list":
                parts = [p.as_int() for p in participants_node.as_list()]
            elif participants_node.kind == "block":
                parts = [p.as_int() for k, p in participants_node.items()]
            else:
                parts = [participants_node.as_int()]
                
        # Drop None or Sentinels
        parts = [p for p in parts if p is not None and p != 4294967295]
        
        is_related = any(p in family_set for p in parts)
        if is_related:
            stype = snode.get("type")
            related.append({
                "type": str(stype.value) if stype else None,
                "participants": parts
            })
    return {"secrets": related, "total": total}

def extract_relations(root, player_family_ids):
    rels_node = root.get("relations")
    if not rels_node: return {"relations": [], "total": 0}
    active = rels_node.get("active_relations")
    if not active: return {"relations": [], "total": 0}
    
    family_set = set(player_family_ids)
    related = []
    total = 0
    iterator = active.as_list() if active.kind == "list" else [r for k, r in active.items()]
    
    for rnode in iterator:
        total += 1
        first = rnode.get("first")
        second = rnode.get("second")
        f_id = first.as_int() if first else None
        s_id = second.as_int() if second else None
        
        alliances_node = rnode.get("alliances")
        allies = []
        if alliances_node:
            nodes = alliances_node.as_list() if alliances_node.kind == "list" else [alliances_node]
            for n in nodes:
                if n.kind == "block":
                    for k, v in n.items():
                        if k.startswith("allied_through"):
                            val = v.as_int()
                            if val is not None:
                                allies.append(val)
                        
        hook_node = rnode.get("active_hook_1")
        hooks = []
        if hook_node and hook_node.kind == "block":
            h_type = hook_node.get("type")
            h_exp = hook_node.get("expiration_date")
            if not h_exp: h_exp = hook_node.get("expiration")
            hooks.append({
                "type": str(h_type.value) if h_type else None,
                "expiration_date": str(h_exp.value) if h_exp else None
            })

        is_related = False
        if f_id in family_set or s_id in family_set:
            is_related = True
        if any(a in family_set for a in allies):
            is_related = True
            
        if is_related:
            rtype = rnode.get("type")
            st = rnode.get("start")
            
            related.append({
                "type": str(rtype.value) if rtype else None,
                "first": f_id,
                "second": s_id,
                "start": str(st.value) if st else None,
                "hooks": hooks,
                "alliances": allies
            })
    return {"relations": related, "total": total}

def extract_dynasties(root, player_dynasty_id):
    dyns_node = root.get("dynasties")
    if not dyns_node: return {"dynasty": None, "total": 0}
    dyns = dyns_node.get("dynasties")
    total = len(dyns.children) if dyns and dyns.children else 0
    player_dyn = None
    if dyns and player_dynasty_id is not None:
        dyn_id_out = player_dynasty_id
        pd_node = dyns.children.get(str(player_dynasty_id)) if dyns.children else None
        if pd_node is None:
            # شناسهٔ ورودی ممکن است house باشد نه dynasty — زنجیرهٔ dynasties.dynasty_house.<id>.dynasty
            houses = dyns_node.children.get("dynasty_house") if dyns_node.children else None
            h = houses.children.get(str(player_dynasty_id)) if houses and houses.children else None
            if h is not None:
                link = h.children.get("dynasty") if h.children else None
                link_id = link.as_int() if link else None
                if link_id is not None and dyns.children.get(str(link_id)) is not None:
                    pd_node = dyns.children.get(str(link_id))
                    dyn_id_out = link_id
        if pd_node:
            prestige = pd_node.get("prestige")
            curr = prestige.get("currency") if prestige else None
            p_val = curr.as_float() if curr else None
            head = pd_node.get("dynasty_head")
            perk_node = pd_node.get("perk")
            perks = []
            if perk_node:
                if perk_node.kind == "list":
                    perks = [str(p.value) for p in perk_node.as_list()]
                elif perk_node.kind == "block":
                    perks = [str(p.value) for k, p in perk_node.items()]
                else:
                    perks = [str(perk_node.value)]
            player_dyn = {"id": dyn_id_out, "prestige": p_val, "dynasty_head": head.as_int() if head else None, "perks": perks}
            if dyn_id_out != player_dynasty_id:
                player_dyn["house_id"] = player_dynasty_id
    return {"dynasty": player_dyn or {}, "total": total}

def extract_artifacts(root, player_family_ids):
    artifacts_node = root.get("artifacts")
    if not artifacts_node: return {"artifacts": [], "missing_owner": 0, "total": 0}
    artifacts = artifacts_node.get("artifacts")
    if not artifacts: return {"artifacts": [], "missing_owner": 0, "total": 0}
    
    family_set = set(player_family_ids)
    related = []
    missing_owner = 0
    total = 0
    for aid_str, anode in artifacts.items():
        total += 1
        owner = anode.get("owner")
        owner_id = owner.as_int() if owner else None
        if owner_id is None:
            missing_owner += 1
            continue
        
        if owner_id in family_set:
            name = anode.get("name")
            atype = anode.get("type")
            rarity = anode.get("rarity")
            dur = anode.get("durability")
            mdur = anode.get("max_durability")
            hist = anode.get("history")
            
            history_entries = []
            if hist:
                def get_all_nodes(node, key):
                    if not node or not node.children: return []
                    res = []
                    if key in node.children: res.append(node.children[key])
                    if getattr(node, 'same_name', None) and key in node.same_name: res.extend(node.same_name[key])
                    return res
                for he in get_all_nodes(hist, "entries"):
                    rec = he.get("recipient")
                    if rec: history_entries.append({"recipient": rec.as_int()})
            
            related.append({
                "id": int(aid_str),
                "name": str(name.value) if name else None,
                "type": str(atype.value) if atype else None,
                "rarity": str(rarity.value) if rarity else None,
                "durability": dur.as_float() if dur else None,
                "max_durability": mdur.as_float() if mdur else None,
                "is_equipped": "missing",
                "history": history_entries
            })
    return {"artifacts": related, "missing_owner": missing_owner, "total": total}

if __name__ == "__main__":
    import sys
    sys.exit(main())
