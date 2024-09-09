import httpx, sys, os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'my_llm')))
from my_llm.config import SERVICE_KEY


date = (datetime.now() - timedelta(days=14)).strftime('%Y%m%d')
ticker = '000660'

SERVICE_KEY = SERVICE_KEY

url = f'https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo?serviceKey={SERVICE_KEY}&resultType=json&beginBasDt={date}&likeSrtnCd={ticker}'

def fetch_data():
    with httpx.Client() as client:
        response = client.get(url)
        return response.json()

data = fetch_data()['response']['body']['items']['item']

stock = ''

for d in data:
    stock += str(d['basDt']) + '에' + str(d['itmsNm']) + '의 종가는 ' + str(d['clpr']) + '입니다./'