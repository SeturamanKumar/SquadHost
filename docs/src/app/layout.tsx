// docs/src/app/layout.tsx
import type { Metadata } from "next";
import Sidebar from "@/components/Sidebar/Sidebar";
import "./globals.css";
import styles from "./layout.module.css";

export const metadata: Metadata = {
  title: "SquadHost Docs – Minecraft Server Hosting on AWS",
  description: "Self‑host your own Minecraft server on AWS with scale‑to‑zero pricing.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className={styles.container}>
          <Sidebar />
          <main className={styles.main} id="main-content">
            <div className={styles.content}>{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}
