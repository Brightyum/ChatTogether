from dotenv import load_dotenv
from operator import itemgetter
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from server.DataBase.user_prompts_function import UserPrompt


class ChatSystem:
    def __init__(self, user_id=None):
        load_dotenv()
        self.user_id = user_id
        self.memory = self.get_memory()
        self.chain = self.get_chain()

    def get_prompt(self):
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
                        f"[{prompt['category']}] {prompt['title']} - {prompt['content']}",
                    )
                )

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

        final_answer = ""
        try:
            response = self.chain.stream({"question": question})

            for token in response:
                print(token.content, end="", flush=True)
                content = token.content
                final_answer += token.content
                yield content

            self.memory.save_context({"inputs": question}, {"output": final_answer})
            return final_answer
        except Exception as e:
            yield f"\n[에러 발생]: {str(e)}"
