import { NavLink } from "react-router-dom";
import { useLanguage } from "../i18n/LanguageContext";

export default function Navbar() {
  const { language, setLanguage } = useLanguage();
  const { t } = useLanguage();

  const handleLangChange = (e) => {
    setLanguage(e.target.value);
  };

  return (
    <nav>
      <div className="flex items-center justify-between bg-gray-800 p-4 text-white">
        <NavLink to="/" className="text-lg font-bold hover:text-gray-300">
          Interpreto
        </NavLink>

        <div>
          <label
            htmlFor="format"
            className="h-full rounded-lg rounded-r-none border border-gray-300 bg-gray-50 p-2 pl-3 text-gray-900 dark:border-gray-700 dark:bg-gray-700 dark:text-gray-100"
          >
            {t("language")}
          </label>
          <select
            id="format"
            onChange={handleLangChange}
            value={language}
            className="h-full rounded-lg rounded-l-none border border-gray-300 bg-gray-50 p-2 text-gray-900 dark:border-gray-700 dark:bg-gray-700 dark:text-gray-100"
          >
            <option value="en">English</option>
            <option value="es">Español</option>
            <option value="ca">Català</option>
          </select>
        </div>
      </div>
    </nav>
  );
}
