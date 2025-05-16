import { NavLink, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { useLanguage } from "../i18n/LanguageContext";

export default function Navbar() {
  const navigate = useNavigate();
  const { language, setLanguage } = useLanguage();
  const [darkMode, setDarkMode] = useState(true);
  const [administrator, setAdministrator] = useState(false);
  const { t } = useLanguage();

  const handleLangChange = (e) => {
    setLanguage(e.target.value);
  };

  useEffect(() => {
    const theme = document.documentElement.classList.contains("dark");
    setDarkMode(theme);
  }, []);

  useEffect(() => {
    // Check if the user is an administrator
    // reads the administrator value from localStorage
    // if administrator value is existent, set administrator to true
    const admin = localStorage.getItem("administrator-token");
    if (admin) {
      setAdministrator(true);
    } else {
      setAdministrator(false);
    }
  }, []);

  const handleThemeChange = () => {
    if (darkMode) {
      document.documentElement.classList.remove("dark");
      setDarkMode(false);
    } else {
      document.documentElement.classList.add("dark");
      setDarkMode(true);
    }
  };

  return (
    <nav>
      <div className="flex items-center justify-between bg-white p-4 text-gray-900 shadow-sm dark:bg-gray-800 dark:text-white">
        <NavLink to="/" className="text-lg font-bold hover:text-gray-300">
          Interpreto
        </NavLink>
        <div className="flex gap-5">
          {administrator && (
            <button
              className="material-symbols-outlined inline-icon m-0 aspect-square w-10 rounded-full border border-gray-300 p-0 shadow-md hover:bg-gray-200 dark:border-gray-800 dark:bg-gray-700 dark:hover:bg-gray-600"
              onClick={() => {
                navigate("/admin");
              }}
            >
              shield_person
            </button>
          )}
          <button
            onClick={handleThemeChange}
            className="material-symbols-outlined inline-icon m-0 aspect-square w-10 rounded-full border border-gray-300 p-0 shadow-md hover:bg-gray-200 dark:border-gray-800 dark:bg-gray-700 dark:hover:bg-gray-600"
          >
            {darkMode ? "light_mode" : "dark_mode"}
          </button>
          <div className="flex">
            <label
              htmlFor="format"
              className="h-full rounded-lg rounded-r-none border-y border-l border-gray-300 bg-gray-50 p-2 pl-3 text-gray-900 shadow-md hover:bg-gray-200 dark:border-gray-800 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"
            >
              {t("language")}
            </label>
            <select
              id="format"
              onChange={handleLangChange}
              value={language}
              className="h-full rounded-lg rounded-l-none border-y border-r border-gray-300 bg-gray-50 p-2 text-gray-900 shadow-md hover:bg-gray-200 dark:border-gray-800 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"
            >
              <option value="en">English</option>
              <option value="es">Español</option>
              <option value="ca">Català</option>
            </select>
          </div>
        </div>
      </div>
    </nav>
  );
}
