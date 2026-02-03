import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
    title: 'GlucoLumin Clinical App',
    description: 'Clinical Validation System for GlucoLumin',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body className="min-h-screen bg-gray-50 text-slate-900">{children}</body>
        </html>
    );
}
