"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import styles from "./Sidebar.module.css";

const docLinks = [
  { label: "Why SquadHost?", href: "#why-squadhost" },
  { label: "What is SquadHost?", href: "#what-is-squadhost" },
  { label: "Installation", href: "#installation" },
  { label: "Usage", href: "#usage" },
  { label: "Monitoring & Alerts", href: "#monitoring-alerts" },
  { label: "Troubleshooting", href: "#troubleshooting" },
  { label: "Contributions", href: "#contributions" },
];

const LINK_HEIGHT_DESKTOP = 2.8 * 16; // 2.8rem in px
const VISIBLE_ITEMS_DESKTOP = 5;
const MIDDLE_INDEX_DESKTOP = Math.floor(VISIBLE_ITEMS_DESKTOP / 2); // 2

const VISIBLE_ITEMS_MOBILE = 3;
const MIDDLE_INDEX_MOBILE = Math.floor(VISIBLE_ITEMS_MOBILE / 2); // 1

export default function Sidebar() {
  const [activeId, setActiveId] = useState("");
  const [isMobile, setIsMobile] = useState(false);
  const navRef = useRef<HTMLElement>(null);

  // ── Detect mobile (width ≤ 768px) ──
  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth <= 768);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  // ── Track active section from main-content scroll ──
  const handleScroll = useCallback(() => {
    const container = document.getElementById("main-content");
    if (!container) return;

    const scrollTop = container.scrollTop;
    const sections = docLinks
      .map((link) => document.getElementById(link.href.replace("#", "")))
      .filter(Boolean) as HTMLElement[];

    let currentId = "";
    for (const section of sections) {
      if (section.offsetTop - container.offsetTop <= scrollTop + 100) {
        currentId = section.id;
      } else {
        break;
      }
    }
    setActiveId(currentId);
  }, []);

  useEffect(() => {
    const container = document.getElementById("main-content");
    if (!container) return;

    container.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll(); // initial
    return () => container.removeEventListener("scroll", handleScroll);
  }, [handleScroll]);

  // ── Auto‑scroll sidebar to keep active link centered (desktop vertically, mobile horizontally) ──
  useEffect(() => {
    if (!navRef.current || !activeId) return;

    const activeIndex = docLinks.findIndex((l) => l.href.replace("#", "") === activeId);
    if (activeIndex === -1) return;

    if (isMobile) {
      // Mobile: scroll horizontally so active link is the middle of 3
      const linkElements = navRef.current.children;
      if (linkElements.length === 0) return;

      // Use the first link's width as base (all links are equal width)
      const linkWidth = (linkElements[0] as HTMLElement).offsetWidth;
      const desiredLeft = (activeIndex - MIDDLE_INDEX_MOBILE) * linkWidth;
      navRef.current.scrollTo({
        left: Math.max(0, desiredLeft),
        behavior: "smooth",
      });
    } else {
      // Desktop: scroll vertically so active link is the middle of 5
      const desiredTop = (activeIndex - MIDDLE_INDEX_DESKTOP) * LINK_HEIGHT_DESKTOP;
      navRef.current.scrollTo({
        top: Math.max(0, desiredTop),
        behavior: "smooth",
      });
    }
  }, [activeId, isMobile]);

  return (
    <aside className={styles.sidebar}>
      {/* Back to Portfolio */}
    <a
      href="https://seturaman.me"
      className={styles.backLink}
      target="_blank"
      rel="noopener noreferrer"
    >
      ← Back to Portfolio
    </a>

    <div className={styles.logo}>
      <a href="/">SquadHost Docs</a>
    </div>

      <nav className={styles.nav} ref={navRef}>
        {docLinks.map((link) => {
          const id = link.href.replace("#", "");
          const isActive = activeId === id;
          return (
            <a
              key={link.href}
              href={link.href}
              className={`${styles.link} ${isActive ? styles.active : ""}`}
            >
              <span className={styles.linkText}>{link.label}</span>
            </a>
          );
        })}
      </nav>
          {/* GitHub Link */}
    <a
      href="https://github.com/SeturamanKumar/SquadHost"
      className={styles.githubLink}
      target="_blank"
      rel="noopener noreferrer"
    >
      View on GitHub ↗
    </a>

    </aside>
  );
}
