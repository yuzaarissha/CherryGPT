from operator import itemgetter

from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import Runnable, RunnablePassthrough, RunnableLambda
from langchain.schema.runnable.config import RunnableConfig
from langchain.memory import ConversationBufferMemory

from chainlit.types import ThreadDict
import chainlit as cl
import ollama

from deep_translator import GoogleTranslator
import asyncio

async def translate_text(text, src_lang, dest_lang):
    translator = GoogleTranslator(source=src_lang, target=dest_lang)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, translator.translate, text)


def setup_runnable():
    memory = cl.user_session.get("memory")
    model = ChatOpenAI(streaming=True)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful chatbot"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

    runnable = (
        RunnablePassthrough.assign(
            history=RunnableLambda(memory.load_memory_variables) | itemgetter("history")
        )
        | prompt
        | model
        | StrOutputParser()
    )
    cl.user_session.set("runnable", runnable)


@cl.password_auth_callback
def auth():
    return cl.User(identifier="Cherry")


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("memory", ConversationBufferMemory(return_messages=True))
    setup_runnable()


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    memory = ConversationBufferMemory(return_messages=True)
    root_messages = [m for m in thread["steps"] if m["parentId"] is None]
    for message in root_messages:
        if message["type"] == "user_message":
            memory.chat_memory.add_user_message(message["output"])
        else:
            memory.chat_memory.add_ai_message(message["output"])

    cl.user_session.set("memory", memory)

    setup_runnable()


@cl.on_message
async def on_message(message: cl.Message):
    memory = cl.user_session.get("memory")
    runnable = cl.user_session.get("runnable")
    res = cl.Message(content="")

    translated_question = await translate_text(message.content, 'kk', 'en')

    async for chunk in runnable.astream(
        {"question": translated_question},
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await res.stream_token(chunk)

    await res.send()

    memory.chat_memory.add_user_message(message.content)
    memory.chat_memory.add_ai_message(res.content)


@cl.password_auth_callback
def auth_callback(username: str, password: str) -> cl.User:
    if (username, password) == ("admin", "admin"):
        return cl.User(identifier="admin", metadata={"role": "ADMIN"})
    else:
        return None


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("chat_history", [])
    cl.user_session.set("counter", 0)


@cl.on_message
async def generate_response(query: cl.Message):
    chat_history = cl.user_session.get("chat_history")
    chat_history.append({"role": "user", "content": query.content})

    loader_msg = cl.Message(content="")
    await loader_msg.send()

    await cl.sleep(2)

    loader_msg.content = ""
    await loader_msg.update()

    response = cl.Message(content="")

    translated_query = await translate_text(query.content, 'kk', 'en')
    chat_history[-1]["content"] = translated_query

    answer = ollama.chat(model="llama3", messages=chat_history, stream=True)

    complete_answer = ""
    for token_dict in answer:
        token = token_dict["message"]["content"]
        complete_answer += token

    translated_answer = await translate_text(complete_answer, 'en', 'kk')

    await cl.Message(content=translated_answer).send()

    chat_history.append({"role": "assistant", "content": translated_answer})
    cl.user_session.set("chat_history", chat_history)