import { NavLink, Route, Routes } from 'react-router-dom'
import { AccountPage } from './features/account/AccountPage'
import { ClipsPage } from './features/clips/ClipsPage'

export default function App() {
  return (
    <div className="shell">
      <nav className="nav" aria-label="Primary">
        <NavLink to="/" end>
          Clips
        </NavLink>
        <NavLink to="/account">Instagram</NavLink>
      </nav>
      <main>
        <Routes>
          <Route path="/" element={<ClipsPage />} />
          <Route path="/account" element={<AccountPage />} />
        </Routes>
      </main>
    </div>
  )
}
