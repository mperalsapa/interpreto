import React, { createContext, useContext, useState, useEffect } from "react";

const translations = {
  en: {
    language: "Language",
    upload_audio_or_video: "Upload audio or video",
    send: "Send",
    sending: "Sending...",
    download: "Download",
    raw_text: "Raw text",
    format: "Format",
    set_interactive_viewer: "Show interactive",
    set_raw_viewer: "Show raw",
  },
  es: {
    language: "Idioma",
    upload_audio_or_video: "Subir audio o video",
    send: "Enviar",
    sending: "Enviando...",
    download: "Descargar",
    raw_text: "Texto sin formato",
    format: "Formato",
    set_interactive_viewer: "Mostrar interactivo",
    set_raw_viewer: "Mostrar sin formato",
  },
  ca: {
    language: "Idioma",
    upload_audio_or_video: "Puja àudio o vídeo",
    send: "Envia",
    sending: "Enviant...",
    download: "Descarrega",
    raw_text: "Text sense format",
    format: "Format",
    set_interactive_viewer: "Mostrar interactiu",
    set_raw_viewer: "Mostrar sense format",
  },
};

const LanguageContext = createContext();

export const LanguageProvider = ({ children }) => {
  const detectLanguage = () => {
    const saved = localStorage.getItem("lang");
    if (saved && translations[saved]) return saved;

    const browserLang = navigator.language.split("-")[0];
    return translations[browserLang] ? browserLang : "en";
  };

  const [language, setLanguage] = useState(detectLanguage());

  useEffect(() => {
    localStorage.setItem("lang", language);
  }, [language]);

  const t = (key) => {
    return translations[language]?.[key] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => useContext(LanguageContext);
