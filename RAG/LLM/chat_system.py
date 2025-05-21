from dotenv import load_dotenv
from operator import itemgetter
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

class ChatSystem:
    def __init__(self):
        load_dotenv()
        self.memory = self.get_memory()
        self.chain = self.get_chain()

    def get_prompt(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are an helpful assistant that answers in Korean."),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "#Question:{question}"),
            ]
        )
        return prompt

    def get_llm(self):
        llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
        return llm

    def get_memory(self):
        memory = ConversationBufferMemory(
            return_messages=True, memory_key="chat_history"
        )
        # 메모리 변수를 빈 딕셔너리로 초기화
        memory.load_memory_variables({})

        return memory

    def get_runnable(self):
        runnable = RunnablePassthrough.assign(
            chat_history=RunnableLambda(self.memory.load_memory_variables)
            | itemgetter("chat_history")
        )
        return runnable

    def get_chain(self):
        runnable = self.get_runnable()
        prompt = self.get_prompt()
        llm = self.get_llm()

        chain = runnable | prompt | llm
        return chain

    def run(self, question: str):
        response = self.chain.invoke({"question": question})
        self.memory.save_context({"inputs": question}, {"output": response.content})
        return response.content


