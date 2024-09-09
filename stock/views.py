from django.shortcuts import render
import httpx, sys, os
from datetime import datetime, timedelta

def index(request):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'my_llm')))
    from my_llm.config import SERVICE_KEY
    
    date = (datetime.now() - timedelta(days=14)).strftime('%Y%m%d')
    stock_number = request.GET.get('stock_number')
    
    url = f'https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo?serviceKey={SERVICE_KEY}&resultType=json&beginBasDt={date}&likeSrtnCd={stock_number}'
    
    response = httpx.Client().get(url)
    
    
    data = response.json()['response']['body']['items']['item']
    
    if not data:
        return render(request, 'stock/index.html')
    
    else:
        name = data[0]['itmsNm']
        
        stock = ''
        for d in data:
            stock += str(d['basDt']) + ', ' + str(d['itmsNm']) + '의 종가는 ' + str(d['clpr']) + '입니다. '
        
        context = {
            'stock': stock,
        }
        return render(request, 'stock/index.html', context)


def article(request):
    if request.method == 'POST':
        input_article = request.POST.get('article')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f'user_data_{timestamp}.txt'
        
        file_path = os.path.join('stock', 'articles', file_name)
        
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(input_article + '\n')
        
        return render(request, 'stock/index.html')
    else:
        return render(request, 'stock/articles.html')