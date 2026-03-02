"""
Report endpoints:
- POST /api/v1/cases/{case_id}/report — generate (or return cached) JSON report
- GET  /api/v1/cases/{case_id}/report — return cached report or 404
- GET  /report/{case_id}              — legacy HTML report for judges
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from ..deps import get_supabase, get_mistral
from ..services.report_builder import ReportBuilder

router = APIRouter(tags=["report"])


# ----------------------------------------------------------------
# JSON Report API (new — serves as contract for frontend team)
# ----------------------------------------------------------------

@router.post("/api/v1/cases/{case_id}/report")
async def generate_report(case_id: str) -> dict:
    """Generate (or return cached) the full after-action report."""
    builder = ReportBuilder(get_supabase(), get_mistral())
    report = await builder.build(case_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")
    return report.model_dump()


@router.get("/api/v1/cases/{case_id}/report")
async def get_report(case_id: str) -> dict:
    """Return cached report if it exists, 404 otherwise."""
    report = ReportBuilder.get_cached(case_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail=f"Report not yet generated for case: {case_id}. Use POST to generate.",
        )
    return report.model_dump()


# ----------------------------------------------------------------
# Legacy HTML report (preserved for judge artifacts)
# ----------------------------------------------------------------


def _severity_color(severity: str) -> str:
    return {
        "unknown": "#6b7280",
        "low": "#22c55e",
        "medium": "#eab308",
        "high": "#f97316",
        "critical": "#ef4444",
    }.get(severity, "#6b7280")


def _status_label(status: str) -> str:
    return {
        "intake": "INTAKE",
        "active": "ACTIVE",
        "escalated": "ESCALATED",
        "critical": "CRITICAL",
        "resolved_demo": "RESOLVED",
    }.get(status, status.upper())


def _render_timeline(logs: list) -> str:
    rows = ""
    for log in logs:
        color = log.get("display_color", "blue")
        css_color = {
            "blue": "#3b82f6", "green": "#22c55e", "amber": "#eab308",
            "red": "#ef4444", "purple": "#a855f7",
        }.get(color, "#6b7280")
        flash = " flash" if log.get("display_flash") else ""
        agent = log.get("agent", "")
        event = log.get("event_type", "")
        message = log.get("message", "")
        ts = log.get("created_at", "")[:19].replace("T", " ")
        rows += f"""
        <tr class="log-row{flash}">
            <td class="ts">{ts}</td>
            <td><span class="badge" style="background:{css_color}">{agent}</span></td>
            <td class="event">{event}</td>
            <td>{message}</td>
        </tr>"""
    return rows


def _render_transcripts(transcripts: list) -> str:
    items = ""
    for t in transcripts:
        is_dispatch = t.get("caller_id") == "dispatch"
        direction = "outbound" if is_dispatch else "inbound"
        label = t.get("caller_label") or t.get("caller_id", "")
        lang = (t.get("language") or "").upper()
        text = t.get("original_text", "")
        translation = t.get("translated_text", "")
        confidence = t.get("confidence")
        conf_str = f" ({confidence:.0%})" if confidence else ""

        items += f"""
        <div class="transcript {direction}">
            <div class="transcript-header">
                <span class="direction-arrow">{"DISPATCH →" if is_dispatch else "← CALLER"}</span>
                <strong>{label}</strong>
                <span class="lang-badge">{lang}</span>
                <span class="confidence">{conf_str}</span>
            </div>
            <div class="transcript-text">"{text}"</div>
            {"<div class='transcript-translation'>Translation: " + translation + "</div>" if translation else ""}
        </div>"""
    return items


def _render_evidence_fusion(logs: list) -> str:
    """Render evidence fusion cards from agent_logs with structured data."""
    fusion_logs = [
        l for l in logs
        if l.get("agent") == "evidence_fusion"
        and l.get("event_type") in ("CROSS_MODAL", "CORROBORATION", "EVACUATION", "reasoning")
    ]
    if not fusion_logs:
        return "<p style='color:#737373'>No fusion events recorded</p>"

    cards = ""
    for log in fusion_logs:
        event_type = log.get("event_type", "")
        message = log.get("message", "")
        data = log.get("data") or {}
        ts = (log.get("created_at") or "")[:19].replace("T", " ")
        model = log.get("model", "")

        if event_type in ("CROSS_MODAL", "CORROBORATION"):
            claim = data.get("claim", "Unknown")
            sources = data.get("sources", [])
            confidence = data.get("combined_confidence", 0)
            modalities = data.get("modalities", [])
            is_cross = data.get("cross_modal", False)
            severity_delta = data.get("severity_delta", "")
            evac = data.get("evacuation_triggered", False)

            # Badge color
            border_color = "#ef4444" if is_cross else "#22c55e"
            type_label = "CROSS-MODAL" if is_cross else "CORROBORATED"
            type_bg = "#7f1d1d" if is_cross else "#14532d"

            # Source pills
            source_pills = ""
            for src in sources:
                src_type = src.get("type", "unknown")
                src_conf = src.get("confidence", 0)
                pill_color = "#06b6d4" if "vision" in src_type.lower() or "cctv" in src_type.lower() else "#22c55e"
                source_pills += f'<span style="display:inline-block;background:{pill_color}20;border:1px solid {pill_color}60;color:{pill_color};padding:0.15rem 0.5rem;border-radius:3px;font-size:0.75rem;margin-right:0.35rem">{src_type} ({src_conf:.0%})</span>'

            # Modality icons
            modality_str = " + ".join(modalities)

            # Confidence bar
            conf_pct = int(confidence * 100)
            conf_color = "#ef4444" if conf_pct >= 80 else "#eab308" if conf_pct >= 50 else "#22c55e"

            evac_badge = ""
            if evac:
                evac_badge = '<span style="display:inline-block;background:#7f1d1d;border:1px solid #ef4444;color:#ef4444;padding:0.15rem 0.5rem;border-radius:3px;font-size:0.7rem;font-weight:700;margin-left:0.5rem;letter-spacing:0.05em">EVACUATION TRIGGERED</span>'

            delta_badge = ""
            if severity_delta:
                delta_badge = f'<span style="display:inline-block;background:#422006;border:1px solid #f97316;color:#f97316;padding:0.15rem 0.5rem;border-radius:3px;font-size:0.7rem;margin-left:0.5rem">{severity_delta}</span>'

            cards += f"""
            <div style="background:#141414;border:1px solid {border_color}40;border-left:3px solid {border_color};border-radius:8px;padding:1rem;margin-bottom:0.75rem">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.6rem">
                <div style="display:flex;align-items:center;gap:0.5rem">
                  <span style="display:inline-block;background:{type_bg};border:1px solid {border_color};color:{border_color};padding:0.2rem 0.6rem;border-radius:4px;font-size:0.7rem;font-weight:700;letter-spacing:0.05em">{type_label}</span>
                  <strong style="font-size:0.95rem;color:#f5f5f5">{claim.upper()}</strong>
                  {evac_badge}{delta_badge}
                </div>
                <span style="font-size:0.75rem;color:#525252;font-family:monospace">{ts}</span>
              </div>
              <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.5rem">
                <div>
                  <span style="font-size:0.7rem;color:#737373;text-transform:uppercase;letter-spacing:0.08em">Sources</span><br>
                  {source_pills}
                </div>
                <div>
                  <span style="font-size:0.7rem;color:#737373;text-transform:uppercase;letter-spacing:0.08em">Modalities</span><br>
                  <span style="font-size:0.85rem;color:#d4d4d4">{modality_str}</span>
                </div>
                <div>
                  <span style="font-size:0.7rem;color:#737373;text-transform:uppercase;letter-spacing:0.08em">Combined Confidence</span><br>
                  <div style="display:flex;align-items:center;gap:0.5rem">
                    <div style="width:80px;height:6px;background:#262626;border-radius:3px;overflow:hidden">
                      <div style="width:{conf_pct}%;height:100%;background:{conf_color};border-radius:3px"></div>
                    </div>
                    <span style="font-size:0.85rem;font-weight:600;color:{conf_color}">{conf_pct}%</span>
                  </div>
                </div>
              </div>
              <div style="font-size:0.75rem;color:#525252;border-top:1px solid #262626;padding-top:0.4rem;margin-top:0.4rem">
                Agent: <span style="color:#a855f7">evidence_fusion</span> · Model: <span style="color:#3b82f6">{model or "mistral-large-latest"}</span>
              </div>
            </div>"""

        elif event_type == "EVACUATION":
            cards += f"""
            <div style="background:#1a0a0a;border:2px solid #ef4444;border-radius:8px;padding:1rem;margin-bottom:0.75rem">
              <div style="display:flex;align-items:center;gap:0.5rem">
                <span style="font-size:1.2rem">🚨</span>
                <strong style="color:#ef4444;font-size:0.95rem;letter-spacing:0.05em">AUTONOMOUS EVACUATION PROTOCOL</strong>
                <span style="font-size:0.75rem;color:#525252;font-family:monospace;margin-left:auto">{ts}</span>
              </div>
              <p style="color:#fca5a5;font-size:0.85rem;margin-top:0.5rem">{message}</p>
            </div>"""

        elif event_type == "reasoning":
            cards += f"""
            <div style="background:#141414;border:1px solid #262626;border-left:3px solid #a855f7;border-radius:8px;padding:0.75rem;margin-bottom:0.75rem">
              <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem">
                <span style="font-size:0.7rem;color:#a855f7;text-transform:uppercase;letter-spacing:0.08em;font-weight:600">Fusion Reasoning</span>
                <span style="font-size:0.75rem;color:#525252;font-family:monospace;margin-left:auto">{ts}</span>
              </div>
              <p style="color:#a3a3a3;font-size:0.85rem;font-style:italic">{message}</p>
              <div style="font-size:0.75rem;color:#525252;margin-top:0.4rem">
                Model: <span style="color:#3b82f6">{model or "mistral-large-latest"}</span>
              </div>
            </div>"""

    return cards


def _render_dispatches(dispatches: list) -> str:
    rows = ""
    for d in dispatches:
        unit = d.get("unit_assigned", "—")
        unit_type = d.get("unit_type", "")
        dest = d.get("destination", "—")
        eta = d.get("eta_minutes", "—")
        status = d.get("status", "")
        voice = d.get("voice_message", "")
        rationale = d.get("rationale", "")
        status_color = {"recommended": "#eab308", "confirmed": "#22c55e", "dispatched": "#3b82f6"}.get(status, "#6b7280")

        rows += f"""
        <tr>
            <td><strong>{unit}</strong></td>
            <td>{unit_type}</td>
            <td>{dest}</td>
            <td>{eta} min</td>
            <td><span class="badge" style="background:{status_color}">{status}</span></td>
            <td class="small">{rationale}</td>
        </tr>"""
    return rows


@router.get("/report/{case_id}", response_class=HTMLResponse)
async def case_report(case_id: str):
    """Render a self-contained HTML case report."""
    supabase = get_supabase()

    try:
        state_result = supabase.table("incident_state") \
            .select("*").eq("case_id", case_id).single().execute()
    except Exception:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    state = state_result.data
    logs = supabase.table("agent_logs") \
        .select("*").eq("case_id", case_id).order("created_at").execute().data
    transcripts = supabase.table("transcripts") \
        .select("*").eq("case_id", case_id).order("created_at").execute().data
    dispatches = supabase.table("dispatches") \
        .select("*").eq("case_id", case_id).order("created_at").execute().data

    severity = state.get("severity", "unknown")
    status = state.get("status", "unknown")
    sev_color = _severity_color(severity)
    created = (state.get("created_at") or "")[:19].replace("T", " ")
    updated = (state.get("updated_at") or "")[:19].replace("T", " ")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DISPATCH — Case {case_id}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: #0a0a0a; color: #e5e5e5; line-height: 1.6;
  }}
  .container {{ max-width: 960px; margin: 0 auto; padding: 2rem; }}
  header {{
    border-bottom: 1px solid #262626; padding-bottom: 1.5rem; margin-bottom: 2rem;
  }}
  .logo {{ font-size: 0.85rem; letter-spacing: 0.2em; color: #737373; text-transform: uppercase; }}
  .logo span {{ color: #ef4444; }}
  h1 {{ font-size: 1.5rem; font-weight: 600; margin-top: 0.5rem; font-family: 'JetBrains Mono', monospace; }}
  .meta {{ display: flex; gap: 1.5rem; margin-top: 0.75rem; font-size: 0.85rem; color: #a3a3a3; }}
  .severity-badge {{
    display: inline-block; padding: 0.25rem 0.75rem; border-radius: 4px;
    font-size: 0.8rem; font-weight: 700; letter-spacing: 0.05em;
    background: {sev_color}20; color: {sev_color}; border: 1px solid {sev_color}40;
  }}
  .status-badge {{
    display: inline-block; padding: 0.25rem 0.75rem; border-radius: 4px;
    font-size: 0.8rem; font-weight: 600; background: #262626; color: #e5e5e5;
  }}

  section {{ margin-bottom: 2.5rem; }}
  h2 {{
    font-size: 0.8rem; letter-spacing: 0.15em; text-transform: uppercase;
    color: #737373; border-bottom: 1px solid #1a1a1a; padding-bottom: 0.5rem;
    margin-bottom: 1rem;
  }}

  /* Summary grid */
  .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }}
  .stat {{ background: #141414; border: 1px solid #262626; border-radius: 8px; padding: 1rem; }}
  .stat-label {{ font-size: 0.75rem; color: #737373; text-transform: uppercase; letter-spacing: 0.1em; }}
  .stat-value {{ font-size: 1.25rem; font-weight: 600; margin-top: 0.25rem; }}

  /* Flags */
  .flags {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem; }}
  .flag {{ background: #1a1a1a; border: 1px solid #333; border-radius: 4px; padding: 0.2rem 0.6rem; font-size: 0.8rem; }}
  .flag.hazard {{ border-color: #ef4444; color: #ef4444; }}
  .flag.injury {{ border-color: #f97316; color: #f97316; }}

  /* Timeline table */
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
  th {{ text-align: left; padding: 0.5rem; border-bottom: 1px solid #262626; color: #737373; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; }}
  td {{ padding: 0.5rem; border-bottom: 1px solid #1a1a1a; vertical-align: top; }}
  .ts {{ font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #737373; white-space: nowrap; }}
  .badge {{ display: inline-block; padding: 0.15rem 0.5rem; border-radius: 3px; font-size: 0.75rem; font-weight: 600; color: #fff; }}
  .event {{ font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #a3a3a3; }}
  .small {{ font-size: 0.8rem; color: #a3a3a3; }}
  tr.flash td {{ background: #1a0a0a; }}

  /* Transcripts */
  .transcript {{
    background: #141414; border: 1px solid #262626; border-radius: 8px;
    padding: 1rem; margin-bottom: 0.75rem;
  }}
  .transcript.outbound {{ border-left: 3px solid #3b82f6; margin-left: 2rem; }}
  .transcript.inbound {{ border-left: 3px solid #22c55e; margin-right: 2rem; }}
  .transcript-header {{ display: flex; gap: 0.75rem; align-items: center; margin-bottom: 0.5rem; font-size: 0.85rem; }}
  .direction-arrow {{ font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #737373; }}
  .lang-badge {{ background: #262626; padding: 0.1rem 0.4rem; border-radius: 3px; font-size: 0.75rem; }}
  .confidence {{ color: #737373; font-size: 0.8rem; }}
  .transcript-text {{ font-style: italic; color: #d4d4d4; }}
  .transcript-translation {{ font-size: 0.85rem; color: #737373; margin-top: 0.5rem; border-top: 1px solid #1a1a1a; padding-top: 0.5rem; }}

  /* Vision */
  .detection {{ display: inline-block; background: #141414; border: 1px solid #262626; border-radius: 6px; padding: 0.5rem 0.75rem; margin: 0.25rem; font-size: 0.85rem; }}

  /* Footer */
  footer {{ text-align: center; padding: 2rem; color: #525252; font-size: 0.8rem; border-top: 1px solid #1a1a1a; margin-top: 2rem; }}
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="logo"><span>●</span> DISPATCH — Incident Intelligence System</div>
    <h1>Case {case_id}</h1>
    <div class="meta">
      <span class="severity-badge">{severity.upper()}</span>
      <span class="status-badge">{_status_label(status)}</span>
      <span>Created: {created} UTC</span>
      <span>Updated: {updated} UTC</span>
    </div>
  </header>

  <section>
    <h2>Incident Summary</h2>
    <div class="summary-grid">
      <div class="stat">
        <div class="stat-label">Incident Type</div>
        <div class="stat-value">{state.get("incident_type") or "—"}</div>
      </div>
      <div class="stat">
        <div class="stat-label">Location</div>
        <div class="stat-value">{state.get("location_normalized") or state.get("location_raw") or "—"}</div>
      </div>
      <div class="stat">
        <div class="stat-label">Callers</div>
        <div class="stat-value">{state.get("caller_count", 0)}</div>
      </div>
      <div class="stat">
        <div class="stat-label">People Involved</div>
        <div class="stat-value">{state.get("people_count_estimate", 0)}</div>
      </div>
      <div class="stat">
        <div class="stat-label">Units Dispatched</div>
        <div class="stat-value">{len(state.get("confirmed_units", []))}</div>
      </div>
      <div class="stat">
        <div class="stat-label">Action Plan Version</div>
        <div class="stat-value">v{state.get("action_plan_version", 0)}</div>
      </div>
    </div>

    <div style="margin-top:1rem">
      <div class="stat-label" style="font-size:0.75rem;color:#737373;text-transform:uppercase;letter-spacing:0.1em;">Hazard Flags</div>
      <div class="flags">
        {"".join(f'<span class="flag hazard">{f}</span>' for f in state.get("hazard_flags", [])) or '<span class="flag">None</span>'}
      </div>
    </div>
    <div style="margin-top:0.75rem">
      <div class="stat-label" style="font-size:0.75rem;color:#737373;text-transform:uppercase;letter-spacing:0.1em;">Injury Flags</div>
      <div class="flags">
        {"".join(f'<span class="flag injury">{f}</span>' for f in state.get("injury_flags", [])) or '<span class="flag">None</span>'}
      </div>
    </div>

    {"<div style='margin-top:1rem'><div class='stat-label' style='font-size:0.75rem;color:#737373;text-transform:uppercase;letter-spacing:0.1em;'>Operator Summary</div><p style=margin-top:0.5rem>" + state.get("operator_summary") + "</p></div>" if state.get("operator_summary") else ""}
  </section>

  <section>
    <h2>Transcripts ({len(transcripts)})</h2>
    {_render_transcripts(transcripts)}
  </section>

  <section>
    <h2>Vision Detections</h2>
    <div>
      {"".join(f"<div class='detection'><strong>{d.get('type', d.get('label', '?'))}</strong> — {d.get('confidence', '?')}</div>" for d in state.get("vision_detections", [])) or "<p style='color:#737373'>No detections</p>"}
    </div>
  </section>

  <section>
    <h2>Evidence Fusion</h2>
    {_render_evidence_fusion(logs)}
  </section>

  <section>
    <h2>Dispatch Units ({len(dispatches)})</h2>
    <table>
      <thead><tr><th>Unit</th><th>Type</th><th>Destination</th><th>ETA</th><th>Status</th><th>Rationale</th></tr></thead>
      <tbody>{_render_dispatches(dispatches)}</tbody>
    </table>
  </section>

  <section>
    <h2>Agent Activity Log ({len(logs)})</h2>
    <table>
      <thead><tr><th>Timestamp</th><th>Agent</th><th>Event</th><th>Message</th></tr></thead>
      <tbody>{_render_timeline(logs)}</tbody>
    </table>
  </section>

  <footer>
    DISPATCH Incident Intelligence System — Generated by TriageNet<br>
    Powered by Mistral AI + ElevenLabs
  </footer>
</div>
</body>
</html>"""

    return HTMLResponse(content=html)
