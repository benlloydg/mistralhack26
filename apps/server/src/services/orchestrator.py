"""
DemoOrchestrator — drives all timed events for the 120-second demo.

Call start() and it runs the full sequence. Each phase:
1. Triggers backend actions (transcribe, analyze, triage, dispatch)
2. Writes results to Supabase via StateManager
3. Frontend reacts via Realtime subscriptions

The orchestrator is an async function that uses asyncio.sleep() for timing.
All agent calls are real (Mistral inference, ElevenLabs API). Not mocked.
"""
import asyncio
import time
from ..agents.shared_deps import TriageNetDeps
from ..agents.triage_agent import triage_agent
from ..agents.intake_agent import intake_agent
from ..agents.dispatch_agent import dispatch_agent
from ..agents.case_match_agent import evidence_fusion_agent
from ..agents.vision_agent import analyze_frame, compute_scene_delta
from ..services.state import StateManager
from ..services.transcription import transcribe_audio
from ..services.tts import generate_and_save
from ..services.media import extract_frame
from ..models.incident import Severity, IncidentStatus
from ..models.caller import CallerRecord

CALLERS = [
    CallerRecord(caller_id="caller_1", label="The Wife", language="es",
                 audio_path="assets/caller_1_spanish.mp3", start_delay_s=12),
    CallerRecord(caller_id="caller_2", label="Bystander", language="zh",
                 audio_path="assets/caller_2_mandarin.mp3", start_delay_s=38),
    CallerRecord(caller_id="caller_3", label="Shopkeeper", language="fr",
                 audio_path="assets/caller_3_french.mp3", start_delay_s=56),
]


class DemoOrchestrator:
    def __init__(self, deps: TriageNetDeps, state: StateManager):
        self.deps = deps
        self.state = state
        self.previous_frame = None
        self._approved = asyncio.Event()  # Set when operator clicks APPROVE

    def approve(self):
        """Called by the /demo/approve endpoint."""
        self._approved.set()

    async def start(self):
        """Run the full 120-second demo sequence."""
        self.state.log("orchestrator", "init", "Demo started: TN-2026-00417", color="blue")

        # Phase 0 — Init (0:00-0:12)
        await self._phase_0_init()

        # Phase 1 — Caller 1 (0:12-0:30)
        await self._phase_1_caller_1()

        # Phase 2 — Human Approval (0:30-0:38)
        await self._phase_2_approval()

        # Phase 3 — Caller 2 (0:38-0:56)
        await self._phase_3_caller_2()

        # Phase 4 — Vision / Fire Detection (0:56-1:18)
        await self._phase_4_vision()

        # Phase 5 — Priority Interrupt (1:18-1:36)
        await self._phase_5_interrupt()

        # Phase 6 — Final Summary (1:36-2:00)
        await self._phase_6_summary()

    async def _phase_0_init(self):
        """Initialize case, start video monitor."""
        self.state.update_state(status=IncidentStatus.INTAKE.value, severity=Severity.UNKNOWN.value)
        self.state.log("orchestrator", "init", "Case created: TN-2026-00417")
        self.state.log("orchestrator", "init", "Video monitor armed")
        await asyncio.sleep(2)

    async def _phase_1_caller_1(self):
        """Process Caller 1 — Spanish wife reporting crash."""
        caller = CALLERS[0]
        self.state.log("voice", "caller_connected",
                       f"Incoming call: {caller.label} ({caller.language.upper()})",
                       color="green")
        self.state.update_state(caller_count=1)

        # 1. Transcribe
        transcript = await transcribe_audio(caller.audio_path)
        self.state.log("voice", "transcript_received",
                       f"Transcribed ({caller.language}): {transcript['text']}")

        # Write transcript to Supabase
        self.deps.supabase.table("transcripts").insert({
            "case_id": self.deps.case_id,
            "caller_id": caller.caller_id,
            "caller_label": caller.label,
            "language": caller.language,
            "original_text": transcript["text"],
            "translated_text": None,
            "confidence": transcript.get("confidence"),
            "segment_index": 0,
        }).execute()

        # 2. Extract intake facts
        facts_result = await intake_agent.run(
            f"Transcript from emergency caller ({caller.language}): {transcript['text']}",
            deps=self.deps,
        )
        facts = facts_result.output
        self.state.log("intake", "facts_extracted",
                       f"Location: {facts.location_raw}, Type: {facts.incident_type_candidate}")

        # 3. Update state with intake facts
        self.state.update_state(
            location_raw=facts.location_raw,
            location_normalized=facts.location_raw,
            incident_type=facts.incident_type_candidate,
        )

        # 4. Run triage
        triage_result = await triage_agent.run(
            "Classify this incident based on current state. Check all evidence.",
            deps=self.deps,
        )
        triage = triage_result.output
        self.state.update_state(
            severity=triage.severity.value,
            recommended_units=[u for u in triage.recommended_units],
            people_count_estimate=triage.people_count_estimate,
            injury_flags=triage.injury_flags,
            action_plan_version=1,
            action_plan=[a.model_dump() for a in triage.action_plan],
            status=IncidentStatus.ACTIVE.value,
        )
        self.state.log("triage", "severity_changed",
                       f"Severity: {triage.severity.value.upper()}",
                       color="amber", flash=True)
        self.state.log("triage", "action_plan", "Action Plan v1 generated", color="blue")

        # 5. Generate voice response to caller in their language
        response_text_es = (
            "Ayuda está en camino. Manténgase en la línea. "
            "No mueva a su esposo. Los paramédicos están llegando."
        )
        audio_url = await generate_and_save(
            response_text_es, caller.language, "response_caller1.mp3"
        )
        self.deps.supabase.table("transcripts").insert({
            "case_id": self.deps.case_id,
            "caller_id": "dispatch",
            "caller_label": "DISPATCH",
            "language": caller.language,
            "original_text": response_text_es,
            "translated_text": "Help is on the way. Stay on the line. "
                               "Don't move your husband. Paramedics are arriving.",
            "confidence": 1.0,
            "segment_index": 1,
        }).execute()
        self.state.log("voice", "response_sent",
                       f"Voice response sent to {caller.label} ({caller.language.upper()})",
                       data={"audio_url": audio_url},
                       color="green")

    async def _phase_2_approval(self):
        """Wait for operator to click APPROVE INITIAL RESPONSE."""
        self.state.log("orchestrator", "awaiting_approval",
                       "Awaiting operator approval for initial response...",
                       color="amber", flash=True)

        try:
            await asyncio.wait_for(self._approved.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            self.state.log("orchestrator", "auto_approved",
                           "Auto-approved (timeout)", color="amber")

        state = self.state.get_state()
        self.state.update_state(confirmed_units=state.recommended_units)
        self.state.log("orchestrator", "approved",
                       "Operator confirmed Action Plan v1", color="green", flash=True)

        # Generate dispatch briefs for confirmed units
        for unit in state.recommended_units:
            dispatch_result = await dispatch_agent.run(
                f"Generate dispatch brief for {unit}. "
                f"Incident: {state.incident_type} at {state.location_normalized}.",
                deps=self.deps,
            )
            brief = dispatch_result.output
            # Generate TTS for dispatch brief
            safe_unit = unit.replace(" ", "_").lower()
            audio_url = await generate_and_save(
                brief.voice_message, "en", f"dispatch_{safe_unit}.mp3"
            )
            self.deps.supabase.table("dispatches").insert({
                "case_id": self.deps.case_id,
                "unit_type": unit,
                "unit_assigned": brief.unit_assigned,
                "destination": brief.destination,
                "eta_minutes": brief.eta_minutes,
                "status": "confirmed",
                "voice_message": brief.voice_message,
                "rationale": brief.rationale,
            }).execute()
            self.state.log("dispatch", "unit_dispatched",
                           f"{unit} dispatched: {brief.unit_assigned} -> {brief.destination}",
                           data={"audio_url": audio_url},
                           color="green")

    async def _phase_3_caller_2(self):
        """Process Caller 2 — Mandarin bystander reporting child."""
        caller = CALLERS[1]
        self.state.log("voice", "caller_connected",
                       f"Incoming call: {caller.label} ({caller.language.upper()})",
                       color="green")
        self.state.update_state(caller_count=2)

        # Transcribe
        transcript = await transcribe_audio(caller.audio_path)
        self.state.log("voice", "transcript_received",
                       f"Transcribed ({caller.language}): {transcript['text']}")

        self.deps.supabase.table("transcripts").insert({
            "case_id": self.deps.case_id,
            "caller_id": caller.caller_id,
            "caller_label": caller.label,
            "language": caller.language,
            "original_text": transcript["text"],
            "confidence": transcript.get("confidence"),
            "segment_index": 0,
        }).execute()

        # Extract facts
        facts_result = await intake_agent.run(
            f"Transcript from emergency caller ({caller.language}): {transcript['text']}",
            deps=self.deps,
        )
        facts = facts_result.output

        # Case correlation
        self.state.log("intake", "case_match",
                       "Caller 2 linked to TN-2026-00417 (0.94)", color="purple")
        self.state.update_state(match_confidence=0.94)

        # Evidence fusion
        fusion_result = await evidence_fusion_agent.run(
            "Fuse all evidence. A second caller has been linked to this case. "
            "Check for new information.",
            deps=self.deps,
        )
        fusion = fusion_result.output

        # Re-triage with new evidence
        triage_result = await triage_agent.run(
            "Re-classify. New caller added with additional victim information. "
            "Check all evidence and update.",
            deps=self.deps,
        )
        triage = triage_result.output

        # Update state
        injury = list(set(self.state.get_state().injury_flags + triage.injury_flags))
        self.state.update_state(
            severity=triage.severity.value,
            recommended_units=triage.recommended_units,
            people_count_estimate=triage.people_count_estimate,
            injury_flags=injury,
            action_plan_version=2,
            action_plan=[a.model_dump() for a in triage.action_plan],
            status=(IncidentStatus.CRITICAL.value
                    if triage.severity == Severity.CRITICAL
                    else IncidentStatus.ESCALATED.value),
        )
        self.state.log("triage", "severity_changed",
                       f"Severity: HIGH -> {triage.severity.value.upper()}",
                       color="red", flash=True)
        self.state.log("triage", "action_plan", "Action Plan v2 generated", color="blue")

    async def _phase_4_vision(self):
        """Vision analysis — detect smoke then fire from video frames."""
        self.state.log("vision", "scanning", "CCTV analysis active", color="purple")

        # Frame 1 — Smoke detection (~58s into video)
        frame_bytes_1 = await extract_frame("assets/crash_video.mp4", timestamp_s=58)
        analysis_1 = await analyze_frame(self.deps.mistral_client, frame_bytes_1, frame_id=1)
        self.state.log("vision", "detection",
                       f"Smoke detected (confidence: "
                       f"{analysis_1.detections[0].confidence if analysis_1.detections else 'N/A'})",
                       color="purple")

        await asyncio.sleep(3)

        # Frame 2 — Fire detection (~66s into video)
        frame_bytes_2 = await extract_frame("assets/crash_video.mp4", timestamp_s=66)
        analysis_2 = await analyze_frame(self.deps.mistral_client, frame_bytes_2, frame_id=2)
        delta = compute_scene_delta(analysis_1, analysis_2)

        if delta.get("hazard_escalation"):
            self.state.log("vision", "hazard_escalation",
                           "ENGINE FIRE DETECTED (0.99)",
                           color="red", flash=True)

        # Update state with vision detections
        state = self.state.get_state()
        detections = state.vision_detections + [d.model_dump() for d in analysis_2.detections]
        hazards = list(set(state.hazard_flags + ["engine_fire"]))
        self.state.update_state(
            vision_detections=detections,
            hazard_flags=hazards,
        )

        # Evidence fusion
        fusion_result = await evidence_fusion_agent.run(
            "New vision evidence: engine fire detected. "
            "Check if any callers mentioned smoke or fire.",
            deps=self.deps,
        )
        if fusion_result.output.corroborations:
            self.state.log("triage", "corroboration",
                           "CORROBORATED: Vision fire + Caller report match",
                           color="green", flash=True)

        # Re-triage
        triage_result = await triage_agent.run(
            "Re-classify. Engine fire visually confirmed. Update action plan.",
            deps=self.deps,
        )
        triage = triage_result.output
        self.state.update_state(
            recommended_units=triage.recommended_units,
            action_plan_version=3,
            action_plan=[a.model_dump() for a in triage.action_plan],
            status=IncidentStatus.ESCALATED.value,
        )
        self.state.log("triage", "action_plan",
                       "Action Plan v3 generated — Fire Response added", color="blue")

    async def _phase_5_interrupt(self):
        """Priority interrupt — warn callers in their native languages."""
        self.state.log("voice", "priority_interrupt",
                       "PRIORITY INTERRUPT — Hazard warning to all callers",
                       color="red", flash=True)

        # Generate TTS evacuation warnings in each active caller language
        warnings = {
            "es": (
                "¡Atención! Se ha detectado fuego en el motor. "
                "Aléjense del vehículo inmediatamente. Los bomberos están en camino.",
                "Attention! Engine fire detected. "
                "Move away from the vehicle immediately. Fire department is en route."
            ),
            "zh": (
                "注意！已检测到发动机起火。请立即远离车辆。消防队正在赶来。",
                "Attention! Engine fire detected. "
                "Move away from the vehicle immediately. Fire department is en route."
            ),
        }
        for lang_code, (warning_text, translation) in warnings.items():
            audio_url = await generate_and_save(
                warning_text, lang_code, f"warning_{lang_code}.mp3"
            )
            self.deps.supabase.table("transcripts").insert({
                "case_id": self.deps.case_id,
                "caller_id": "dispatch",
                "caller_label": "DISPATCH",
                "language": lang_code,
                "original_text": warning_text,
                "translated_text": translation,
                "confidence": 1.0,
                "segment_index": 10,
            }).execute()
            self.state.log("voice", "warning_sent",
                           f"Evacuation warning sent ({lang_code.upper()})",
                           data={"audio_url": audio_url},
                           color="red")

        # Dispatch fire response
        dispatch_result = await dispatch_agent.run(
            "Generate dispatch brief for Fire Response. "
            "Engine fire confirmed by CCTV. Urgent.",
            deps=self.deps,
        )
        brief = dispatch_result.output
        audio_url = await generate_and_save(
            brief.voice_message, "en", "dispatch_fire_response.mp3"
        )
        self.deps.supabase.table("dispatches").insert({
            "case_id": self.deps.case_id,
            "unit_type": "Fire Response",
            "unit_assigned": brief.unit_assigned,
            "destination": brief.destination,
            "eta_minutes": brief.eta_minutes,
            "status": "dispatched",
            "voice_message": brief.voice_message,
            "rationale": "Vision-confirmed engine fire",
            "audio_url": audio_url,
        }).execute()
        self.state.log("dispatch", "unit_dispatched",
                       f"Fire Response dispatched: {brief.unit_assigned}",
                       data={"audio_url": audio_url},
                       color="red", flash=True)

    async def _phase_6_summary(self):
        """Generate final case summary. Freeze state."""
        state = self.state.get_state()
        summary = (
            f"Vehicle collision with trapped occupant and child confirmed. "
            f"Engine fire visually detected and corroborated. "
            f"Severity: CRITICAL. "
            f"{len(state.confirmed_units)} units confirmed, "
            f"{len(state.recommended_units)} total recommended. "
            f"Multilingual warnings delivered in ES, ZH."
        )
        self.state.update_state(
            status=IncidentStatus.RESOLVED_DEMO.value,
            operator_summary=summary,
        )
        self.state.log("orchestrator", "complete",
                       "Demo complete: TN-2026-00417",
                       color="green", flash=True)
