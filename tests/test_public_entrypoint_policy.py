import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
LOCALES = ("es", "tl", "zh", "ar", "vi", "ru", "hi", "fr")
EXCLUDED_PARTS = {"starter-kit", "build-kit", "build-kits"}


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.links.append(value)


def public_shell_pages():
    pages = []
    for path in ROOT.rglob("*.html"):
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        text = path.read_text(encoding="utf-8")
        if 'class="site-header"' in text:
            pages.append((relative, text))
    return pages


def primary_nav(text):
    match = re.search(r'<div class="nav-links">(.*?)</div>', text, re.S)
    if not match:
        raise AssertionError("Missing primary nav-links block")
    return match.group(1)


class PublicEntrypointPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.faq = (ROOT / "faq.html").read_text(encoding="utf-8")
        cls.start = (ROOT / "start-here.html").read_text(encoding="utf-8")
        cls.shell = (ROOT / "assets" / "site-shell.js").read_text(encoding="utf-8")
        cls.pages = public_shell_pages()

    def test_every_public_shell_page_has_shared_orientation_and_general_nav_has_one_quiz_cta(self):
        self.assertGreaterEqual(len(self.pages), 80)
        failures = []
        for relative, text in self.pages:
            nav = primary_nav(text)
            quiz_ctas = re.findall(
                r'<a\b[^>]*class="[^"]*nav-cta[^"]*"[^>]*href="([^"]*soul-quiz\.html)"',
                nav,
                re.I,
            )
            if "soul-quiz.html" in nav and len(quiz_ctas) != 1:
                failures.append(f"{relative}: highlighted quiz nav CTA count={len(quiz_ctas)}")
            if "assets/site-shell.js" not in text:
                failures.append(f"{relative}: missing site-shell.js")
        self.assertEqual([], failures)

    def test_competing_destinations_are_absent_from_primary_navigation(self):
        failures = []
        for relative, text in self.pages:
            nav = primary_nav(text)
            for anchor in re.findall(r'<a\b[^>]*href="[^"]+"[^>]*>.*?</a>', nav, re.S | re.I):
                if re.search(r'\s(?:lang|hreflang)="', anchor, re.I):
                    continue
                href_match = re.search(r'href="([^"]+)"', anchor, re.I)
                if not href_match:
                    failures.append(f"{relative}: anchor missing href")
                    continue
                href = href_match.group(1).lower()
                if (
                    href.split("#", 1)[0].rstrip("/").rsplit("/", 1)[-1]
                    in {"start-here.html", "faq.html", "nurse-station.html"}
                    or "#founding-year" in href
                ):
                    failures.append(f"{relative}: {href}")
        self.assertEqual([], failures)

    def test_orientation_component_is_localized_and_skips_core_onboarding(self):
        for language in ("en",) + LOCALES:
            self.assertRegex(self.shell, rf"\b{language}:\s*\[")
        for page in (
            "soul-quiz.html",
            "start-here.html",
            "setup.html",
            "setup-kit.html",
        ):
            self.assertIn(f'"{page}": true', self.shell)
        self.assertNotIn('"index.html": true', self.shell)
        self.assertNotIn('"": true', self.shell)
        self.assertIn("localeHome", self.shell)
        self.assertIn('path === "/" || path === "/index.html"', self.shell)
        self.assertIn('className = "new-here-bar"', self.shell)
        self.assertIn('new URL("../soul-quiz.html", script.src)', self.shell)

    def test_homepage_has_one_primary_action_repeated(self):
        primary_links = re.findall(
            r'<a class="btn btn-primary" href="([^"]+)"', self.home, re.I
        )
        self.assertGreaterEqual(len(primary_links), 3)
        self.assertEqual({"soul-quiz.html"}, set(primary_links))
        nav = primary_nav(self.home)
        self.assertEqual(1, nav.count('class="nav-cta"'))
        self.assertIn('href="soul-quiz.html"', nav)

    def test_mobile_browser_and_optional_desktop_boundaries_are_up_front(self):
        hero = self.home.split('<section class="hero">', 1)[1].split("</section>", 1)[0]
        for phrase in (
            "phone, tablet, Chromebook, Mac, or Windows computer",
            "Only optional Hermes requires a desktop.",
            "Core setup and self-customization are free forever.",
        ):
            self.assertIn(phrase, hero)
        self.assertIn("Can I start on my phone? What needs a computer?", self.faq)
        self.assertIn("required only if you later choose the optional Hermes", self.faq)
        self.assertIn("Browser-first onboarding · Optional Hermes setup", self.start)

    def test_door_one_routes_to_executable_browser_steps_not_hermes_filesystem_steps(self):
        setup = (ROOT / "setup.html").read_text(encoding="utf-8")
        downloads = (ROOT / "hermes-downloads" / "index.html").read_text(encoding="utf-8")
        for text in (self.start, setup, downloads):
            self.assertIn("four browser-safe steps", text)
            self.assertIn("index.html#how-it-works", text)
        for stale in (
            "do steps 2–5 in ChatGPT or Claude",
            "Do steps 2–5 in the browser AI",
            "do steps 2–5 of",
        ):
            self.assertNotIn(stale, self.start + setup + downloads)
        for heading in (
            "Door 2 only — take the SOUL Quiz, then give Hermes your SOUL file",
            "Door 2 only — download the Starter Kit and show Hermes where it lives",
            "Door 2 only — build your dashboard with Hermes, then bookmark it",
            "Both doors — run your first prompts",
            "<strong>Door 2/Hermes only:</strong> tell Hermes, \"Load the skills in 15-Student-Study-OS.\"",
            "Browser users can use the safe lecture-notes prompt above without loading a local folder.",
        ):
            self.assertIn(heading, self.start)

    def test_pricing_policy_is_specific_and_has_a_clear_after_state(self):
        for phrase in (
            "Through December 31, 2026",
            "Core setup is free forever.",
            "$10 one time",
            "$29.90/year",
            "September 15–17, 2026 virtual summit",
            "No auto-enrollment",
        ):
            self.assertIn(phrase, self.home)
        self.assertIn('id="pricing"', self.faq)
        self.assertIn("free core setup and self-directed customization continue permanently", self.faq)

    def test_homepages_do_not_use_inflated_anchor_or_placeholder_testimonials(self):
        failures = []
        for path in (ROOT / "index.html",) + tuple(ROOT / locale / "index.html" for locale in LOCALES):
            text = path.read_text(encoding="utf-8")
            for pattern in (
                r"\$1,500\s*[–-]\s*\$2,999",
                r'id="when-it-works"',
                r"words we intend to earn",
                r"palabras que queremos merecer",
                r"mga salitang nais naming",
            ):
                if re.search(pattern, text, re.I):
                    failures.append(f"{path.relative_to(ROOT)}: {pattern}")
            primary_links = re.findall(
                r'<a class="btn btn-primary" href="([^"]+)"', text, re.I
            )
            if not primary_links or any("soul-quiz.html" not in href for href in primary_links):
                failures.append(f"{path.relative_to(ROOT)}: competing primary CTA")
        self.assertEqual([], failures)

    def test_localized_front_doors_carry_same_pricing_and_device_boundaries(self):
        failures = []
        for locale in LOCALES:
            home = (ROOT / locale / "index.html").read_text(encoding="utf-8")
            faq = (ROOT / locale / "faq.html").read_text(encoding="utf-8")
            for token in ("2026", "10", "29"):
                if token not in home or token not in faq:
                    failures.append(f"{locale}: missing {token}")
            if 'id="pricing"' not in faq:
                failures.append(f"{locale}: missing pricing anchor")
            if "Hermes" not in faq or "8&nbsp;" not in faq:
                failures.append(f"{locale}: missing optional Hermes device boundary")
        self.assertEqual([], failures)

    def test_localized_homepages_are_browser_first_and_hermes_is_optional_last(self):
        failures = []
        for locale in LOCALES:
            text = (ROOT / locale / "index.html").read_text(encoding="utf-8")
            match = re.search(
                r'<section class="section section-alt" id="how-it-works">(.*?)</section>',
                text,
                re.S,
            )
            if not match:
                failures.append(f"{locale}: missing how-it-works section")
                continue
            how = match.group(1)
            if how.count('class="step"') != 5:
                failures.append(f"{locale}: browser path does not have five steps")
            for token in (
                "ChatGPT",
                "Claude",
                "nurse-ai-os-starter-kit.zip",
                '../start-here.html" lang="en"',
            ):
                if token not in how:
                    failures.append(f"{locale}: missing {token}")
            steps = re.findall(r'<div class="step">(.*?)</div>', how, re.S)
            if len(steps) == 5 and (
                any("Hermes" in step for step in steps[:4])
                or "Hermes" not in steps[4]
            ):
                failures.append(f"{locale}: Hermes is not confined to optional step five")
            if 'href="#how-it-works"' not in text:
                failures.append(f"{locale}: hero secondary CTA does not stay on browser path")
        self.assertEqual([], failures)

    def test_localized_start_pages_offer_browser_first_and_optional_hermes_doors(self):
        failures = []
        for locale in LOCALES:
            text = (ROOT / locale / "start-here.html").read_text(encoding="utf-8")
            for token in (
                '<main id="main-content">',
                "ChatGPT",
                "Claude",
                '../soul-quiz.html',
                '../start-here.html" lang="en"',
            ):
                if token not in text:
                    failures.append(f"{locale}/start-here.html: missing {token}")
            if "<iframe" in text:
                failures.append(f"{locale}/start-here.html: stale install-first video remains")
        self.assertEqual([], failures)

    def test_public_shell_has_no_expired_first_huddle_date_or_free_only_this_year_claim(self):
        expired = (
            "July 13",
            "13 de julio",
            "Hulyo 13",
            "7月13",
            "13 يوليو",
            "13 tháng 7",
            "13 июля",
            "13 जुलाई",
            "13 juillet",
        )
        free_only = (
            "free for nurses and nursing students this founding year",
            "gratuito para profesionales y estudiantes de enfermería este año de fundación",
            "libre para sa mga nars at student nurse ngayong founding year",
            "创始年面向护士和护理学生免费",
            "مجاني للممرضين والممرضات وطلاب وطالبات التمريض خلال سنة التأسيس",
            "miễn phí cho điều dưỡng và sinh viên điều dưỡng trong năm sáng lập",
            "в год основания система бесплатна",
            "इस संस्थापक वर्ष में नर्सों और नर्सिंग विद्यार्थियों के लिए निःशुल्क",
            "gratuit pour le personnel infirmier et les étudiant·es en sciences infirmières pendant cette année fondatrice",
        )
        failures = []
        for relative, text in public_shell_pages():
            phrases = free_only
            if relative.name in {"index.html", "faq.html", "resources.html"}:
                phrases = expired + free_only
            for phrase in phrases:
                if phrase.casefold() in text.casefold():
                    failures.append(f"{relative}: stale phrase {phrase}")
        self.assertEqual([], failures)

    def test_faqs_do_not_make_mandatory_runtime_or_safety_guarantees(self):
        forbidden = (
            r"step 1|paso 1|hakbang 1|第 1 步|الخطوة الأولى|bước 1|первый шаг|चरण 1|étape 1",
            r"inconvenience, not an incident|abala, hindi insidente|désagrément, pas un incident|không phải một sự cố nghiêm trọng",
            r"system is designed to say no|sistema está diseñado para decir no|系统的设计原则是先判断|Hệ thống được thiết kế để biết nói|система.*сначала определить необходимость отказа|système est conçu pour dire non",
            r"the safe value|valor seguro|ligtas na halaga|valeur sûre|安全值|القيمة الآمنة|giá trị an toàn|безопаснее выбрать|सुरक्षित मान",
            r"system applies it for you|sistema lo aplica por usted|inilalapat ng system ang mga ito para sa iyo|系统会在工作流中落实|النظام يطبقها نيابة|hệ thống sẽ áp dụng|система применяет правила|system इसे आपके लिए लागू|système applique ces principes pour vous",
        )
        failures = []
        faq_paths = [ROOT / "faq.html"] + [ROOT / locale / "faq.html" for locale in LOCALES]
        for path in faq_paths:
            text = path.read_text(encoding="utf-8")
            for pattern in forbidden:
                if re.search(pattern, text, re.I):
                    failures.append(f"{path.relative_to(ROOT)}: {pattern}")
            for link in (
                "start-here.html",
                "hermes-configuration-handbook.html",
                "when-things-go-wrong.html",
                "privacy.html",
            ):
                if link not in text:
                    failures.append(f"{path.relative_to(ROOT)}: missing {link}")
        self.assertEqual([], failures)

    def test_entrypoint_metadata_matches_browser_first_product(self):
        failures = []
        assistant_terms = (
            "asistente personal de IA",
            "personal AI assistant",
            "个人 AI 助手",
            "مساعد ذكاء اصطناعي شخصي",
            "Trợ lý AI cá nhân",
            "персональный ИИ-помощник",
            "व्यक्तिगत AI सहायक",
            "assistant personnel d’IA",
        )
        for locale in LOCALES:
            text = (ROOT / locale / "index.html").read_text(encoding="utf-8")
            head = text.split("</head>", 1)[0]
            if "ChatGPT" not in head or "Claude" not in head:
                failures.append(f"{locale}/index.html: browser tools missing from metadata")
            for term in assistant_terms:
                if term.casefold() in head.casefold():
                    failures.append(f"{locale}/index.html: stale assistant metadata")
        start_head = (ROOT / "start-here.html").read_text(encoding="utf-8").split("</head>", 1)[0]
        if "browser" not in start_head.casefold() or "optional Hermes" not in start_head:
            failures.append("start-here.html: stale install-first metadata")
        hermes_downloads = (ROOT / "hermes-downloads" / "index.html").read_text(encoding="utf-8")
        for phrase in ("Step 1", "Step&nbsp;1", "five-step"):
            if phrase in hermes_downloads:
                failures.append(f"hermes-downloads/index.html: {phrase}")
        self.assertEqual([], failures)

    def test_404_preserves_quiz_first_hierarchy_at_nested_paths(self):
        text = (ROOT / "404.html").read_text(encoding="utf-8")
        self.assertIn('<script src="/assets/site-shell.js" defer></script>', text)
        primary_links = re.findall(r'<a class="btn btn-primary" href="([^"]+)"', text, re.I)
        self.assertEqual(["/soul-quiz.html"], primary_links)
        self.assertNotIn("Start Here — the five steps", text)

    def test_about_pages_bound_maturity_enforcement_and_authority(self):
        forbidden = (
            r"routes, enforces|Hermes learns and adapts|applies EDENA risk classification",
            r"Nurse AI OS enruta, aplica|Hermes aprende y se adapta|aplica la clasificación de riesgo EDENA",
            r"Nurse AI OS 路由、执行|Hermes 学习并进化|施加 EDENA",
            r"يفرض الضوابط|يتعلم ويتكيف|يطبق تصنيف المخاطر",
            r"Nurse AI OS định tuyến, thực thi|Hermes học hỏi và thích nghi|áp dụng phân loại rủi ro",
            r"Nurse AI OS маршрутизирует, обеспечивает|Hermes учится и адаптируется|применяет классификацию рисков",
            r"Nurse AI OS रूट करता है, नियम लागू|Hermes सीखता और अनुकूलित|EDENA जोखिम वर्गीकरण और गवर्नेंस-युक्त मेमोरी लागू",
            r"Nurse AI OS achemine, fait appliquer|Hermes apprend et s’adapte|applique la classification des risques",
        )
        failures = []
        maturity = {
            "about.html": "standalone operating system",
            "es/about.html": "sistema operativo autónomo",
            "tl/about.html": "standalone OS",
            "zh/about.html": "独立操作系统",
            "ar/about.html": "نظام تشغيل مستقل",
            "vi/about.html": "hệ điều hành độc lập",
            "ru/about.html": "самостоятельная ОС",
            "hi/about.html": "standalone OS",
            "fr/about.html": "système d’exploitation autonome",
        }
        for path in [ROOT / "about.html"] + [ROOT / locale / "about.html" for locale in LOCALES]:
            text = path.read_text(encoding="utf-8")
            for pattern in forbidden:
                if re.search(pattern, text, re.I):
                    failures.append(f"{path.relative_to(ROOT)}: {pattern}")
            for token in ("ChatGPT", "Claude", "Hermes"):
                if token not in text:
                    failures.append(f"{path.relative_to(ROOT)}: missing {token}")
            if path == ROOT / "about.html":
                expected_packet = "assets/nurse-ai-os-media-packet.pdf"
            elif path.parent.name in {"ar", "hi"}:
                expected_packet = f"../media-{path.parent.name}.html"
            else:
                expected_packet = f"../assets/nurse-ai-os-media-packet-{path.parent.name}.pdf"
            if text.count(expected_packet) != 1:
                failures.append(f"{path.relative_to(ROOT)}: current localized media kit link count")
            expected_center = 'href="media.html"' if path == ROOT / "about.html" else 'href="../media.html"'
            if text.count(expected_center) != 1:
                failures.append(f"{path.relative_to(ROOT)}: media center link count")
            relative = str(path.relative_to(ROOT))
            if maturity[relative].casefold() not in text.casefold():
                failures.append(f"{path.relative_to(ROOT)}: missing standalone maturity boundary")
        self.assertEqual([], failures)

    def test_localized_safety_cards_do_not_promise_license_or_patient_protection(self):
        forbidden = (
            r"reglas en lenguaje sencillo que protegen tu licencia y a tus pacientes",
            r"malinaw na rules na nagpoprotekta sa lisensya mo at sa mga pasyente",
            r"保护你执照和患者的白话规则",
            r"قواعد واضحة تحمي ترخيصكم ومرضاكم",
            r"quy tắc dễ hiểu giúp bảo vệ giấy phép hành nghề của bạn cùng người bệnh",
            r"правила, защищающие вашу профессиональную ответственность и пациентов",
            r"जो आपके license और मरीजों की रक्षा करने में मदद करते हैं",
            r"règles claires contribuent à protéger votre autorisation d’exercer et vos patients",
        )
        failures = []
        old_headers = '<thead><tr><th>Option</th><th>Price</th><th>Details</th></tr></thead>'
        for locale in LOCALES:
            text = (ROOT / locale / "index.html").read_text(encoding="utf-8")
            if old_headers in text:
                failures.append(f"{locale}/index.html: untranslated pricing headers")
            for pattern in forbidden:
                if re.search(pattern, text, re.I):
                    failures.append(f"{locale}/index.html: {pattern}")
        self.assertEqual([], failures)

    def test_external_review_findings_remain_closed(self):
        terms = (ROOT / "terms.html").read_text(encoding="utf-8")
        self.assertIn("Effective date: July 25, 2026", terms)
        self.assertNotIn("Effective date: July 14, 2026", terms)
        for phrase in (
            "core browser-first setup and self-customization are free forever",
            "$10 one time", "$29.90 per year", "no automatic enrollment",
            "free core does not",
        ):
            self.assertIn(phrase.casefold(), terms.casefold())
        self.assertNotIn("During the founding year, the core experience is free", terms)

        css = (ROOT / "assets" / "nurse-ai.css").read_text(encoding="utf-8")
        mobile_pricing = css[css.index("@media (max-width: 700px)"):css.index("/* ---------- FAQ ---------- */")]
        self.assertIn(".pricing-policy-table thead { position: static; }", mobile_pricing)
        self.assertNotIn("clip:", mobile_pricing)
        self.assertNotIn("display: block", mobile_pricing)
        orientation_rule = css[css.index(".new-here-inner a {"):css.index(".new-here-inner a:focus-visible")]
        self.assertIn("min-height: 44px", orientation_rule)

        timing_phrases = {
            "es": ("2 minutos", "30 días", "20 minutos"),
            "tl": ("2 minuto", "30-day roadmap", "20 minuto"),
            "zh": ("2 分钟", "30 天路线图", "20 分钟"),
            "ar": ("دقيقتين", "30 يومًا", "20 دقيقة"),
            "vi": ("2 phút", "30 ngày", "20 phút"),
            "ru": ("2 минут", "30-дневную", "20 минут"),
            "hi": ("2 मिनट", "30-दिन", "20 मिनट"),
            "fr": ("2 minutes", "30 jours", "20 minutes"),
        }
        failures = []
        for locale in LOCALES:
            home = (ROOT / locale / "index.html").read_text(encoding="utf-8")
            start = (ROOT / locale / "start-here.html").read_text(encoding="utf-8")
            faq = (ROOT / locale / "faq.html").read_text(encoding="utf-8")
            proof = re.search(
                r'<section[^>]+id="proof"[\s\S]*?<p class="eyebrow">(.*?)</p>\s*<h2>(.*?)</h2>',
                home,
            )
            if not proof or proof.group(1).strip() == proof.group(2).strip():
                failures.append(f"{locale}/index.html: duplicated proof eyebrow and heading")
            if home.count('href="faq.html#pricing"') != 1 or 'href="../faq.html#pricing"' in home:
                failures.append(f"{locale}/index.html: pricing does not target localized FAQ")
            if start.count('<p class="cta-line"><a href="../pathways.html">') != 1:
                failures.append(f"{locale}/start-here.html: role CTA does not target pathways")
            if re.search(r'^\s{8}<strong>[^<]+</strong>', start, re.M):
                failures.append(f"{locale}/start-here.html: unwrapped affirmative text remains")
            missing_timing = [phrase for phrase in timing_phrases[locale] if phrase not in faq]
            if missing_timing:
                failures.append(
                    f"{locale}/faq.html: missing timing phrases {missing_timing}"
                )
        ar_start = (ROOT / "ar" / "start-here.html").read_text(encoding="utf-8")
        if "ابدؤوا من دون تثبيت →" in ar_start:
            failures.append("ar/start-here.html: LTR arrow remains in RTL CTA")
        fr_faq = (ROOT / "fr" / "faq.html").read_text(encoding="utf-8")
        if "<strong>point de contrôle humain</strong>" not in fr_faq:
            failures.append("fr/faq.html: glossary label does not match its question")
        self.assertEqual([], failures)

    def test_localized_safety_resources_target_real_anchor_without_guarantees(self):
        root_start = (ROOT / "start-here.html").read_text(encoding="utf-8")
        self.assertRegex(root_start, r'id=["\']safety["\']')
        retired = (
            "protect patients, licenses, and you",
            "protegen a los pacientes, las licencias y a ti",
            "nagpoprotekta sa mga pasyente, lisensya, at sa iyo",
            "保护患者、执业资格和你自己的五条规则",
            "تحمي المرضى والتراخيص وتحميكم",
            "bảo vệ người bệnh, giấy phép hành nghề và chính bạn",
            "защитить пациентов, профессиональную ответственность и вас",
            "मरीजों, आपके पेशेवर लाइसेंस और आपको सुरक्षित रखते हैं",
            "protègent les patients, votre droit d’exercice et vous-même",
            "your AI runs governed",
            "sus ejecuciones de IA estarán gobernadas",
            "pamamahalaan ang iyong AI run",
            "让 AI 在治理下运行",
            "ليعمل الذكاء الاصطناعي ضمن الحوكمة",
            "AI của bạn vận hành trong khuôn khổ quản trị",
            "чтобы ИИ работал в заданных границах",
            "आपका AI गवर्नेंस के तहत चलेगा",
            "encadrer votre IA par la gouvernance",
        )
        pages = [ROOT / "resources.html"] + [ROOT / locale / "resources.html" for locale in LOCALES]
        failures = []
        for path in pages:
            text = path.read_text(encoding="utf-8")
            expected = 'href="start-here.html#safety"' if path == ROOT / "resources.html" else 'href="../start-here.html#safety"'
            if text.count(expected) != 1:
                failures.append(f"{path.relative_to(ROOT)}: missing exact safety destination")
            for phrase in retired:
                if phrase.casefold() in text.casefold():
                    failures.append(f"{path.relative_to(ROOT)}: retired claim {phrase}")
        self.assertEqual([], failures)

    def test_public_shell_internal_links_resolve(self):
        missing = []
        checked = 0
        for relative, text in public_shell_pages():
            collector = LinkCollector()
            collector.feed(text)
            source = ROOT / relative
            for raw in collector.links:
                if raw.startswith((
                    "http://", "https://", "mailto:", "tel:",
                    "data:", "javascript:", "#",
                )):
                    continue
                parsed = urlsplit(raw)
                if not parsed.path or "{" in parsed.path:
                    continue
                decoded = unquote(parsed.path)
                target = (
                    ROOT / decoded.lstrip("/")
                    if decoded.startswith("/")
                    else source.parent / decoded
                ).resolve()
                if decoded.endswith("/"):
                    target = target / "index.html"
                checked += 1
                if not target.exists():
                    missing.append(f"{relative}: {raw}")
        self.assertGreater(checked, 2500)
        self.assertEqual([], missing)


if __name__ == "__main__":
    unittest.main()
