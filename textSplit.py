from langchain.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
import pinecone

if __name__ == '__main__':
    loader = UnstructuredFileLoader("epictetus plain text.txt")
    data = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(data)

    embeddings = OpenAIEmbeddings(openai_api_key="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")

    # initialize pinecone
    pinecone.init(
        api_key="8d93fd06-85da-4235-8dd2-128444eb2752",
        environment="us-central1-gcp"
    )
    index_name = "faqs_bot"
    namespace = "book"

    docsearch = Pinecone.from_texts(
      [t.page_content for t in texts], embeddings,
      index_name=index_name, namespace=namespace)
