import React from "react";
import Image from "next/image";
import { GithubIcon } from "../ui/GithubIcon";
import { project } from "@/data/project";
import { ExternalLink } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-[#131315] border-t border-white/8 pt-16 pb-12 text-[#9E9E99]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 pb-12 border-b border-white/8">
          {/* Brand & Descriptor (6 cols) */}
          <div className="md:col-span-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#222227] border border-white/10 p-1 flex items-center justify-center">
                <Image
                  src="/ruexis_logo.svg"
                  alt="RUEXIS AI Logo"
                  width={24}
                  height={24}
                  className="w-full h-full object-contain"
                />
              </div>
              <span className="font-heading font-bold text-lg text-[#F4F3EE]">
                RUEXIS <span className="text-[#DA7756]">AI</span>
              </span>
            </div>

            <p className="text-xs text-[#9E9E99] leading-relaxed max-w-md font-sans">
              {project.descriptor}. An open research platform translating scientific publications into structured, feasibility-aware PyTorch implementations through an 8-stage compiler pipeline.
            </p>

            <div className="flex items-center gap-2 text-xs font-mono text-[#71717A]">
              <span className="w-2 h-2 rounded-full bg-[#34D399]" />
              <span>Open Source Research Platform</span>
            </div>
          </div>

          {/* Quick Navigation (3 cols) */}
          <div className="md:col-span-3">
            <h4 className="text-xs font-mono uppercase tracking-wider text-[#F4F3EE] mb-4 font-semibold">
              Sections
            </h4>
            <ul className="space-y-2.5 text-xs">
              <li>
                <a href="#workflow" className="hover:text-[#F4F3EE] transition-colors">
                  8-Stage Workflow
                </a>
              </li>
              <li>
                <a href="#features" className="hover:text-[#F4F3EE] transition-colors">
                  Core Capabilities
                </a>
              </li>
              <li>
                <a href="#demo" className="hover:text-[#F4F3EE] transition-colors">
                  Product Demo & Chapters
                </a>
              </li>
              <li>
                <a href="#architecture" className="hover:text-[#F4F3EE] transition-colors">
                  System Architecture
                </a>
              </li>
            </ul>
          </div>

          {/* Resources & Repository (3 cols) */}
          <div className="md:col-span-3">
            <h4 className="text-xs font-mono uppercase tracking-wider text-[#F4F3EE] mb-4 font-semibold">
              Source & Code
            </h4>
            <div className="space-y-3 text-xs">
              <a
                href="https://github.com/varunchandra10/Paper-2-Project"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-[#1C1C20] border border-white/10 text-[#F4F3EE] hover:bg-[#222227] hover:border-white/20 transition-all w-full"
              >
                <GithubIcon className="w-4 h-4 text-[#9E9E99]" />
                <span>GitHub Repository</span>
                <ExternalLink className="w-3.5 h-3.5 text-[#71717A] ml-auto" />
              </a>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#71717A] font-mono">
          <p>© 2026 RUEXIS AI. {project.acronym}.</p>
          <div className="flex items-center gap-3">
            <span>Next.js 16</span>
            <span>•</span>
            <span>TypeScript</span>
            <span>•</span>
            <span>PyTorch</span>
            <span>•</span>
            <span>Python AST</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
