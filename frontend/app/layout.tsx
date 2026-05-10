import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "AdhikarAI Dev Chat",
  description: "Developer test UI for Phase 2 text agent"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
