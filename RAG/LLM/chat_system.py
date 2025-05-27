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
                else:
                    print(
                        f"[WARN] JSON 문서 없음, VectorStore 생성만 진행 (team_id: {team_id})"
                    )
                    # docs = [
                    #     Document(
                    #         page_content="초기 질문",
                    #         metadata={"답변": "초기 답변", "팀ID": team_id},
                    #     )
                    # ]
                # 임베딩 시도 (docs 비어있어도 embed_documents가 내부에서 안전 처리)
                self.vectorstore.embed_documents(docs, team_id)
                self.vectorstore_obj = self.vectorstore.load_vectorstore(team_id)
        else:
            print("[INFO] 개인 모드: RAG 사용하지 않고 기본 LLM만 응답")

    def search_vectorstore(self, query: str, k=3) -> list:
        return self.vectorstore_obj.similarity_search_with_score(query, k=k)

    def get_prompt(self, retrieved_docs=None):
        messages = [
            ("system", "You are a helpful assistant that answers in Korean."),
            MessagesPlaceholder(variable_name="chat_history"),
        ]

        # 🔥 세션 프롬프트 우선 적용
        selected_prompt = session.get("selected_prompt")
        if selected_prompt:
            messages.append(
                (
                    "system",
                    f"[{selected_prompt['category']}] {selected_prompt['title']} - {selected_prompt['content']}",
                )
            )
        else:
            # 예외 처리: 세션에 없을 경우 기본 프롬프트 or DB (선택)
            print(
                "[INFO] 세션에 선택된 프롬프트 없음. 기본 시스템 프롬프트만 사용합니다."
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

    def calculate_total_tokens(
        self, prompt_template, chat_history, question, final_answer
    ):
        # Prompt 텍스트 변환 및 토큰 계산
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
        else:
            prompt_text = ""

        prompt_tokens = len(self.tokenizer.encode(prompt_text)) if prompt_text else 0

        # Chat History 토큰 계산
        chat_history_text = ""
        if chat_history:
            chat_history_text = "\n".join(
                [f"{msg.type}: {msg.content}" for msg in chat_history]
            )
        chat_history_tokens = (
            len(self.tokenizer.encode(chat_history_text)) if chat_history_text else 0
        )

        # Question 토큰 계산
        question_tokens = len(self.tokenizer.encode(question)) if question else 0

        # Final Answer 토큰 계산
        final_answer_tokens = (
            len(self.tokenizer.encode(final_answer)) if final_answer else 0
        )

        # 총합
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
            retrieved_docs = []
            if self.team_id is not None:
                retrieved_docs = self.search_vectorstore(question)

            # VectorStore 검색 결과 있음
            if retrieved_docs:
                chain = self.get_chain(retrieved_docs)

                # 🔥 VectorStore 응답은 LLM 참고자료로만 사용
                response = chain.stream({"question": question})

                for token in response:
                    print(token.content, end="", flush=True)
                    final_answer += token.content
                    yield token.content

                self.memory.save_context({"inputs": question}, {"output": final_answer})

                # 🔥 토큰 계산
                token_info = self.calculate_total_tokens(
                    prompt_template=self.get_prompt(retrieved_docs),
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

                print("\n[INFO] 토큰 사용량")
                print("──────────────────────────────")
                print(f"질문 (Q):    {token_info['question_tokens']} tokens")
                print(f"답변 (A):   {token_info['final_answer_tokens']} tokens")
                print(f"프롬프트:    {token_info['prompt_tokens']} tokens")
                print(f"대화 기록:  {token_info['chat_history_tokens']} tokens")
                print("──────────────────────────────")
                print(f"총합:       {token_info['total_tokens']} tokens")
                print("──────────────────────────────")

                # 🔹 데이터 출력: 실제 질문, 답변, 프롬프트, 대화 기록
                print("\n[INFO] 실제 데이터 확인")
                print("──────────────────────────────")
                print(f"질문 (Q): {question}")

                print("──────────────────────────────")
                print(f"답변 (A):\n{final_answer}")

                print("──────────────────────────────")
                # 프롬프트 출력
                try:
                    prompt_messages = self.get_prompt(retrieved_docs).format_messages(
                        question=question,
                        chat_history=self.memory.chat_memory.messages,
                    )
                    prompt_text = "\n".join(
                        [f"{msg.type}: {msg.content}" for msg in prompt_messages]
                    )
                    print(f"프롬프트:\n{prompt_text}")
                except Exception as e:
                    print(f"[WARN] 프롬프트 출력 중 오류: {e}")

                print("──────────────────────────────")
                # 대화 기록 출력
                if self.memory.chat_memory.messages:
                    chat_history_text = "\n".join(
                        [
                            f"{msg.type}: {msg.content}"
                            for msg in self.memory.chat_memory.messages
                        ]
                    )
                    print(f"대화 기록:\n{chat_history_text}")
                else:
                    print("대화 기록: (없음)")

                print("──────────────────────────────")
                if self.session_summary is None:
                    self.session_summary = self.summarize_messages(
                        self.memory.chat_memory.messages
                    )

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
                return  # ✅ 이제는 yield response 대신 LLM이 생성한 답변이 출력됩니다

            chain = self.get_chain(retrieved_docs)
            response = chain.stream({"question": question})

            for token in response:
                print(token.content, end="", flush=True)
                final_answer += token.content
                yield token.content

            self.memory.save_context({"inputs": question}, {"output": final_answer})

            # 🔥 토큰 계산
            token_info = self.calculate_total_tokens(
                prompt_template=self.get_prompt(retrieved_docs),
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

            print("\n[INFO] 토큰 사용량")
            print("──────────────────────────────")
            print(f"질문 (Q):    {token_info['question_tokens']} tokens")
            print(f"답변 (A):   {token_info['final_answer_tokens']} tokens")
            print(f"프롬프트:    {token_info['prompt_tokens']} tokens")
            print(f"대화 기록:  {token_info['chat_history_tokens']} tokens")
            print("──────────────────────────────")
            print(f"총합:       {token_info['total_tokens']} tokens")
            print("──────────────────────────────")

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

            # # 🔹 데이터 출력: 실제 질문, 답변, 프롬프트, 대화 기록
            # print("\n[INFO] 실제 데이터 확인")
            # print("──────────────────────────────")
            # print(f"질문 (Q): {question}")

            # print("──────────────────────────────")
            # print(f"답변 (A):\n{final_answer}")

            # print("──────────────────────────────")
            # # 프롬프트 출력
            # try:
            #     prompt_messages = self.get_prompt(retrieved_docs).format_messages(
            #         question=question, chat_history=self.memory.chat_memory.messages
            #     )
            #     prompt_text = "\n".join(
            #         [f"{msg.type}: {msg.content}" for msg in prompt_messages]
            #     )
            #     print(f"프롬프트:\n{prompt_text}")
            # except Exception as e:
            #     print(f"[WARN] 프롬프트 출력 중 오류: {e}")

            # print("──────────────────────────────")
            # # 대화 기록 출력
            # if self.memory.chat_memory.messages:
            #     chat_history_text = "\n".join(
            #         [
            #             f"{msg.type}: {msg.content}"
            #             for msg in self.memory.chat_memory.messages
            #         ]
            #     )
            #     print(f"대화 기록:\n{chat_history_text}")
            # else:
            #     print("대화 기록: (없음)")

            # print("──────────────────────────────")

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
