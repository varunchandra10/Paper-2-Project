"use client";

import React, { useState, useEffect } from "react";
import { 
  X, 
  Clock, 
  CheckCircle2, 
  Monitor, 
  Bell, 
  ShieldCheck,
  Check
} from "lucide-react";

interface DownloadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function DownloadModal({ isOpen, onClose }: DownloadModalProps) {
  // 7 Days Countdown Timer (1 week = 604,800 seconds)
  const initialSeconds = 7 * 24 * 60 * 60;
  const [timeLeft, setTimeLeft] = useState(initialSeconds);
  const [email, setEmail] = useState("");
  const [subscribed, setSubscribed] = useState(false);

  useEffect(() => {
    if (!isOpen) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      clearInterval(timer);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const days = Math.floor(timeLeft / (24 * 3600));
  const hours = Math.floor((timeLeft % (24 * 3600)) / 3600);
  const minutes = Math.floor((timeLeft % 3600) / 60);
  const seconds = timeLeft % 60;

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (email.trim()) {
      setSubscribed(true);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
      {/* Dark Glass Backdrop */}
      <div 
        onClick={onClose}
        className="fixed inset-0 bg-black/80 backdrop-blur-md transition-opacity animate-in fade-in duration-200"
      />

      {/* Modal Dialog Card */}
      <div className="relative w-full max-w-xl rounded-3xl bg-[#1C1C20] border border-white/15 p-6 sm:p-8 shadow-2xl z-10 overflow-hidden text-left">
        
        {/* Ambient Top Glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-80 h-32 bg-[#DA7756]/20 rounded-full blur-3xl pointer-events-none -z-10" />

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl bg-[#222227] border border-white/10 text-[#9E9E99] hover:text-[#F4F3EE] hover:bg-[#292930] transition-colors cursor-pointer"
          title="Close dialog"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header Tag */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#DA7756]/15 border border-[#DA7756]/30 text-xs font-mono text-[#DA7756] mb-4 font-semibold">
          <Clock className="w-3.5 h-3.5 animate-spin-slow" />
          <span>OFFICIAL V1.0.0 WINDOWS RELEASE</span>
        </div>

        {/* Title */}
        <h3 className="text-2xl sm:text-3xl font-bold font-heading text-[#F4F3EE] leading-tight mb-2">
          Windows Desktop Binary <span className="text-[#DA7756] glow-accent">in 7 Days</span>
        </h3>

        <p className="text-sm text-[#9E9E99] leading-relaxed mb-6 font-sans">
          The Windows production installer with native Win32 C-FFI taskbar docking and offline Ollama runtime is undergoing final Windows Authenticode code signing. Binary downloads unlock in 1 week.
        </p>

        {/* 1-WEEK COUNTDOWN CARDS */}
        <div className="grid grid-cols-4 gap-2.5 sm:gap-3 mb-6">
          <div className="p-3 rounded-2xl bg-[#18181B] border border-white/10 text-center shadow-inner">
            <span className="text-2xl sm:text-3xl font-black font-mono text-[#F4F3EE] block">
              {String(days).padStart(2, "0")}
            </span>
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#71717A]">
              Days
            </span>
          </div>

          <div className="p-3 rounded-2xl bg-[#18181B] border border-white/10 text-center shadow-inner">
            <span className="text-2xl sm:text-3xl font-black font-mono text-[#DA7756] block">
              {String(hours).padStart(2, "0")}
            </span>
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#71717A]">
              Hours
            </span>
          </div>

          <div className="p-3 rounded-2xl bg-[#18181B] border border-white/10 text-center shadow-inner">
            <span className="text-2xl sm:text-3xl font-black font-mono text-[#38BDF8] block">
              {String(minutes).padStart(2, "0")}
            </span>
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#71717A]">
              Mins
            </span>
          </div>

          <div className="p-3 rounded-2xl bg-[#18181B] border border-white/10 text-center shadow-inner">
            <span className="text-2xl sm:text-3xl font-black font-mono text-[#34D399] block animate-pulse">
              {String(seconds).padStart(2, "0")}
            </span>
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#71717A]">
              Secs
            </span>
          </div>
        </div>

        {/* Windows OS Target Card */}
        <div className="p-4 rounded-2xl bg-[#18181B] border border-[#DA7756]/30 mb-6 shadow-inner flex items-center justify-between">
          <div className="flex items-center gap-3.5">
            <div className="p-2.5 rounded-xl bg-[#DA7756]/15 border border-[#DA7756]/30 text-[#DA7756]">
              <Monitor className="w-5 h-5 text-[#38BDF8]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold font-heading text-[#F4F3EE]">
                  Windows 11 / 10 (64-bit)
                </span>
                <span className="text-[9px] font-mono bg-[#34D399]/15 text-[#34D399] px-2 py-0.5 rounded-full border border-[#34D399]/30 font-semibold">
                  v1.0.0
                </span>
              </div>
              <span className="text-xs font-mono text-[#9E9E99]">
                Native Win32 C-FFI Shell32 Taskbar Docking Installer (.exe)
              </span>
            </div>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 text-xs font-mono text-[#34D399]">
            <Check className="w-4 h-4" />
            <span>Ready for Signing</span>
          </div>
        </div>

        {/* Early Access Notification Form */}
        <div className="p-4 rounded-2xl bg-[#18181B] border border-white/8">
          {subscribed ? (
            <div className="flex items-center gap-3 text-sm font-mono text-[#34D399]">
              <CheckCircle2 className="w-5 h-5 shrink-0" />
              <span>You&#39;re on the priority list! Direct download link will be dispatched to your inbox the second the timer hits zero.</span>
            </div>
          ) : (
            <form onSubmit={handleSubscribe} className="space-y-3">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-[#F4F3EE] font-bold flex items-center gap-1.5">
                  <Bell className="w-3.5 h-3.5 text-[#DA7756]" />
                  Get Day-1 Download Notification
                </span>
                <span className="text-[#71717A]">No spam • 1 email only</span>
              </div>

              <div className="flex gap-2">
                <input
                  type="email"
                  required
                  placeholder="name@university.edu or dev@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="flex-1 bg-[#222227] border border-white/10 rounded-xl px-3.5 py-2 text-xs font-mono text-[#F4F3EE] placeholder:text-[#71717A] focus:outline-none focus:border-[#DA7756]"
                />
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-[#DA7756] text-white font-heading font-bold text-xs hover:bg-[#E48666] transition-all shadow-md cursor-pointer shrink-0"
                >
                  Notify Me
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Footer Note */}
        <div className="mt-4 flex items-center justify-between text-[11px] font-mono text-[#71717A]">
          <span className="flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-[#34D399]" />
            SHA-256 Verified Windows Binary
          </span>
          <span>Open Source on GitHub</span>
        </div>

      </div>
    </div>
  );
}
