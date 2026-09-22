from bs4 import BeautifulSoup
import requests

# Hedef liste sayfası
url = 'https://www.fullhdfilmizlesene.now/filmizle/turkce-dublaj-filmler-1'

# Bot engeline takılmamak için tarayıcı benzeri User-Agent header'ı ekliyoruz
headers = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,'
        ' like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
}

try:
  response = requests.get(url, headers=headers)
  response.raise_for_status()

  # BeautifulSoup ile HTML'i parse ediyoruz
  soup = BeautifulSoup(response.text, 'html.parser')

  # Önceki tarama sonuçlarına göre film öğelerini buluyoruz
  # (Sitenin güncel yapısına göre seçiciler optimize edilebilir)
  movies = soup.find_all('div', class_='box-item') or soup.find_all('article')

  print(f'Toplam {len(movies)} film bulundu.\n')

  for movie in movies[:5]:  # İlk 5 filmi örnek olarak yazdıralım
    title_tag = movie.find('a')
    if title_tag:
      title = title_tag.get('title') or title_tag.text.strip()
      link = title_tag.get('href')
      img_tag = movie.find('img')
      img_url = (
          img_tag.get('data-src') or img_tag.get('src') if img_tag else 'Yok'
      )

      print(f'Film Adı: {title}')
      print(f'Detay Linki: {link}')
      print(f'Afiş URL: {img_url}')
      print('-' * 40)

except Exception as e:
  print(f'Bir hata oluştu: {e}')
