"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { 
  Workflow, 
  Layers, 
  Cpu, 
  Play, 
  Menu, 
  X,
  ExternalLink
} from "lucide-react";
import { GithubIcon } from "../ui/GithubIcon";

export function Navbar() {
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
    { label: "Workflow", href: "#workflow", icon: <Workflow className="w-3.5 h-3.5" /> },
    { label: "Features", href: "#features", icon: <Layers className="w-3.5 h-3.5" /> },
    { label: "Architecture", href: "#architecture", icon: <Cpu className="w-3.5 h-3.5" /> },
    { label: "Demo", href: "#demo", icon: <Play className="w-3.5 h-3.5" /> },
  ];

  const handleScrollTo = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    if (href.startsWith("#")) {
      e.preventDefault();
      const targetId = href.replace("#", "");
      const elem = document.getElementById(targetId);
      if (elem) {
        elem.scrollIntoView({ behavior: "smooth" });
        setMobileMenuOpen(false);
      }
    }
  };

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
          {/* Brand Logo & Wordmark */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="relative w-8 h-8 rounded-lg bg-[#222227] border border-white/10 flex items-center justify-center overflow-hidden p-1.5 transition-transform duration-300 group-hover:scale-105 group-hover:border-[#DA7756]/50">
              <Image
                src="/ruexis_logo.svg"
                alt="RUEXIS AI Logo"
                width={28}
                height={28}
                className="w-full h-full object-contain"
                priority
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="font-heading font-bold text-base md:text-lg tracking-wider text-[#F4F3EE] group-hover:text-[#DA7756] transition-colors">
                RUEXIS
              </span>
              <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-[#DA7756]/15 text-[#DA7756] border border-[#DA7756]/30 uppercase tracking-wider font-semibold">
                AI
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 bg-[#1C1C20]/80 border border-white/8 rounded-full px-3 py-1.5 backdrop-blur-md">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                onClick={(e) => handleScrollTo(e, link.href)}
                className="flex items-center gap-1.5 text-xs font-medium text-[#9E9E99] hover:text-[#F4F3EE] px-3.5 py-1.5 rounded-full hover:bg-white/5 transition-all duration-200"
              >
                {link.icon}
                <span>{link.label}</span>
              </a>
            ))}
          </nav>

          {/* Action CTAs */}
          <div className="hidden sm:flex items-center gap-3">
            <a
              href="https://github.com/varunchandra10/Paper-2-Project"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-xs font-medium px-3.5 py-2 rounded-xl bg-[#222227] border border-white/10 text-[#F4F3EE] hover:bg-[#292930] hover:border-white/20 transition-all"
            >
              <GithubIcon className="w-4 h-4 text-[#9E9E99]" />
              <span>GitHub</span>
            </a>

            <a
              href="#demo"
              onClick={(e) => handleScrollTo(e, "#demo")}
              className="group flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-xl bg-[#DA7756] text-[#F4F3EE] hover:bg-[#E48666] transition-all duration-200 shadow-[0_0_20px_-4px_rgba(218,119,86,0.5)] hover:shadow-[0_0_25px_-2px_rgba(218,119,86,0.7)]"
            >
              <Play className="w-3.5 h-3.5 fill-current transition-transform duration-200 group-hover:scale-110" />
              <span>Watch demo</span>
            </a>
          </div>

          {/* Mobile Hamburger */}
          <div className="flex items-center gap-2 md:hidden">
            <a
              href="#demo"
              onClick={(e) => handleScrollTo(e, "#demo")}
              className="text-xs font-medium px-3 py-1.5 rounded-lg bg-[#DA7756] text-white flex items-center gap-1.5"
            >
              <Play className="w-3 h-3 fill-current" />
              <span>Demo</span>
            </a>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-xl bg-[#222227] border border-white/10 text-[#F4F3EE] focus:outline-none focus:ring-2 focus:ring-[#DA7756]"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu Dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden mt-3 p-4 rounded-2xl bg-[#1C1C20] border border-white/10 shadow-2xl flex flex-col gap-2 animate-in fade-in slide-in-from-top-2 duration-200">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                onClick={(e) => handleScrollTo(e, link.href)}
                className="flex items-center gap-3 text-sm font-medium text-[#9E9E99] hover:text-[#F4F3EE] px-3 py-2.5 rounded-xl hover:bg-white/5 transition-colors"
              >
                {link.icon}
                <span>{link.label}</span>
              </a>
            ))}
            <div className="border-t border-white/10 pt-3 mt-1 flex flex-col gap-2">
              <a
                href="https://github.com/varunchandra10/Paper-2-Project"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 text-sm font-medium px-4 py-2.5 rounded-xl bg-[#222227] border border-white/10 text-[#F4F3EE]"
              >
                <GithubIcon className="w-4 h-4 text-[#9E9E99]" />
                <span>GitHub Repository</span>
                <ExternalLink className="w-3.5 h-3.5 text-[#71717A]" />
              </a>
              <a
                href="#demo"
                onClick={(e) => handleScrollTo(e, "#demo")}
                className="flex items-center justify-center gap-2 text-sm font-semibold px-4 py-2.5 rounded-xl bg-[#DA7756] text-[#F4F3EE]"
              >
                <Play className="w-4 h-4 fill-current" />
                <span>Watch Walkthrough Demo</span>
              </a>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
