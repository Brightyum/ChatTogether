from dotenv import load_dotenv
from operator import itemgetter
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from server.DataBase.user_prompts_function import UserPrompt
from server.DataBase.user_qna_save import UserQnaSave
from RAG.vectorstore import VectorStore
import os

MAX_MEMORY_LENGTH = 4


class ChatSystem:
    def __init__(self, user_id=None, team_id=None):
        load_dotenv()
        self.user_id = user_id
        self.team_id = team_id
        self.memory = self.get_memory()
        self.session_summary = None
        self.vectorstore = VectorStore()

        index_path = os.path.join(
            self.vectorstore.VECTORSTORE_PATH,
            str(team_id) if team_id is not None else "",
        )
        index_file = os.path.join(index_path, "index.faiss")
        pkl_file = os.path.join(index_path, "index.pkl")

        if os.path.exists(index_file) and os.path.exists(pkl_file):
            print(f"[INFO] FAISS 인덱스 로드 (team_id: {team_id})")
            self.vectorstore_obj = self.vectorstore.load_vectorstore(
                team_id=self.team_id
            )
        else:
            print(
                f"[INFO] 인덱스 파일이 없어 set_vectorstore() 실행 (team_id: {team_id})"
            )
            self.vectorstore.set_vectorstore(team_id=self.team_id)
            self.vectorstore_obj = self.vectorstore.load_vectorstore(
                team_id=self.team_id
            )

    def search_vectorstore(self, query: str, k=3) -> list:
        return self.vectorstore_obj.similarity_search_with_score(query, k=k)

    def get_prompt(self, retrieved_docs=None):
        user_prompt = UserPrompt()
        prompt_list = user_prompt.getPrompt(self.user_id)

        messages = [
            ("system", "You are a helpful assistant that answers in Korean."),
            MessagesPlaceholder(variable_name="chat_history"),
        ]

        if prompt_list:
            for prompt in prompt_list:
                messages.append(
                    (
                        "system",
                        f"[{prompt['category']}] {prompt['title']} - {prompt['content']}",
                    )
                )

        if retrieved_docs:
            context = ""
            for doc, score in retrieved_docs:
                context += f"문서 (score: {score:.4f}): {doc.page_content}\n\n"
            messages.append(("system", f"다음은 참고할 문서입니다:\n{context}"))

        messages.append(("human", "#Question: {question}"))
        return ChatPromptTemplate.from_messages(messages)

    def get_llm(self):
        return ChatOpenAI(model_name="gpt-4o", temperature=0.5)

    def get_memory(self):
        memory = ConversationBufferMemory(
            return_messages=True, memory_key="chat_history"
        )
        memory.load_memory_variables({})
        return memory

    def get_runnable(self):
        return RunnablePassthrough.assign(
            chat_history=RunnableLambda(self.memory.load_memory_variables)
            | itemgetter("chat_history")
        )

    def get_chain(self, retrieved_docs=None):
        prompt = (
            self.get_prompt(retrieved_docs) if retrieved_docs else self.get_prompt()
        )
        return self.get_runnable() | prompt | self.get_llm()

    def run(self, question: str):
        final_answer = ""
        try:
            retrieved_docs = []
            if self.team_id is not None:
                retrieved_docs = self.search_vectorstore(question)
                if retrieved_docs:
                    print(
                        f"team_id: {self.team_id}, {len(retrieved_docs)}개 문서 검색됨"
                    )
                else:
                    print("유사 문서가 없어 기본 프롬프트를 사용하겠습니다.")

            chain = self.get_chain(retrieved_docs)
            response = chain.stream({"question": question})

            for token in response:
                print(token.content, end="", flush=True)
                final_answer += token.content
                yield token.content

            self.memory.save_context({"inputs": question}, {"output": final_answer})

            if self.session_summary is not None:
                self.save_to_db(
                    self.user_id, question, final_answer, self.session_summary
                )
                if self.team_id is not None:
                    self.save_team_qna_to_db(
                        self.user_id,
                        self.team_id,
                        question,
                        final_answer,
                        self.session_summary,
                    )

            self.check_memory_limit()
            return final_answer

        except Exception as e:
            yield f"\n[에러 발생]: {str(e)}"

    def check_memory_limit(self):
        messages = self.memory.chat_memory.messages
        if len(messages) > MAX_MEMORY_LENGTH:
            summary = self.summarize_messages(messages)
            if self.session_summary is None:
                self.session_summary = summary
                db = self.get_db()
                db.save_history_chat_messages(
                    self.user_id, messages, self.session_summary
                )
                db.save_history_team_chat_messages(
                    self.user_id, self.team_id, messages, self.session_summary
                )
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

    def save_team_qna_to_db(
        self, user_id, team_id, question, final_answer, session_summary
    ):
        self.get_db().save_team_chat_messages(
            user_id, team_id, question, final_answer, session_summary
        )

    def save_to_db(self, user_id, question, final_answer, session_summary):
        self.get_db().save_chat_messages(
            user_id, question, final_answer, session_summary
        )

    def get_db(self):
        return UserQnaSave()
