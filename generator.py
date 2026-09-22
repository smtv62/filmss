import json
import re
from bs4 import BeautifulSoup
from curl_cffi import requests


def get_stream_url_from_html(html_content):
  """Detay sayfasının kaynak kodu içindeki .m3u8 uzantılı akış linkini regex ile yakalar."""
  # Sayfa içerisindeki script veya kaynaklarda geçen .m3u8 linklerini arıyoruz
  m3u8_matches = re.findall(r'https?://[^\s<>"]+?\.m3u8[^\s<>"]*', html_content)
  if m3u8_matches:
    return m3u8_matches[0]
  return ''


def main():
  base_url = 'https://www.fullhdfilmizlesene.now/filmizle/turkce-dublaj-filmler-1'
  movies_data = []

  print('curl_cffi ile liste sayfası taranıyor...')
  try:
    # impersonate="chrome" parametresi ile Cloudflare'i tamamen atlatıyoruz
    response = requests.get(base_url, impersonate='chrome', timeout=30)
    print(f'Liste sayfası yanıt kodu: {response.status_code}')

    if response.status_code != 200:
      print('Liste sayfasına erişilemedi!')
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
        print(f'   -> Detay sayfasına gidiliyor: {link}')
        detail_res = requests.get(link, impersonate='chrome', timeout=30)
        if detail_res.status_code == 200:
          stream_url = get_stream_url_from_html(detail_res.text)
      except Exception as e:
        print(f'   -> Detay sayfası çekilemedi: {e}')

    print(f'Yakalanan Stream URL: {stream_url}')

    movies_data.append({
        'title': title,
        'link': link,
        'poster': img_url,
        'stream_url': stream_url,
    })

  # JSON dosyasına kaydet
  with open('movies.json', 'w', encoding='utf-8') as f:
    json.dump(movies_data, f, ensure_ascii=False, indent=4)

  print(
      '\nİşlem tamam! Veriler movies.json dosyasına yazıldı. Toplam işlenen:'
      f' {len(movies_data)}'
  )


if __name__ == '__main__':
  main()
