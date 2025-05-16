import React, { createContext, useContext, useState, useEffect } from "react";

const translations = {
  en: {
    language: "Language",
    upload_audio_or_video: "Upload audio or video",
    upload: "Upload",
    uploading: "Uploading...",
    download: "Download",
    raw_text: "Raw text",
    format: "Format",
    set_interactive_viewer: "Show interactive",
    set_raw_viewer: "Show raw",
    upload_complete_wait_a_moment: "Upload complete, wait a moment",
    not_found_title: "Not found",
    not_found_message: "Sorry, the page you are looking for does not exist.",
    go_home: "Go home",
  },
  es: {
    language: "Idioma",
    upload_audio_or_video: "Subir audio o video",
    upload: "Enviar",
    uploading: "Enviando...",
    download: "Descargar",
    raw_text: "Texto sin formato",
    format: "Formato",
    set_interactive_viewer: "Mostrar interactivo",
    set_raw_viewer: "Mostrar sin formato",
    upload_complete_wait_a_moment: "Envío completo, espera un momento",
    not_found_title: "No encontrado",
    not_found_message: "Lo sentimos, la página que buscas no existe.",
    go_home: "Ir al inicio",
  },
  ca: {
    language: "Idioma",
    upload_audio_or_video: "Puja àudio o vídeo",
    upload: "Envia",
    uploading: "Enviant...",
    download: "Descarrega",
    raw_text: "Text sense format",
    format: "Format",
    set_interactive_viewer: "Mostrar interactiu",
    set_raw_viewer: "Mostrar sense format",
    upload_complete_wait_a_moment: "Enviament complet, espera un moment",
    not_found_title: "No trobat",
    not_found_message: "Ho sentim, la pàgina que busques no existeix.",
    go_home: "Anar a l'inici",
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
