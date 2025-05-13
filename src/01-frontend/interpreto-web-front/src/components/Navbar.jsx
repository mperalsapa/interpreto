import { NavLink } from "react-router-dom";

export default function Navbar() {
    return (
        <nav>
            <div className="flex items-center justify-between p-4 bg-gray-800 text-white">
                <NavLink to="/" className="hover:text-gray-300 text-lg font-bold">Interpreto</NavLink>

                <button
                    className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                >
                    Subir Archivo
                </button>
            </div>
        </nav>)
}
