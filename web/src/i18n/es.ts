export const es = {
  app: {
    name: "Judicial RAG",
    tagline: "Extrae y clasifica variables a partir de documentos PDF judiciales.",
    workspace: "Espacio de trabajo",
  },
  nav: {
    overview: "Resumen",
    documents: "Documentos",
    settings: "Ajustes",
  },
  common: {
    loading: "Cargando…",
    configured: "Configurada",
    missing: "Falta",
    cancel: "Cancelar",
    save: "Guardar",
    close: "Cerrar",
    notSet: "Sin definir",
    dash: "—",
  },
  theme: {
    light: "Claro",
    dark: "Oscuro",
  },
  locale: {
    en: "English",
    es: "Español",
  },
  profile: {
    title: "Perfil",
    account: "Cuenta Supabase",
    llm: "LLM",
    activeLlmKey: "Clave LLM activa",
    embeddings: "Embeddings",
    hfKey: "Clave Hugging Face",
    tokens: "Tokens de generación",
    tokensHint: "Solo esta sesión. Las llamadas de embedding no se incluyen.",
    signOut: "Cerrar sesión",
    keys: "Claves API",
    theme: "Tema",
    language: "Idioma",
  },
  keys: {
    title: "Claves API de sesión",
    intro:
      "Sustituciones opcionales solo para esta sesión del navegador. Los valores no se vuelven a mostrar tras guardar. Si un campo está vacío, se usan las claves del entorno del servidor.",
    llmLabel: "Clave LLM",
    llmHint: "Variable de entorno del proveedor activo:",
    hfLabel: "Clave Hugging Face",
    hfHint: "Se usa para embeddings cuando la recuperación está activa.",
    clearLlm: "Quitar sustitución LLM",
    clearHf: "Quitar sustitución Hugging Face",
    saved: "Claves actualizadas.",
  },
  run: {
    run: "Ejecutar pipeline",
    reset: "Reiniciar",
    hint: "Sube PDFs y guarda el esquema primero.",
  },
  overview: {
    title: "Resumen",
    documents: "Documentos",
    documentsHint: "PDFs en esta sesión",
    schema: "Esquema",
    saved: "Guardado",
    draft: "Borrador",
    schemaSavedHint: "pregunta(s)",
    schemaDraftHint: "Guarda el esquema para ejecutar",
    questions: "Preguntas",
    questionsHint: "En el esquema guardado",
    answered: "Respondidas",
    answeredHint: "Filas que no son not_found",
    recent: "Documentos recientes",
    noDocuments: "Aún no hay PDFs en esta sesión.",
  },
  documents: {
    title: "Documentos",
    subtitle: "PDFs aceptados en esta sesión, con estado y horas.",
    name: "Nombre",
    status: "Estado",
    accepted: "Aceptado",
    finished: "Finalizado",
    empty: "Aún no hay PDFs en esta sesión.",
  },
  documentDetail: {
    back: "Documentos",
    notFound: "Documento no encontrado.",
    backLink: "Volver a documentos",
    finished: "finalizado",
    accepted: "aceptado",
    answers: "Respuestas",
    noAnswers: "Aún no hay respuestas para este documento.",
  },
  settings: {
    title: "Ajustes",
    subtitle: "Preguntas, guardar esquema y los tres niveles de sesión.",
    typesTitle: "Tipos de pregunta",
    typesIntro:
      "Cada tipo usa la instrucción en pipeline/rag_agent.py. El texto editable es la pregunta, el formato de salida y las notas.",
  },
  help: {
    overview: {
      title: "Resumen",
      body:
        "Vista general de la sesión: PDFs aceptados, si hay esquema guardado y cuántas respuestas se encontraron. Ejecuta el pipeline tras subir y guardar. Reiniciar borra PDFs y resultados pero mantiene esquema y niveles.",
    },
    documents: {
      title: "Documentos",
      body:
        "Sube PDFs y sigue cada archivo desde listo hasta extracción, embedding, respuesta, hecho o error. Abre una fila para ver respuestas cuando el pipeline terminó ese archivo.",
    },
    documentDetail: {
      title: "Detalle del documento",
      body:
        "Estado y marcas de tiempo de un PDF. Las respuestas y citas solo aparecen si el pipeline completó ese archivo.",
    },
    settings: {
      title: "Ajustes",
      body:
        "Define preguntas y guarda el esquema antes de ejecutar. Los ajustes avanzados eligen parser, troceado y recuperación. La instrucción compartida del agente no se edita aquí.",
    },
    run: {
      title: "Ejecutar pipeline",
      body:
        "Procesa cada PDF aceptado con el esquema guardado. El progreso se actualiza en vivo; un fallo no detiene el resto.",
    },
    schema: {
      title: "Esquema de preguntas",
      body:
        "Cada fila es una variable a extraer. Guarda el esquema para usarlo en ejecuciones. Los borradores se pierden al recargar hasta guardar.",
    },
    tiers: {
      title: "Niveles avanzados",
      body:
        "Parser, troceado y recuperación equilibran velocidad y calidad. Afectan a la siguiente ejecución en esta sesión.",
    },
    profile: {
      title: "Perfil",
      body:
        "El correo y los modelos vienen de la configuración del servidor. Los tokens son solo de generación en esta sesión. Cerrar sesión termina la sesión y borra las subidas.",
    },
    keys: {
      title: "Claves API",
      body:
        "Las sustituciones de sesión viven en memoria en el servidor hasta cerrar sesión o caducar. Nunca se devuelven en las respuestas de la API.",
    },
  },
}
