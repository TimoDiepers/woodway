import React from "react";
import ReactDOM from "react-dom/client";
import TalkApp from "./TalkApp";
import "../index.css";
import "../vaul.css";
import "../ui/deck/deck.css";
import "./frame.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <TalkApp />
  </React.StrictMode>,
);
