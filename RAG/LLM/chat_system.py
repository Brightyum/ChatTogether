from dotenv import load_dotenv
from operator import itemgetter
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from server.DataBase.user_prompts_function import UserPrompt
from server.DataBase.user_qna_save import UserQnaSave
from vectorstore import VectorStore

MAX_MEMORY_LENGTH = 4



class ChatSystem:
    def __init__(self, user_id=None, team_id=None):
        load_dotenv()
        self.user_id = user_id
        self.memory = self.get_memory()
        self.chain = self.get_chain()
        self.session_summary = None
        self.team_id = team_id
        self.vectorstore = VectorStore()
        self.load_vectorstore = self.vectorstore.load_vectorstore(team_id=self.team_id)
    
    def search_vectorstore(self, query: str, k=3) -> list:
        embedding_model = self.vectorstore.embedding.get_embedding_model()
        query_vector = embedding_model.embed_query(query)
        result = self.load_vectorstore.similarity_search_by_vector(query_vector, k=k)

        return result
     
    def get_prompt(self, retrieved_docs=None):
        user_prompt = UserPrompt()
        prompt_list = user_prompt.getPrompt(self.user_id)

        messages = [
            ("system", "You are an helpful assistant that answers in Korean."),
            MessagesPlaceholder(variable_name="chat_history"),
        ]

        if prompt_list:
            for prompt in prompt_list:
                messages.append(
                    (
                        "system",
                        f"[{prompt['category']}] {prompt['title']} - {prompt['content']}"
                    )
                )

        if retrieved_docs:
            context = ""
            for doc in retrieved_docs:
                context += f"문서: {doc.page_content}\n\n"
            
            system_message = f"다음은 참고할 문서입니다:\n{context}"
            
            messages.append(("system", system_message))

        messages.append(("human", "#Question: {question}"))

        result_prompt = ChatPromptTemplate.from_messages(messages)
        return result_prompt

    def get_llm(self):
        llm = ChatOpenAI(model_name="gpt-4o", temperature=0.5)  # max_tokens=350

        return llm

    def get_memory(self):
        memory = ConversationBufferMemory(
            return_messages=True, memory_key="chat_history"
        )
        # 메모리 변수를 빈 딕셔너리로 초기화
        memory.load_memory_variables({})

        return memory

    def get_runnable(self):
        # RunnableLambda - 함수 매핑
        # chat_history = {'chat_history': [대화기록]}
        # itemgetter('키 이름') - 딕셔너리에 키이름의 키를 가진 value값을 반환
        # RunnalblePassthrough - 입력 쌍을 배출
        # runnable 객체가 받는 매서드의 반환값 + chat_history
        runnable = RunnablePassthrough.assign(
            chat_history=RunnableLambda(self.memory.load_memory_variables)
            | itemgetter("chat_history")
        )
        return runnable

    def get_chain(self, retrieved_docs=None):
        if self.team_id is not None and retrieved_docs:
            prompt = self.get_prompt(retrieved_docs)
            runnable = self.get_runnable()
            llm = self.get_llm()

            team_chain = runnable | prompt | llm
            return team_chain
        else:
            runnable = self.get_runnable()
            prompt = self.get_prompt()
            llm = self.get_llm()

            chain = runnable | prompt | llm
            return chain

    def run(self, question: str): 

        final_answer = ""
        try:
            # team_id가 있는 경우 RAG시스템 수행
            retrieved_docs = []
            if self.team_id is not None:
                retrieved_docs = self.search_vectorstore(question)
                if retrieved_docs:
                    print(f"team_id: {self.team_id}, {len(retrieved_docs)}개 문서 검색됨")
                else:
                    print(f"유사 문서가 없어 기본 프롬프트를 사용하겠습니다.")
            
            chain = self.get_chain(retrieved_docs)
            
            response = chain.stream({"question": question})

            for token in response:
                print(token.content, end="", flush=True)
                content = token.content
                final_answer += token.content
                yield content

            self.memory.save_context({"inputs": question}, {"output": final_answer})

            if self.session_summary is not None:
                self.save_to_db(self.user_id, question, final_answer, self.session_summary)

            self.check_memory_limit()

            return final_answer
        
        except Exception as e:
            yield f"\n[에러 발생]: {str(e)}"


    def check_memory_limit(self):
        messages = self.memory.chat_memory.messages
        if len(messages) > MAX_MEMORY_LENGTH:
            # 대화들 중 오래된 4개 요약
            summary = self.summarize_messages(messages)

            # 최초의 요약만 session_summary에 저장
            if self.session_summary is None:
                self.session_summary = summary
                db = self.get_db()
                db.save_history_chat_messages(self.user_id, messages, self.session_summary)

            # 최신 대화는 메모리에 저장
            self.memory.chat_memory.messages = messages[-MAX_MEMORY_LENGTH:]
            self.memory.chat_memory.add_user_message("[이전 대화 요약]")
            self.memory.chat_memory.add_ai_message(summary)

    def summarize_messages(self, messages):
        summary_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "다음 사용자와 AI 간의 대화를 맥락을 유지하며 한글로 간결히 요약하세요.",
                ),
                (
                    "human",
                    "\n".join([f"{m.type.upper()}: {m.content}" for m in messages]),
                ),
            ]
        )
        chain = summary_prompt | self.get_llm() | StrOutputParser()
        return chain.invoke({})

    def save_to_db(self, user_id, question, final_answer, session_summary ):
        db = self.get_db()
        db.save_chat_messages(user_id, question, final_answer, session_summary)
    
    def get_db(self):
        db = UserQnaSave()
        return db
