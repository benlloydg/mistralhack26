"use client";

import { useState, useEffect, useRef } from "react";

const DISPATCH_PITCH = () => {
  const [visible, setVisible] = useState(false);
  const [scanLine, setScanLine] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), 200);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setScanLine((prev) => (prev + 1) % 100);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  const stats = [
    { value: "7", label: "AGENTS" },
    { value: "4", label: "LANGUAGES" },
    { value: "2", label: "MODALITIES" },
    { value: "21s", label: "EARLY WARNING" },
    { value: "0", label: "CASUALTIES" },
  ];

  const techStack = [
    { name: "Mistral Large", role: "Triage + Fusion" },
    { name: "Pixtral", role: "Vision Analysis" },
    { name: "ElevenLabs Scribe v2", role: "Multilingual STT" },
    { name: "ElevenLabs TTS", role: "Voice Response" },
    { name: "Pydantic-AI", role: "Agent Framework" },
    { name: "Supabase Realtime", role: "Shared State" },
  ];

  return (
    <div
      ref={containerRef}
      style={{
        minHeight: "100vh",
        background: "#0a0a0c",
        color: "#e8e6e1",
        fontFamily: "'IBM Plex Mono', 'SF Mono', 'Fira Code', monospace",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Scan line effect */}
      <div
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(255,255,255,0.008) 2px,
            rgba(255,255,255,0.008) 4px
          )`,
          pointerEvents: "none",
          zIndex: 10,
        }}
      />

      {/* Subtle moving scan line */}
      <div
        style={{
          position: "fixed",
          top: `${scanLine}%`,
          left: 0,
          right: 0,
          height: "2px",
          background: "linear-gradient(90deg, transparent, rgba(255,120,50,0.06), transparent)",
          pointerEvents: "none",
          zIndex: 10,
        }}
      />

      {/* Grid overlay */}
      <div
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px)
          `,
          backgroundSize: "60px 60px",
          pointerEvents: "none",
          zIndex: 1,
        }}
      />

      <div
        style={{
          maxWidth: "860px",
          margin: "0 auto",
          padding: "80px 40px",
          position: "relative",
          zIndex: 5,
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0)" : "translateY(20px)",
          transition: "all 1.2s cubic-bezier(0.16, 1, 0.3, 1)",
        }}
      >
        {/* System status bar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            marginBottom: "60px",
            fontSize: "10px",
            letterSpacing: "3px",
            textTransform: "uppercase",
            color: "#555",
          }}
        >
          <div
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              background: "#ff6b35",
              boxShadow: "0 0 8px rgba(255,107,53,0.6)",
              animation: "pulse 2s infinite",
            }}
          />
          <span>SYSTEM ACTIVE</span>
          <span style={{ color: "#333" }}>—</span>
          <span>MISTRAL × ELEVENLABS</span>
        </div>

        {/* Title */}
        <div style={{ marginBottom: "16px" }}>
          <h1
            style={{
              fontSize: "clamp(42px, 7vw, 72px)",
              fontWeight: 700,
              letterSpacing: "-2px",
              lineHeight: 0.95,
              margin: 0,
              fontFamily: "'IBM Plex Sans', 'Helvetica Neue', sans-serif",
              color: "#fff",
            }}
          >
            DISPATCH
          </h1>
        </div>

        <p
          style={{
            fontSize: "13px",
            letterSpacing: "4px",
            textTransform: "uppercase",
            color: "#ff6b35",
            margin: "0 0 64px 0",
            fontWeight: 500,
          }}
        >
          Multilingual Incident Intelligence
        </p>

        {/* Divider */}
        <div
          style={{
            height: "1px",
            background: "linear-gradient(90deg, #ff6b35, rgba(255,107,53,0.1), transparent)",
            marginBottom: "48px",
          }}
        />

        {/* Problem */}
        <div style={{ marginBottom: "48px" }}>
          <p
            style={{
              fontSize: "18px",
              lineHeight: 1.75,
              color: "#999",
              margin: 0,
              fontFamily: "'IBM Plex Sans', 'Helvetica Neue', sans-serif",
              fontWeight: 300,
            }}
          >
            Emergency scenes are loud, chaotic, and multilingual. Bystanders shout
            in whatever language they speak. Cameras capture what no one reports.
          </p>
          <p
            style={{
              fontSize: "18px",
              lineHeight: 1.75,
              color: "#e8e6e1",
              margin: "16px 0 0 0",
              fontFamily: "'IBM Plex Sans', 'Helvetica Neue', sans-serif",
              fontWeight: 400,
            }}
          >
            Today, most of that signal is lost.
          </p>
        </div>

        {/* What it does */}
        <div style={{ marginBottom: "56px" }}>
          <div
            style={{
              fontSize: "10px",
              letterSpacing: "3px",
              color: "#555",
              marginBottom: "20px",
              textTransform: "uppercase",
            }}
          >
            SYSTEM
          </div>
          <p
            style={{
              fontSize: "15px",
              lineHeight: 1.85,
              color: "#bbb",
              margin: 0,
              fontFamily: "'IBM Plex Sans', 'Helvetica Neue', sans-serif",
            }}
          >
            DISPATCH is a multi-agent incident intelligence system that monitors
            emergency scenes through CCTV video and ambient audio — no phone
            calls, no 911 operator. ElevenLabs Scribe v2 converts a single live
            audio stream into speaker-segmented, language-tagged intelligence in
            real time. Mistral Large triages severity, fuses that audio evidence
            with Pixtral vision analysis, and recommends response actions.
            ElevenLabs TTS then broadcasts evacuation warnings back to the scene
            in every detected language.
          </p>
        </div>

        {/* Demo section */}
        <div
          style={{
            background: "rgba(255,107,53,0.03)",
            border: "1px solid rgba(255,107,53,0.1)",
            padding: "40px",
            marginBottom: "56px",
            position: "relative",
          }}
        >
          <div
            style={{
              position: "absolute",
              top: "-1px",
              left: "32px",
              background: "#0a0a0c",
              padding: "0 12px",
              fontSize: "10px",
              letterSpacing: "3px",
              color: "#ff6b35",
              textTransform: "uppercase",
              transform: "translateY(-50%)",
            }}
          >
            DEMO SCENARIO
          </div>
          <p
            style={{
              fontSize: "15px",
              lineHeight: 1.85,
              color: "#bbb",
              margin: "0 0 20px 0",
              fontFamily: "'IBM Plex Sans', 'Helvetica Neue', sans-serif",
            }}
          >
            A vehicle collision unfolds in front of a surveillance camera. Four
            bystanders respond in Spanish, English, Mandarin, and French. DISPATCH
            detects the crash simultaneously through an audio spike and a visual
            scene change.
          </p>
          <p
            style={{
              fontSize: "15px",
              lineHeight: 1.85,
              color: "#bbb",
              margin: "0 0 20px 0",
              fontFamily: "'IBM Plex Sans', 'Helvetica Neue', sans-serif",
            }}
          >
            It extracts a trapped-occupant report from Spanish, a child-present
            alert from Mandarin, and a fire warning from French — then
            cross-validates the fire by detecting both smoke and a HAZMAT placard
            in the video feed.
          </p>
          <p
            style={{
              fontSize: "15px",
              lineHeight: 1.85,
              color: "#ddd",
              margin: "0 0 24px 0",
              fontFamily: "'IBM Plex Sans', 'Helvetica Neue', sans-serif",
              fontWeight: 400,
            }}
          >
            The system autonomously issues a trilingual evacuation warning 21
            seconds before an explosion.
          </p>
          <div
            style={{
              fontSize: "28px",
              fontWeight: 700,
              color: "#fff",
              fontFamily: "'IBM Plex Sans', 'Helvetica Neue', sans-serif",
              letterSpacing: "-0.5px",
            }}
          >
            Zero casualties.
          </div>
        </div>

        {/* Stats row */}
        <div
          style={{
            display: "flex",
            gap: "0",
            marginBottom: "56px",
            borderTop: "1px solid #1a1a1e",
            borderBottom: "1px solid #1a1a1e",
          }}
        >
          {stats.map((stat, i) => (
            <div
              key={i}
              style={{
                flex: 1,
                padding: "28px 0",
                textAlign: "center",
                borderRight: i < stats.length - 1 ? "1px solid #1a1a1e" : "none",
              }}
            >
              <div
                style={{
                  fontSize: stat.value === "21s" ? "28px" : "32px",
                  fontWeight: 700,
                  color: stat.value === "0" ? "#ff6b35" : "#fff",
                  fontFamily: "'IBM Plex Sans', sans-serif",
                  marginBottom: "6px",
                }}
              >
                {stat.value}
              </div>
              <div
                style={{
                  fontSize: "9px",
                  letterSpacing: "2px",
                  color: "#555",
                  textTransform: "uppercase",
                }}
              >
                {stat.label}
              </div>
            </div>
          ))}
        </div>

        {/* Tech stack */}
        <div style={{ marginBottom: "64px" }}>
          <div
            style={{
              fontSize: "10px",
              letterSpacing: "3px",
              color: "#555",
              marginBottom: "24px",
              textTransform: "uppercase",
            }}
          >
            BUILT WITH
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "0",
            }}
          >
            {techStack.map((tech, i) => (
              <div
                key={i}
                style={{
                  padding: "14px 0",
                  borderBottom: "1px solid #141416",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "baseline",
                  paddingRight: i % 2 === 0 ? "32px" : "0",
                  paddingLeft: i % 2 === 1 ? "32px" : "0",
                  borderLeft: i % 2 === 1 ? "1px solid #141416" : "none",
                }}
              >
                <span style={{ fontSize: "13px", color: "#ddd" }}>
                  {tech.name}
                </span>
                <span style={{ fontSize: "11px", color: "#555" }}>
                  {tech.role}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer line */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            paddingTop: "32px",
            borderTop: "1px solid #1a1a1e",
          }}
        >
          <span
            style={{
              fontSize: "11px",
              letterSpacing: "6px",
              color: "#333",
              textTransform: "uppercase",
            }}
          >
            DISPATCH
          </span>
          <span
            style={{
              fontSize: "11px",
              color: "#333",
              letterSpacing: "2px",
            }}
          >
            INCIDENT INTELLIGENCE
          </span>
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;700&family=IBM+Plex+Sans:wght@300;400;500;700&display=swap');

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }

        * { box-sizing: border-box; }
        body { margin: 0; background: #0a0a0c; }

        ::selection {
          background: rgba(255,107,53,0.3);
          color: #fff;
        }
      `}</style>
    </div>
  );
};

export default DISPATCH_PITCH;
