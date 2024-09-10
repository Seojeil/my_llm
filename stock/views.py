from django.shortcuts import render
import httpx, sys, os
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter

def index(request):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'my_llm')))
    from my_llm.config import SERVICE_KEY
    
    date = (datetime.now() - timedelta(days=14)).strftime('%Y%m%d')
    stock_number = request.GET.get('stock_number')
    
    if not stock_number or len(stock_number) != 6:
        return render(request, 'stock/index.html')
    
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
        
        os.environ['USER_AGENT'] = 'MyLangChainApp/1.0'
        
        llm = ChatOpenAI(model="gpt-4o-mini")
        
        path = "stock/articles"
        loader = DirectoryLoader(path, glob="**/*.txt", loader_cls=lambda p: TextLoader(p, encoding="utf-8"), silent_errors=False)
        docs = loader.load()
        
        if not docs:
            raise ValueError("No documents were loaded. Please check the file path and file contents.")
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)
        
        if not splits:
            raise ValueError("Document splitting resulted in an empty list. Please check document contents.")

        vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())

        retriever = vectorstore.as_retriever()
        prompt = ChatPromptTemplate.from_messages([("user", """
        You are a financial consultant. The user asks you about a specific stock.
        Based on the context provided and the given stock price, predict the stock's price movement and provide the expected closing price for the day.
        If the context's date is recent, it should be given more weight in the evaluation.
        The response must be in Korean.

        Question: {question}

        Context: {context}

        Stock Data: {stock}

        Answer:
        """)])

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            {
                "context": retriever | format_docs,
                "question": RunnablePassthrough(),
                "stock": lambda _: stock,
                }
            | prompt
            | llm
            | StrOutputParser()
        )

        result = rag_chain.invoke(f"Please predict the change in the stock price of {name} today.")

        context = {
            'result': result,
        }
        return render(request, 'stock/index.html', context)


def article(request):
    if request.method == 'POST':
        input_corporation = request.POST.get('corporation')
        input_date = request.POST.get('date')
        input_article = request.POST.get('article')
        
        if not input_article:
            return render(request, 'stock/articles.html')
        
        input_data = input_corporation + ' ' + str(input_date) + input_article
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f'user_data_{timestamp}.txt'
        
        file_path = os.path.join('stock', 'articles', file_name)
        
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(input_data + '\n')
        
        return render(request, 'stock/index.html')
    else:
        return render(request, 'stock/articles.html')