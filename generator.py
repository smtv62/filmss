import json
import re
from bs4 import BeautifulSoup
from curl_cffi import requests


def main():
  base_url = 'https://www.hdfilmcehennemi.nl'
  # Yeni eklenen filmler sayfası
  target_url = f'{base_url}/load/page/1/home/'

  headers = {
      'Accept': (
          'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
      ),
      'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
      'X-Requested-With': 'fetch',
      'User-Agent': (
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0)'
          ' Gecko/20100101 Firefox/137.0'
      ),
  }

  print('GitHub Actions üzerinden liste taranıyor...')
  try:
    response = requests.get(
        target_url, impersonate='chrome', headers=headers, timeout=30
    )
    print(f'Yanıt kodu: {response.status_code}')

    if response.status_code != 200:
      print('Sayfaya erişilemedi!')
      return

    data = response.json()
    html_content = data.get('html', '')
  except Exception as e:
    print(f'Bağlantı veya JSON parse hatası: {e}')
    return

  soup = BeautifulSoup(html_content, 'html.parser')
  links = soup.select('a')

  m3u_lines = ['#EXTM3U']
  count = 0

  for a_tag in links:
    title = a_tag.get('title')
    href = a_tag.get('href')
    img_tag = a_tag.select_one('img')

    if not title or not href:
      continue

    if not href.startswith('http'):
      href = base_url + href

    poster_url = ''
    if img_tag:
      poster_url = (
          img_tag.get('data-src') or img_tag.get('src') or ''
      )
      if poster_url.startswith('/'):
        poster_url = base_url + poster_url

    # IPTV M3U formatına ekle
    # Not: Gerçek akış linki (m3u8) için detay sayfasına gitmek gerekir, 
    # burada temel kart bilgilerini ve site linkini M3U meta verisi olarak ekliyoruz.
    m3u_lines.append(
        f'#EXTINF:-1 tvg-logo="{poster_url}" group-title="HD Film Cehennemi",{title}'
    )
    m3u_lines.append(href)
    count += 1

    # Test / örnek amaçlı ilk 20 filmi alalım
    if count >= 20:
      break

  # playlist.m3u dosyasına kaydet
  with open('playlist.m3u', 'w', encoding='utf-8') as f:
    f.write('\n'.join(m3u_lines))

  print(f'İşlem tamam! Toplam {count} film playlist.m3u dosyasına yazıldı.')


if __name__ == '__main__':
  main()
