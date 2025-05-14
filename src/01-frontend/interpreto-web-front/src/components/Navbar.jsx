import { NavLink } from "react-router-dom";
import { useLanguage } from "../i18n/LanguageContext";

export default function Navbar() {
    const { language, setLanguage } = useLanguage();
    const { t } = useLanguage();

    const handleLangChange = (e) => {
        setLanguage(e.target.value);
    }

    return (
        <nav>
            <div className="flex items-center justify-between p-4 bg-gray-800 text-white">
                <NavLink to="/" className="hover:text-gray-300 text-lg font-bold">Interpreto</NavLink>

                <div>
                    <label htmlFor="format" className=" h-full p-2 pl-3 border border-gray-300 dark:border-gray-700 rounded-lg rounded-r-none bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 ">{t("language")}</label>
                    <select
                        id="format"
                        onChange={handleLangChange}
                        value={language}
                        className="h-full p-2 border border-gray-300 dark:border-gray-700 rounded-lg rounded-l-none bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                    >
                        <option value="en">English</option>
                        <option value="es">Español</option>
                        <option value="ca">Català</option>
                    </select>
                </div>
            </div>
        </nav>)
}
