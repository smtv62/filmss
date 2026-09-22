import json
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import requests


def get_stream_url_with_playwright(detail_url):
  """Playwright kullanarak detay sayfasını açar ve ağ trafiğinden m3u8 master linkini yakalar."""
  stream_url = ''
  with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    def handle_request(request):
      nonlocal stream_url
      if '.m3u8' in request.url or 'cdnimages' in request.url:
        if not stream_url and 'vtt' not in request.url:
          stream_url = request.url

    page.on('request', handle_request)

    try:
      page.goto(detail_url, timeout=60000)
      time.sleep(3)
    except Exception as e:
      print(f'Sayfa yüklenme hatası ({detail_url}): {e}')

    browser.close()
  return stream_url


def main():
  base_url = 'https://www.fullhdfilmizlesene.now/filmizle/turkce-dublaj-filmler-1'
  headers = {
      'User-Agent': (
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,'
          ' like Gecko) Chrome/120.0.0.0 Safari/537.36'
      )
  }

  print('Film listesi taranıyor...')
  response = requests.get(base_url, headers=headers)
  soup = BeautifulSoup(response.text, 'html.parser')

  movies_data = []
  movies = soup.find_all('div', class_='box-item') or soup.find_all('article')

  for movie in movies[:3]:
    title_tag = movie.find('a')
    if title_tag:
      title = title_tag.get('title') or title_tag.text.strip()
      link = title_tag.get('href')
      img_tag = movie.find('img')
      img_url = (
          img_tag.get('data-src') or img_tag.get('src') if img_tag else ''
      )

      print(f'İşleniyor: {title}')

      stream_url = ''
      if link:
        stream_url = get_stream_url_with_playwright(link)
        print(f'-> Yakalanan Link: {stream_url}')

      movies_data.append({
          'title': title,
          'link': link,
          'poster': img_url,
          'stream_url': stream_url,
      })

  with open('movies.json', 'w', encoding='utf-8') as f:
    json.dump(movies_data, f, ensure_ascii=False, indent=4)

  print('\nTüm veriler başarıyla movies.json dosyasına kaydedildi!')


if __name__ == '__main__':
  main()
