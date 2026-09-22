import json
import re
from bs4 import BeautifulSoup
from curl_cffi import requests


def main():
  base_url = 'https://www.fullhdfilmizlesene.now/filmizle/turkce-dublaj-filmler-1'
  movies_data = []

  # Gerçek bir tarayıcının gönderdiği standart başlıklar
  headers = {
      'Accept': (
          'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
      ),
      'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache',
      'Referer': 'https://www.fullhdfilmizlesene.now/',
      'Sec-Ch-Ua': (
          '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"'
      ),
      'Sec-Ch-Ua-Mobile': '?0',
      'Sec-Ch-Ua-Platform': '"Windows"',
      'Sec-Fetch-Dest': 'document',
      'Sec-Fetch-Mode': 'navigate',
      'Sec-Fetch-Site': 'same-origin',
      'Sec-Fetch-User': '?1',
      'Upgrade-Insecure-Requests': '1',
  }

  print('Genişletilmiş başlıklar ile liste sayfası taranıyor...')
  try:
    response = requests.get(
        base_url, impersonate='chrome', headers=headers, timeout=30
    )
    print(f'Liste sayfası yanıt kodu: {response.status_code}')

    if response.status_code != 200:
      print(f'Erişim reddedildi! Sayfa içeriği: {response.text[:200]}')
      return

    html_content = response.text
  except Exception as e:
    print(f'Bağlantı hatası: {e}')
    return

  soup = BeautifulSoup(html_content, 'html.parser')
  movies = soup.select('li.film')
  print(f'Başarılı! Toplam {len(movies)} film kutusu bulundu.')

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

    stream_url = ''
    if link:
      try:
        detail_res = requests.get(
            link, impersonate='chrome', headers=headers, timeout=30
        )
        if detail_res.status_code == 200:
          m3u8_matches = re.findall(
              r'https?://[^\s<>"]+?\.m3u8[^\s<>"]*', detail_res.text
          )
          if m3u8_matches:
            stream_url = m3u8_matches[0]
      except Exception as e:
        print(f'   -> Detay sayfası çekilemedi: {e}')

    print(f'Yakalanan Stream URL: {stream_url}')

    movies_data.append({
        'title': title,
        'link': link,
        'poster': img_url,
        'stream_url': stream_url,
    })

  with open('movies.json', 'w', encoding='utf-8') as f:
    json.dump(movies_data, f, ensure_ascii=False, indent=4)

  print(
      '\nİşlem tamam! Veriler movies.json dosyasına yazıldı. Toplam işlenen:'
      f' {len(movies_data)}'
  )


if __name__ == '__main__':
  main()
