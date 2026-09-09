"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { 
  Network, 
  Cpu, 
  Bot, 
  Workflow, 
  Sparkles, 
  Menu, 
  X, 
  ArrowRight,
  Terminal,
  HelpCircle,
  Download,
  Layers
} from "lucide-react";
import { GithubIcon } from "../ui/GithubIcon";

interface NavbarProps {
  onOpenDownload?: () => void;
}

export function Navbar({ onOpenDownload }: NavbarProps) {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { label: "Features", href: "/#features", icon: <Layers className="w-3.5 h-3.5" /> },
    { label: "Architecture", href: "/#architecture", icon: <Workflow className="w-3.5 h-3.5" /> },
    { label: "Interactive Mascot", href: "/#mascot", icon: <Sparkles className="w-3.5 h-3.5" /> },
    { label: "Models & Roadmap", href: "/#models-roadmap", icon: <Cpu className="w-3.5 h-3.5" /> },
    { label: "FAQ", href: "/#faq", icon: <HelpCircle className="w-3.5 h-3.5" /> },
  ];

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-[#18181B]/90 backdrop-blur-xl border-b border-white/10 shadow-[0_4px_30px_rgba(0,0,0,0.5)] py-3"
          : "bg-transparent py-5"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          {/* Brand Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="relative w-9 h-9 rounded-xl bg-[#222227] border border-white/10 flex items-center justify-center overflow-hidden p-1.5 transition-transform duration-300 group-hover:scale-105 group-hover:border-[#DA7756]/50">
              <Image
                src="/ruexis_logo.svg"
                alt="RUEXIS AI Logo"
                width={32}
                height={32}
                className="w-full h-full object-contain"
              />
            </div>
            <div className="flex items-center">
              <span className="font-heading font-bold text-lg tracking-wider text-[#F4F3EE] group-hover:text-[#DA7756] transition-colors flex items-center gap-2">
                RUEXIS <span className="text-xs px-1.5 py-0.5 rounded bg-[#DA7756]/20 text-[#DA7756] font-mono border border-[#DA7756]/30">AI</span>
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden xl:flex items-center gap-1 bg-[#1C1C20]/80 border border-white/8 rounded-full px-3 py-1.5 backdrop-blur-md">
            {navLinks.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                className="flex items-center gap-1.5 text-xs font-medium text-[#9E9E99] hover:text-[#F4F3EE] px-3 py-1 rounded-full hover:bg-white/5 transition-all duration-200"
              >
                {link.icon}
                <span>{link.label}</span>
              </Link>
            ))}
          </nav>

          {/* Action CTAs */}
          <div className="hidden sm:flex items-center gap-2.5">
            {/* Download Desktop App Button (triggers 1-week countdown modal) */}
            <button
              onClick={onOpenDownload}
              className="group flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-xl bg-[#DA7756] text-white hover:bg-[#E48666] transition-all duration-200 shadow-[0_0_20px_-4px_rgba(218,119,86,0.5)] hover:shadow-[0_0_25px_-2px_rgba(218,119,86,0.7)] cursor-pointer"
            >
              <Download className="w-3.5 h-3.5 transition-transform duration-200 group-hover:-translate-y-0.5" />
              <span>Download App</span>
            </button>

            <Link
              href="/#mascot"
              className="flex items-center gap-1.5 text-xs font-semibold px-3.5 py-2 rounded-xl bg-[#222227] border border-white/10 text-[#F4F3EE] hover:bg-[#292930] hover:border-white/20 transition-all"
            >
              <Sparkles className="w-3.5 h-3.5 text-[#DA7756]" />
              <span>Mascot</span>
            </Link>

            <a
              href="https://github.com/varunchandra10/Paper-2-Project"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-xl bg-[#222227] border border-white/10 text-[#9E9E99] hover:text-[#F4F3EE] hover:border-white/20 transition-colors"
              title="GitHub Repository"
            >
              <GithubIcon className="w-4 h-4" />
            </a>
          </div>

          {/* Mobile Hamburger */}
          <div className="flex items-center gap-2 xl:hidden">
            <button
              onClick={onOpenDownload}
              className="text-xs font-medium px-3 py-1.5 rounded-lg bg-[#DA7756] text-white flex items-center gap-1.5"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download</span>
            </button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-xl bg-[#222227] border border-white/10 text-[#F4F3EE]"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu Dropdown */}
        {mobileMenuOpen && (
          <div className="xl:hidden mt-3 p-4 rounded-2xl bg-[#1C1C20] border border-white/10 shadow-2xl flex flex-col gap-2">
            {navLinks.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 text-sm font-medium text-[#9E9E99] hover:text-[#F4F3EE] px-3 py-2 rounded-xl hover:bg-white/5"
              >
                {link.icon}
                <span>{link.label}</span>
              </Link>
            ))}
            <div className="border-t border-white/10 pt-3 mt-2 flex flex-col gap-2">
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  onOpenDownload?.();
                }}
                className="flex items-center justify-center gap-2 text-sm font-semibold px-4 py-2.5 rounded-xl bg-[#DA7756] text-white"
              >
                <Download className="w-4 h-4" />
                <span>Download Desktop App</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
