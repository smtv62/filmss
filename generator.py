import json
from bs4 import BeautifulSoup
import requests

url = 'https://www.fullhdfilmizlesene.now/filmizle/turkce-dublaj-filmler-1'
headers = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,'
        ' like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
}

print('Film verileri taranıyor...')
try:
  response = requests.get(url, headers=headers)
  response.raise_for_status()

  soup = BeautifulSoup(response.text, 'html.parser')
  movies_data = []

  # Sitedeki film öğelerini buluyoruz
  movies = soup.find_all('div', class_='box-item') or soup.find_all('article')

  for movie in movies:
    title_tag = movie.find('a')
    if title_tag:
      title = title_tag.get('title') or title_tag.text.strip()
      link = title_tag.get('href')
      img_tag = movie.find('img')
      img_url = (
          img_tag.get('data-src') or img_tag.get('src') if img_tag else ''
      )

      movies_data.append(
          {'title': title, 'link': link, 'poster': img_url, 'stream_url': ''}
      )

  # Elde edilen verileri movies.json dosyasına kaydediyoruz
  with open('movies.json', 'w', encoding='utf-8') as f:
    json.dump(movies_data, f, ensure_ascii=False, indent=4)

  print(
      f'Başarılı! Toplam {len(movies_data)} film movies.json dosyasına'
      ' kaydedildi.'
  )

except Exception as e:
  print(f'Hata oluştu: {e}')
