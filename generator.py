import json
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def get_stream_url_with_page(page, detail_url):
  """Playwright kullanarak detay sayfasını açar ve ağ trafiğinden m3u8 linkini yakalar."""
  stream_url = ''

  def handle_request(request):
    nonlocal stream_url
    if '.m3u8' in request.url or 'cdnimages' in request.url:
      if not stream_url and 'vtt' not in request.url:
        stream_url = request.url

  page.on('request', handle_request)

  try:
    print(f'   -> Detay sayfasına gidiliyor: {detail_url}')
    page.goto(detail_url, timeout=60000)
    time.sleep(3)
  except Exception as e:
    print(f'   -> Sayfa yüklenme hatası: {e}')

  page.remove_listener('request', handle_request)
  return stream_url


def main():
  base_url = 'https://www.fullhdfilmizlesene.now/filmizle/turkce-dublaj-filmler-1'
  movies_data = []

  with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
        ],
    )

    context = browser.new_context(
        user_agent=(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            ' (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        ),
        viewport={'width': 1920, 'height': 1080},
        locale='tr-TR',
    )
    page = context.new_page()

    # Tarayıcının otomasyon izlerini yerleşik JS enjeksiyonu ile tamamen gizliyoruz
    page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.navigator.chrome = {
                runtime: {},
            };
            Object.defineProperty(navigator, 'languages', {
                get: () => ['tr-TR', 'tr', 'en-US', 'en'],
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
        """)

    print('Liste sayfası taranıyor...')
    try:
      page.goto(base_url, timeout=60000)
      time.sleep(6)  # Cloudflare kontrolünün geçilmesi için bekleme

      page_title = page.title()
      print(f'Gezinilen Sayfa Başlığı: {page_title}')

      html_content = page.content()
    except Exception as e:
      print(f'Liste sayfası yüklenemedi: {e}')
      browser.close()
      return

    soup = BeautifulSoup(html_content, 'html.parser')

    movies = soup.select('li.film')
    print(f'Toplam {len(movies)} film kutusu bulundu.')

    # Eğer hala 0 film buluyorsa debug için kaydedelim
    if len(movies) == 0:
      with open('debug.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
      print(
          '⚠️ Hiç film bulunamadı! Sayfa içeriği incelenmek üzere debug.html'
          ' olarak kaydedildi.'
      )

    # Test amaçlı ilk 3 filmi işleyelim
    for movie in movies[:3]:
      a_tag = movie.find('a', class_='tt')
      if not a_tag:
        continue

      link = a_tag.get('href')
      if link and not link.startswith('http'):
        link = 'https://www.fullhdfilmizlesene.now' + link

      title = a_tag.text.strip()

      img_tag = movie.find('img')
      img_url = ''
      if img_tag:
        img_url = (
            img_tag.get('data-src')
            or img_tag.get('src')
            or img_tag.get('data-lazy-src')
            or ''
        )

      print(f'\nFilm: {title}')
      print(f'Link: {link}')
      print(f'Afiş: {img_url}')

      stream_url = ''
      if link:
        stream_url = get_stream_url_with_page(page, link)
        print(f'Yakalanan Stream URL: {stream_url}')

      movies_data.append({
          'title': title,
          'link': link,
          'poster': img_url,
          'stream_url': stream_url,
      })

    browser.close()

  # JSON dosyasına kaydet
  with open('movies.json', 'w', encoding='utf-8') as f:
    json.dump(movies_data, f, ensure_ascii=False, indent=4)

  print(
      '\nİşlem tamam! Veriler movies.json dosyasına yazıldı. Toplam işlenen:'
      f' {len(movies_data)}'
  )


if __name__ == '__main__':
  main()
