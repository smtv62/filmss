import json
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


BASE_URL = "https://www.fullhdfilmizlesene.now"

START_URL = (
    "https://www.fullhdfilmizlesene.now/"
    "filmizle/turkce-dublaj-filmler-1"
)

OUTPUT_FILE = "movies.json"


def make_absolute_url(url):
    if not url:
        return ""

    return urljoin(BASE_URL, url)


def get_poster(movie):

    picture = movie.find("picture")

    if picture:

        img = picture.find("img")

        if img:

            for attr in [
                "data-src",
                "data-lazy-src",
                "data-original",
                "src"
            ]:

                value = img.get(attr)

                if value:
                    return make_absolute_url(value)

    img = movie.find("img")

    if img:

        for attr in [
            "data-src",
            "data-lazy-src",
            "data-original",
            "src"
        ]:

            value = img.get(attr)

            if value:
                return make_absolute_url(value)

    return ""


def parse_movie(movie):

    a_tag = movie.select_one("a.tt")

    if not a_tag:
        return None

    link = a_tag.get("href", "")

    if not link:
        return None

    title = a_tag.get_text(
        " ",
        strip=True
    )

    if title.lower().endswith(" izle"):
        title = title[:-5].strip()

    year_element = movie.select_one(".film-yil")

    year = ""

    if year_element:
        year = year_element.get_text(
            " ",
            strip=True
        )

    imdb_element = movie.select_one(".imdb")

    imdb = ""

    if imdb_element:
        imdb = imdb_element.get_text(
            " ",
            strip=True
        )

    genre_element = movie.select_one(".ktt")

    genre = ""

    if genre_element:
        genre = genre_element.get_text(
            " ",
            strip=True
        )

    quality_element = movie.select_one(".uhd")

    quality = ""

    if quality_element:
        quality = quality_element.get_text(
            " ",
            strip=True
        )

    language_element = movie.select_one(".tur")

    language = ""

    if language_element:

        language = (
            language_element.get("title")
            or language_element.get_text(
                " ",
                strip=True
            )
        )

    return {
        "title": title,
        "link": make_absolute_url(link),
        "poster": get_poster(movie),
        "year": year,
        "imdb": imdb,
        "genre": genre,
        "language": language,
        "quality": quality,
        "stream_url": ""
    }


def main():

    movies = []

    with sync_playwright() as p:

        print("=" * 60)
        print("FULLHD FILM GENERATOR")
        print("=" * 60)

        browser = p.chromium.launch(

            # REPLIT / LINUX SERVER
            headless=True,

            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-gpu"
            ]
        )

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

            locale="tr-TR"
        )

        page = context.new_page()

        print("\nSite açılıyor...")

        try:

            response = page.goto(
                START_URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

            if response:
                print(
                    "HTTP:",
                    response.status
                )

        except Exception as e:

            print(
                "Site açılırken hata:"
            )

            print(e)

            browser.close()
            return

        print(
            "Sayfanın yüklenmesi bekleniyor..."
        )

        try:

            page.wait_for_selector(
                "ul.list li.film",
                timeout=30000
            )

        except Exception as e:

            print(
                "Film selector bulunamadı:"
            )

            print(e)

        # Dinamik içerik için bekle
        page.wait_for_timeout(5000)

        print(
            "Sayfa başlığı:",
            page.title()
        )

        print(
            "Sayfa URL:",
            page.url
        )

        # --------------------------------------------------
        # Film sayısını doğrudan Playwright ile kontrol et
        # --------------------------------------------------

        film_count = page.locator(
            "ul.list li.film"
        ).count()

        print(
            "\nBulunan film kartı:",
            film_count
        )

        # --------------------------------------------------
        # Film yoksa HTML kaydet
        # --------------------------------------------------

        if film_count == 0:

            print(
                "\nFilm bulunamadı!"
            )

            with open(
                "debug.html",
                "w",
                encoding="utf-8"
            ) as f:

                f.write(
                    page.content()
                )

            print(
                "debug.html oluşturuldu."
            )

            browser.close()
            return

        # --------------------------------------------------
        # BeautifulSoup
        # --------------------------------------------------

        html = page.content()

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        film_elements = soup.select(
            "ul.list li.film"
        )

        print(
            "\nFilm bilgileri çıkarılıyor..."
        )

        # --------------------------------------------------
        # Filmleri işle
        # --------------------------------------------------

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
                    f"\n[{index}/{len(film_elements)}]"
                )

                print(
                    "Film:",
                    data["title"]
                )

                print(
                    "URL:",
                    data["link"]
                )

                print(
                    "Poster:",
                    data["poster"]
                )

                print(
                    "Yıl:",
                    data["year"]
                )

                print(
                    "IMDb:",
                    data["imdb"]
                )

                print(
                    "Tür:",
                    data["genre"]
                )

                print(
                    "Kalite:",
                    data["quality"]
                )

            except Exception as e:

                print(
                    f"Film işleme hatası: {e}"
                )

        browser.close()

    # ------------------------------------------------------
    # JSON
    # ------------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            movies,
            f,
            ensure_ascii=False,
            indent=4
        )

    print("\n")
    print("=" * 60)
    print("İŞLEM TAMAMLANDI")
    print("=" * 60)

    print(
        "Toplam film:",
        len(movies)
    )

    print(
        "Dosya:",
        OUTPUT_FILE
    )


if __name__ == "__main__":
    main()
