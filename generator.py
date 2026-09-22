import json
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


# ============================================================
# AYARLAR
# ============================================================

BASE_URL = "https://www.fullhdfilmizlesene.now"

START_URL = (
    "https://www.fullhdfilmizlesene.now/"
    "filmizle/turkce-dublaj-filmler-1"
)

OUTPUT_FILE = "movies.json"

# Kaç sayfa taransın?
# 1 = sadece ilk sayfa
# 2 = ilk 2 sayfa
# 0 = mümkün olduğu kadar tüm sayfalar
MAX_PAGES = 1


# ============================================================
# URL DÜZELTME
# ============================================================

def make_absolute_url(url):
    """
    Relative URL'yi absolute URL'ye çevirir.
    """

    if not url:
        return ""

    url = url.strip()

    if url.startswith("//"):
        return "https:" + url

    return urljoin(BASE_URL, url)


# ============================================================
# POSTER BUL
# ============================================================

def get_poster(movie_element):
    """
    Film kartındaki poster URL'sini bulur.
    """

    # Önce picture içerisindeki source/img elementlerini kontrol et
    picture = movie_element.find("picture")

    if picture:

        # source
        for source in picture.find_all("source"):

            for attr in [
                "src",
                "data-src",
                "data-lazy-src",
                "data-original",
                "srcset",
                "data-srcset"
            ]:

                value = source.get(attr)

                if value:
                    if " " in value and "," not in value:
                        value = value.split(" ")[0]

                    if "," in value:
                        value = value.split(",")[0].strip()

                    return make_absolute_url(value)

        # img
        img = picture.find("img")

        if img:

            for attr in [
                "data-src",
                "data-lazy-src",
                "data-original",
                "src",
                "srcset"
            ]:

                value = img.get(attr)

                if value:

                    if "," in value:
                        value = value.split(",")[0].strip()

                    if " " in value:
                        value = value.split(" ")[0]

                    return make_absolute_url(value)

    # picture yoksa doğrudan img ara
    img = movie_element.find("img")

    if img:

        for attr in [
            "data-src",
            "data-lazy-src",
            "data-original",
            "src",
            "srcset"
        ]:

            value = img.get(attr)

            if value:

                if "," in value:
                    value = value.split(",")[0].strip()

                if " " in value:
                    value = value.split(" ")[0]

                return make_absolute_url(value)

    return ""


# ============================================================
# FILM BİLGİSİNİ ÇIKAR
# ============================================================

def parse_movie(movie):
    """
    li.film elementinden film bilgilerini çıkarır.
    """

    # --------------------------------------------------------
    # Film linki / başlığı
    # --------------------------------------------------------

    title_link = movie.select_one("a.tt")

    if not title_link:
        return None

    link = title_link.get("href", "").strip()

    if not link:
        return None

    link = make_absolute_url(link)

    title = title_link.get_text(" ", strip=True)

    # " izle" gibi son ekleri temizle
    title = title.strip()

    if title.lower().endswith(" izle"):
        title = title[:-5].strip()

    # --------------------------------------------------------
    # Yıl
    # --------------------------------------------------------

    year_element = movie.select_one(".film-yil")

    year = ""

    if year_element:
        year = year_element.get_text(" ", strip=True)

    # --------------------------------------------------------
    # IMDb
    # --------------------------------------------------------

    imdb_element = movie.select_one(".imdb")

    imdb = ""

    if imdb_element:
        imdb = imdb_element.get_text(" ", strip=True)

    # --------------------------------------------------------
    # Tür
    # --------------------------------------------------------

    genre_element = movie.select_one(".ktt")

    genre = ""

    if genre_element:
        genre = genre_element.get_text(" ", strip=True)

    # --------------------------------------------------------
    # 4K
    # --------------------------------------------------------

    uhd_element = movie.select_one(".uhd")

    uhd = ""

    if uhd_element:
        uhd = uhd_element.get_text(" ", strip=True)

    # --------------------------------------------------------
    # Dublaj / Altyazı
    # --------------------------------------------------------

    tur_element = movie.select_one(".tur")

    language = ""

    if tur_element:

        language = (
            tur_element.get("title")
            or tur_element.get_text(" ", strip=True)
        )

    # --------------------------------------------------------
    # Film kartındaki süre / eklenme zamanı
    # --------------------------------------------------------

    time_element = movie.select_one("time")

    added_time = ""

    if time_element:
        added_time = time_element.get_text(" ", strip=True)

    # --------------------------------------------------------
    # Poster
    # --------------------------------------------------------

    poster = get_poster(movie)

    # --------------------------------------------------------
    # Sonuç
    # --------------------------------------------------------

    return {
        "title": title,
        "link": link,
        "poster": poster,
        "year": year,
        "imdb": imdb,
        "genre": genre,
        "language": language,
        "quality": uhd,
        "added_time": added_time,
        "stream_url": ""
    }


# ============================================================
# SAYFADAKİ FİLMLERİ BUL
# ============================================================

def extract_movies(page):
    """
    Playwright üzerinden mevcut sayfadaki filmleri çıkarır.
    """

    print("\nFilm listesi aranıyor...")

    # Direkt DOM üzerinden kontrol
    count = page.locator("ul.list li.film").count()

    print(f"Bulunan film kartı: {count}")

    if count == 0:

        print("\nUYARI: ul.list li.film bulunamadı.")

        # HTML debug
        try:
            with open(
                "debug.html",
                "w",
                encoding="utf-8"
            ) as f:
                f.write(page.content())

            print("debug.html oluşturuldu.")

        except Exception as e:
            print("debug.html yazılamadı:", e)

        return []

    # BeautifulSoup ile mevcut DOM'u parse et
    html = page.content()

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    film_elements = soup.select(
        "ul.list li.film"
    )

    movies = []

    for index, movie in enumerate(
        film_elements,
        start=1
    ):

        try:

            data = parse_movie(movie)

            if not data:
                continue

            movies.append(data)

            print(
                f"[{index}/{len(film_elements)}] "
                f"{data['title']}"
            )

            print(
                f"    URL    : {data['link']}"
            )

            print(
                f"    Poster : {data['poster']}"
            )

            print(
                f"    Yıl    : {data['year']}"
            )

            print(
                f"    IMDb   : {data['imdb']}"
            )

            print(
                f"    Tür    : {data['genre']}"
            )

        except Exception as e:

            print(
                f"Film işlenirken hata: {e}"
            )

    return movies


# ============================================================
# SONRAKİ SAYFA
# ============================================================

def get_next_page(page):
    """
    Sayfadaki sonraki sayfa linkini bulmaya çalışır.
    """

    selectors = [
        "a.next",
        "a[rel='next']",
        ".pagination a.next",
        ".sayfalama a.next",
        "a[title*='Sonraki']",
        "a[aria-label*='Sonraki']"
    ]

    for selector in selectors:

        try:

            element = page.locator(
                selector
            ).first

            if element.count() == 0:
                continue

            href = element.get_attribute(
                "href"
            )

            if href:

                return make_absolute_url(
                    href
                )

        except Exception:
            continue

    return ""


# ============================================================
# ANA PROGRAM
# ============================================================

def main():

    all_movies = []

    visited_pages = set()

    with sync_playwright() as p:

        print("=" * 60)
        print("FullHD Film Generator")
        print("=" * 60)

        # ----------------------------------------------------
        # Browser
        # ----------------------------------------------------

        browser = p.chromium.launch(

            headless=False,

            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )

        # ----------------------------------------------------
        # Browser Context
        # ----------------------------------------------------

        context = browser.new_context(

            viewport={
                "width": 1920,
                "height": 1080
            },

            user_agent=(
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/122.0.0.0 "
                "Safari/537.36"
            ),

            locale="tr-TR",

            timezone_id="Europe/Istanbul"
        )

        # ----------------------------------------------------
        # Page
        # ----------------------------------------------------

        page = context.new_page()

        current_url = START_URL

        page_number = 1

        # ====================================================
        # SAYFALARI TARA
        # ====================================================

        while current_url:

            if current_url in visited_pages:
                break

            visited_pages.add(
                current_url
            )

            print("\n")
            print("=" * 60)
            print(
                f"SAYFA {page_number}"
            )
            print("=" * 60)

            print(
                f"URL: {current_url}"
            )

            # ------------------------------------------------
            # Sayfaya git
            # ------------------------------------------------

            try:

                response = page.goto(

                    current_url,

                    wait_until="domcontentloaded",

                    timeout=60000
                )

                if response:

                    print(
                        f"HTTP: {response.status}"
                    )

            except Exception as e:

                print(
                    "Sayfa açılırken hata:"
                )

                print(e)

                break

            # ------------------------------------------------
            # Sayfanın yüklenmesini bekle
            # ------------------------------------------------

            print(
                "Sayfanın yüklenmesi bekleniyor..."
            )

            try:

                page.wait_for_selector(

                    "ul.list li.film",

                    timeout=20000
                )

            except Exception:

                print(
                    "Film selector bekleme "
                    "süresi doldu."
                )

            # Ek bekleme
            page.wait_for_timeout(
                3000
            )

            # ------------------------------------------------
            # Başlık
            # ------------------------------------------------

            print(
                f"Sayfa başlığı: {page.title()}"
            )

            # ------------------------------------------------
            # Filmleri çıkar
            # ------------------------------------------------

            movies = extract_movies(
                page
            )

            print(
                f"\nBu sayfada bulunan film: "
                f"{len(movies)}"
            )

            # ------------------------------------------------
            # Duplicate kontrolü
            # ------------------------------------------------

            existing_links = {
                movie["link"]
                for movie in all_movies
            }

            for movie in movies:

                if movie["link"] not in existing_links:

                    all_movies.append(
                        movie
                    )

            print(
                f"Toplam benzersiz film: "
                f"{len(all_movies)}"
            )

            # ------------------------------------------------
            # Sayfa limiti
            # ------------------------------------------------

            if MAX_PAGES > 0:

                if page_number >= MAX_PAGES:

                    print(
                        "\nMAX_PAGES sınırına ulaşıldı."
                    )

                    break

            # ------------------------------------------------
            # Sonraki sayfa
            # ------------------------------------------------

            next_url = get_next_page(
                page
            )

            if not next_url:

                print(
                    "\nSonraki sayfa bulunamadı."
                )

                break

            print(
                f"\nSonraki sayfa: {next_url}"
            )

            current_url = next_url

            page_number += 1

            time.sleep(1)

        # ====================================================
        # BROWSER KAPAT
        # ====================================================

        browser.close()

    # ========================================================
    # JSON KAYDET
    # ========================================================

    print("\n")
    print("=" * 60)
    print("JSON OLUŞTURULUYOR")
    print("=" * 60)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            all_movies,
            f,
            ensure_ascii=False,
            indent=4
        )

    print(
        f"\nTamamlandı!"
    )

    print(
        f"Toplam film: {len(all_movies)}"
    )

    print(
        f"Dosya: {OUTPUT_FILE}"
    )

    # ========================================================
    # ÖZET
    # ========================================================

    print("\n")
    print("=" * 60)
    print("ÖZET")
    print("=" * 60)

    for i, movie in enumerate(
        all_movies[:10],
        start=1
    ):

        print(
            f"{i}. {movie['title']}"
        )

    if len(all_movies) > 10:

        print(
            f"... ve {len(all_movies) - 10} film daha."
        )


# ============================================================
# PROGRAMI ÇALIŞTIR
# ============================================================

if __name__ == "__main__":
    main()
