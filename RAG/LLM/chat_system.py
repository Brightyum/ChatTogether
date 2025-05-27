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
from server.DataBase.user_qna_token import UserQnaToken
from RAG.vectorstore import VectorStore
from RAG.load import Load
from RAG.split import Split
from flask import session
import os
import tiktoken

MAX_MEMORY_LENGTH = 4


class ChatSystem:
    def __init__(self, user_id=None, team_id=None):
        load_dotenv()
        self.user_id = user_id
        self.team_id = team_id
        self.memory = self.get_memory()
        self.session_summary = None
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        if self.team_id is not None:
            self.load = Load(team_id=team_id)
            self.vectorstore = VectorStore()
            index_path = os.path.join(self.vectorstore.VECTORSTORE_PATH, str(team_id))
            index_file = os.path.join(index_path, "index.faiss")
            pkl_file = os.path.join(index_path, "index.pkl")

            if os.path.exists(index_file) and os.path.exists(pkl_file):
                print(f"[INFO] FAISS 인덱스 로드 (team_id: {team_id})")
                self.vectorstore_obj = self.vectorstore.load_vectorstore(team_id)
            else:
                print(f"[INFO] 인덱스 없음, JSON → 임베딩 진행 (team_id: {team_id})")
                docs = self.load.get_json_to_documents()
                if docs:
                    self.vectorstore.embed_documents(docs, team_id)
                self.vectorstore_obj = self.vectorstore.load_vectorstore(team_id)
        else:
            print("[INFO] 개인 모드: RAG 사용하지 않고 기본 LLM만 응답")

    def search_vectorstore(self, query: str, k=3) -> list:
        return self.vectorstore_obj.similarity_search_with_score(query, k=k)

    def summarize_documents(self, retrieved_docs) -> str:
        """
        retrieved_docs: [(Document, score), ...] 형태의 리스트
        반환: 문서 요약 텍스트 (str)
        """
        doc_text = "\n\n".join(
            [
                f"문서 (score: {score:.4f}): {doc.page_content}"
                for doc, score in retrieved_docs
            ]
        )

        summary_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "다음 문서들의 내용을 요약해 주세요. 각 문서의 핵심 내용을 요약하며, 전체 내용을 사용자의 질문과 관련된 형태로 통합해 주세요.",
                ),
                ("human", doc_text),
            ]
        )

        chain = summary_prompt | self.get_llm() | StrOutputParser()
        summary = chain.invoke({})
        return summary

    def get_prompt(self, summarized_context=None):
        messages = [
            ("system", "You are a helpful assistant that answers in Korean."),
            MessagesPlaceholder(variable_name="chat_history"),
        ]

        selected_prompt = session.get("selected_prompt")
        if selected_prompt:
            messages.append(
                (
                    "system",
                    f"[{selected_prompt['category']}] {selected_prompt['title']} - {selected_prompt['content']}",
                )
            )

        if summarized_context:
            messages.append(
                (
                    "system",
                    f"""
다음은 참고할 문서의 요약입니다. 반드시 이 내용을 답변으로 하여 질문에 답변하세요.
{summarized_context}
""",
                )
            )

        messages.append(("human", "#Question: {question}"))
        return ChatPromptTemplate.from_messages(messages)

    def get_llm(self):
        return ChatOpenAI(model_name="gpt-4o", temperature=0)

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

    def get_chain(self, summarized_context=None):
        prompt = self.get_prompt(summarized_context)
        return self.get_runnable() | prompt | self.get_llm()

    def calculate_total_tokens(
        self, prompt_template, chat_history, question, final_answer
    ):
        prompt_text = ""
        if prompt_template:
            try:
                prompt_messages = prompt_template.format_messages(
                    question=question, chat_history=chat_history
                )
                prompt_text = "\n".join(
                    [f"{msg.type}: {msg.content}" for msg in prompt_messages]
                )
            except Exception as e:
                print(f"[WARN] Prompt 변환 오류: {e}")

        prompt_tokens = len(self.tokenizer.encode(prompt_text)) if prompt_text else 0
        chat_history_text = (
            "\n".join([f"{msg.type}: {msg.content}" for msg in chat_history])
            if chat_history
            else ""
        )
        chat_history_tokens = (
            len(self.tokenizer.encode(chat_history_text)) if chat_history_text else 0
        )
        question_tokens = len(self.tokenizer.encode(question)) if question else 0
        final_answer_tokens = (
            len(self.tokenizer.encode(final_answer)) if final_answer else 0
        )

        total_tokens = (
            prompt_tokens + chat_history_tokens + question_tokens + final_answer_tokens
        )
        return {
            "prompt_tokens": prompt_tokens,
            "chat_history_tokens": chat_history_tokens,
            "question_tokens": question_tokens,
            "final_answer_tokens": final_answer_tokens,
            "total_tokens": total_tokens,
        }

    def run(self, question: str):
        final_answer = ""
        try:
            summarized_context = None
            retrieved_docs = []

            if self.team_id is not None:
                retrieved_docs = self.search_vectorstore(question)
                if retrieved_docs:
                    summarized_context = self.summarize_documents(retrieved_docs)

            chain = self.get_chain(summarized_context)
            response = chain.stream({"question": question})

            for token in response:
                print(token.content, end="", flush=True)
                final_answer += token.content
                yield token.content

            self.memory.save_context({"inputs": question}, {"output": final_answer})

            # 🔥 검색된 문서와 score 출력
            if retrieved_docs:
                print("\n\n🔍 [참고한 문서 목록]")
                for idx, (doc, score) in enumerate(retrieved_docs, 1):
                    print(
                        f"{idx}. (score: {score:.4f}) {doc.page_content[:100]}..."
                    )  # 문서 일부만 출력

                # 문서 정보도 yield로 전달
                doc_info = "\n".join(
                    [
                        f"{idx}. (score: {score:.4f}) {doc.page_content[:100]}..."
                        for idx, (doc, score) in enumerate(retrieved_docs, 1)
                    ]
                )
                yield f"\n\n🔍 [참고한 문서 목록]\n{doc_info}"

            token_info = self.calculate_total_tokens(
                prompt_template=self.get_prompt(summarized_context),
                chat_history=self.memory.chat_memory.messages,
                question=question,
                final_answer=final_answer,
            )

            self.save_to_token_db(
                user_id=self.user_id,
                question=question,
                answer=final_answer,
                prompt_tokens=token_info["prompt_tokens"],
                chat_history_tokens=token_info["chat_history_tokens"],
                question_tokens=token_info["question_tokens"],
                final_answer_tokens=token_info["final_answer_tokens"],
                total_token=token_info["total_tokens"],
            )

            if self.session_summary is None:
                self.session_summary = self.summarize_messages(
                    self.memory.chat_memory.messages
                )

            self.save_to_db(self.user_id, question, final_answer, self.session_summary)
            if self.team_id is not None:
                self.save_team_qna_to_db(
                    self.user_id,
                    self.team_id,
                    question,
                    final_answer,
                    self.session_summary,
                )

            self.check_memory_limit()

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
                    """
                    다음 사용자와 AI 간의 대화를 맥락을 유지하며 한글로 요약을 하세요.
                    AI가 이 요약문을 보았을때 사용자와 나누었던 이전 대화내용을 파악 할 수 있어야 한다.
                    사용자는 무조건 이전 대화에 대한 질문을 할 것 이다.
                    """,
                ),
                (
                    "human",
                    "\n".join([f"{m.type.upper()}: {m.content}" for m in messages]),
                ),
            ]
        )
        chain = summary_prompt | self.get_llm() | StrOutputParser()
        return chain.invoke({})

    def load_previous_conversation(self, conversation_data):
        """
        DB에서 불러온 conversation_id별 대화 데이터를 메모리에 추가하고,
        요약(summarize_messages) 처리 후 메모리에 최종 등록.

        :param conversation_data: [{Personal_Asw: "질문", Personal_Rsp: "답변"}, ...]
        """
        if not conversation_data:
            print("[INFO] 불러올 대화 데이터가 없습니다.")
            return

        # 1. 대화 기록을 memory에 추가
        for entry in conversation_data:
            question = entry.get("Personal_Asw", "").strip()
            answer = entry.get("Personal_Rsp", "").strip()

            if question:
                self.memory.chat_memory.add_user_message(question)
            if answer:
                self.memory.chat_memory.add_ai_message(answer)

        # 2. 요약 생성 후 memory에 추가
        messages = self.memory.chat_memory.messages
        if messages:
            summary = self.summarize_messages(messages)
            self.memory.chat_memory.messages = messages[-MAX_MEMORY_LENGTH:]
            self.memory.chat_memory.add_user_message("[이전 대화 요약]")
            self.memory.chat_memory.add_ai_message(summary)
            self.session_summary = summary

            print("[INFO] 이전 대화 기록이 요약 및 메모리에 등록되었습니다.")
            print(f"[요약 내용]: {summary}")

    def save_team_qna_to_db(
        self, user_id, team_id, question, final_answer, session_summary
    ):
        self.get_db().save_team_chat_messages(
            user_id, team_id, question, final_answer, session_summary
        )

    def save_to_db(self, user_id, question, final_answer, session_summary):
        print("저장을 시도하겠습니다.")
        self.get_db().save_chat_messages(
            user_id, question, final_answer, session_summary
        )
        print(
            f"user_id: {user_id}, question: {question}, final_answer: {final_answer}, summary: {session_summary}"
        )

    def save_to_token_db(
        self,
        user_id,
        question,
        answer,
        prompt_tokens,
        chat_history_tokens,
        question_tokens,
        final_answer_tokens,
        total_token,
    ):
        self.get_db(user_id).save_qna_token(
            user_id,
            question,
            answer,
            prompt_tokens,
            chat_history_tokens,
            question_tokens,
            final_answer_tokens,
            total_token,
        )

    def get_db(self, user_id=None):
        if user_id:
            return UserQnaToken()
        else:
            return UserQnaSave()
