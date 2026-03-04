import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HR Agent - 인사규정 AI 어시스턴트",
  description: "인사규정에 대해 질문하고 답변을 받으세요",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="antialiased">{children}</body>
    </html>
  );
}
