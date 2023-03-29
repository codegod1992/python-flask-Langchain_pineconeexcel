import pandas as pd
import numpy as np
import pandas
import json
import string    
import random 
import openai
import os
import json
import textwrap
import re
import pinecone
from flask import Flask, request
from flask_cors import CORS, cross_origin
from numpy.linalg import norm
from numpy import dot
from time import time, sleep
from langchain.llms import OpenAI
from langchain.chains.question_answering import load_qa_chain
from langchain.vectorstores import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from dotenv import load_dotenv

from langchain.document_loaders import PDFMinerLoader
from langchain.document_loaders import UnstructuredWordDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY=os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT=os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME=os.getenv("PINECONE_INDEX_NAME")
UPLOAD_FOLDER=os.getenv("PINECONE_API_KEY")
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/")
@cross_origin()
def home():

    return "Hello!!!!"
 
ALLOWED_EXTENSIONS = {'xls', 'xlsx', 'pdf', 'docx', 'doc'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
@app.route("/getReply", methods=['POST'])
@cross_origin()
def get_response():
    req_data = request.form
    query = req_data['message']
    botId = req_data['botId']
    llm = OpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
    chain = load_qa_chain(llm, chain_type="stuff")
    print("here2", query)

    pinecone.init(
        api_key=PINECONE_API_KEY,
        environment=PINECONE_ENVIRONMENT
    )
    index_name = PINECONE_INDEX_NAME
    namespace = botId
    print("here3")

    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    doclist = Pinecone.from_existing_index(index_name, embeddings, namespace=namespace)
    print("here4")
    docs = doclist.similarity_search(query, include_metadata=True, namespace=namespace) 
    print("here5")

    return str(chain.run(input_documents=docs, question=query))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload", methods=['POST'])     
# @cross_origin()
def upload_bot():
    if request.method == 'POST':
        print("ip address:", request.remote_addr)
        # check if the post request has the file part
        if 'file' not in request.files:
            print('No file part')
            return "No file part"
        file = request.files['file']
        print("bot----", request.form)
        botId = request.form['botname']
        print("botname-----------", botId)
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            print('No selected file')
            return "No selected file" 
        if file and allowed_file(file.filename):
            filename = file.filename
            print("filename============", filename)
            file.save(app.config['UPLOAD_FOLDER'] + filename)
            texts = []
            if(file.filename.rsplit('.', 1)[1].lower() == "pdf"):
                loader = PDFMinerLoader(app.config['UPLOAD_FOLDER'] + file.filename)
                documents = loader.load()
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=0)
                docs = text_splitter.split_documents(documents)
                for doc in docs:
                    texts.append(str(doc))
            elif(file.filename.rsplit('.', 1)[1].lower() == "doc" or file.filename.rsplit('.', 1)[1].lower() == "docx"):
                loader = UnstructuredWordDocumentLoader(app.config['UPLOAD_FOLDER'] + file.filename)
                documents = loader.load()
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=0)
                docs = text_splitter.split_documents(documents)
                for doc in docs:
                    texts.append(str(doc))
            elif (file.filename.rsplit('.', 1)[1].lower() == "xls" or file.filename.rsplit('.', 1)[1].lower() == "xlsx"):
                excel_data_df = pandas.read_excel(app.config['UPLOAD_FOLDER'] + file.filename, sheet_name='FAQs')
                excel_data_df = excel_data_df.replace(np.nan, '')
                thisisjson = excel_data_df.to_json(orient='records')
                trainData = []
                excelarray = json.loads(thisisjson)
                for pair in excelarray:
                    print("pair---", pair)
                    trainData.append(json.dumps(pair))
                
                
                for pair in trainData:
                    if(len(json.dumps(pair)) > 5000):
                        continue
                    texts.append(json.dumps(pair))
            embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

            # initialize pinecone
            pinecone.init(
                api_key=PINECONE_API_KEY,
                environment=PINECONE_ENVIRONMENT
            )
            index_name = PINECONE_INDEX_NAME
            S = 10  
            ran = ''.join(random.choices(string.ascii_uppercase + string.digits, k = S))    
            namespace = str(botId)
            print("text----------", str(texts[0]))
            docsearch = Pinecone.from_texts(
            [t for t in texts], embeddings,
            index_name=index_name, namespace=namespace)
            return {"file":filename, "createdBotId": namespace}
if __name__ == "__main__":
    app.run()
