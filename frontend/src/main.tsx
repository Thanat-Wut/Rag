import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './styles/index.css'  // <-- เพิ่มบรรทัดนี้
import './styles/scroll.css' // <-- เพิ่มบรรทัดนี้

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)