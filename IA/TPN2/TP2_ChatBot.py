import gradio as gr
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import os
import json
from langchain_groq import ChatGroq
from langchain_core.documents import Document as LangChainDocument
from itertools import groupby
from langchain_community.vectorstores import FAISS
from langchain_cohere import CohereEmbeddings


MAX_MENSAJES_HISTORIAL = 6   # últimos N mensajes (usuario+asistente); bajalo si Groq te da error de tokens
RUTA_TRANSCRIPCION_JSON = "output/transcripcion1.json"

if not os.getenv("COHERE_API_KEY"):
    import getpass
    os.environ["COHERE_API_KEY"] = getpass.getpass("COHERE_API_KEY: ")

if not os.getenv("GROQ_API_KEY"):
    import getpass
    os.environ["GROQ_API_KEY"] = getpass.getpass("GROQ_API_KEY: ")

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)

with open(RUTA_TRANSCRIPCION_JSON, encoding="utf-8") as f:
    turnos1 = json.load(f)

embeddings = CohereEmbeddings(
    model="embed-v4.0"
)

# Reescribe preguntas tipo "¿y quién lo dijo?" como preguntas autocontenidas para el retrieval
prompt_condensar = ChatPromptTemplate.from_template(
    "Dado el historial y la última pregunta del usuario, reescribí la última pregunta "
    "para que se entienda SIN el historial. Si ya es autocontenida, devolvela igual. "
    "Devolvé SOLO la pregunta.\n\nHistorial:\n{historial}\n\nÚltima pregunta: {pregunta}"
)

prompt_chat = ChatPromptTemplate.from_messages([
    ("system",
     "Respondé usando SOLO los fragmentos de la reunión que se muestran abajo. "
     "Si el contexto no alcanza para responder, decilo. Si se pide un listado "
     "(ej. problemáticas y prioridad), ordenalo por criticidad.\n\nContexto:\n{contexto}"),
    MessagesPlaceholder("historial"),
    ("human", "{pregunta}"),
])


def _a_mensajes(historial):
    msgs = []
    for m in historial[-MAX_MENSAJES_HISTORIAL:]:
        c = m["content"]
        if not isinstance(c, str):  # según versión, gradio puede mandar bloques
            c = "".join(b.get("text", "") for b in c if isinstance(b, dict))
        msgs.append(HumanMessage(c) if m["role"] == "user" else AIMessage(c))
    return msgs


def _armar_contexto(docs):
    partes = []
    for d in docs:
        if "hablante" in d.metadata:
            partes.append(f"[{d.metadata['hablante']} · minuto {d.metadata['minuto']}]\n{d.page_content}")
        else:
            partes.append(d.page_content)
    return "\n\n---\n\n".join(partes)


def crear_chat(vectorstore, k: int = 4):
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    parser = StrOutputParser()

    def responder(mensaje, historial):
        msgs = _a_mensajes(historial)

        if msgs:
            txt_hist = "\n".join(
                f"{'Usuario' if isinstance(m, HumanMessage) else 'Asistente'}: {m.content}"
                for m in msgs
            )
            consulta = (prompt_condensar | llm | parser).invoke(
                {"historial": txt_hist, "pregunta": mensaje}
            )
        else:
            consulta = mensaje

        contexto = _armar_contexto(retriever.invoke(consulta))
        return (prompt_chat | llm | parser).invoke(
            {"contexto": contexto, "historial": msgs, "pregunta": mensaje}
        )

    return responder

def crear_vectorstore(turnos: list[dict]):
    """
    Indexa la transcripción agrupada por turno de habla: cada documento es
    un bloque continuo de una persona, con metadata de hablante y minuto.
    Así el retrieval recupera QUIÉN dijo QUÉ y CUÁNDO.
    """
    docs = []
    for hablante, grupo in groupby(turnos, key=lambda t: t["hablante"]):
        grupo = list(grupo)
        minuto = int((grupo[0]["inicio"] or 0) // 60)
        docs.append(LangChainDocument(
            page_content=f"{hablante}: {' '.join(t['texto'] for t in grupo)}",
            metadata={"hablante": hablante, "minuto": minuto},
        ))
    return FAISS.from_documents(docs, embeddings)

vectorstore1 = crear_vectorstore(turnos1)

demo = gr.ChatInterface(
    fn=crear_chat(vectorstore1),   # vectorstore1 = con turnos/hablante; usá vectorstore_txt para la variante TXT
    type="messages",
    title="Asistente de la reunión",
    description="Preguntame lo que quieras sobre la reunión.",
    examples=[
        "¿Qué problemáticas se discutieron y con qué prioridad?",
        "¿Qué personas tienen tareas asignadas?",
    ],
)
demo.launch()   # demo.launch(share=True) para link público temporal