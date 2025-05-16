import { useNavigate } from "react-router-dom";
import { useLanguage } from "../i18n/LanguageContext";
import Navbar from "./Navbar";
import { NavLink } from "react-router-dom";

export default function NotFoundPage() {
  const { t } = useLanguage();

  return (
    <div className="flex min-h-screen min-w-screen flex-col justify-center bg-gray-100 dark:bg-gray-900">
      <Navbar />
      <div className="mx-auto my-auto flex w-100 flex-col gap-3 rounded-md bg-white p-6 shadow-md dark:bg-gray-800 dark:shadow-lg">
        <h1 className="text-4xl dark:text-white">{t("not_found_title")}</h1>
        <p className="dark:text-white">{t("not_found_message")}</p>
        <NavLink
          to="/"
          className="rounded-lg border border-gray-300 bg-gray-50 p-2 pl-3 text-center text-gray-900 shadow-md hover:bg-gray-200 dark:border-gray-800 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"
        >
          {t("go_home")}
        </NavLink>
      </div>
    </div>
  );
}
