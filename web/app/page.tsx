"use client";

import { KeyboardEvent, useMemo, useState } from "react";
import { AudienceKey, Scenario, ScenarioKey, ViewKey, scenarios, views } from "./data";

const audienceLabels: Record<AudienceKey, string> = {
  employee: "Employee",
  manager: "Manager",
  executive: "Executive",
  it: "IT + security",
};

function Mark() {
  return <svg viewBox="0 0 42 42" aria-hidden="true"><path d="M7 9h12v9H7zM23 24h12v9H23z"/><path d="M19 13h9c4 0 7 3 7 7v4M23 29h-9c-4 0-7-3-7-7v-4" fill="none" stroke="currentColor" strokeWidth="3"/></svg>;
}

function Arrow() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h13M13 6l6 6-6 6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>;
}

function ListenView({ scenario }: { scenario: Scenario }) {
  const fields = [
    ["What starts the work?", scenario.before[0].title],
    ["Who does it today?", scenario.before[0].actor],
    ["Which team owns it?", scenario.department],
    ["What makes it difficult?", scenario.before.find((step) => step.friction)?.friction ?? "Exceptions require judgment"],
  ];
  return <section className="listen-grid" aria-labelledby="view-title">
    <div className="interview-sheet">
      <div className="sheet-heading"><b>Interview complete · 8 of 8 questions captured</b></div>
      <h2 id="view-title">Start with the person doing the work.</h2>
      <p className="lede">Describe the process as it really happens, including the parts people work around.</p>
      <div className="field-stack">{fields.map(([label, value]) => <label key={label}><span>{label}</span><input value={value} readOnly /></label>)}</div>
      <label className="long-field"><span>In their own words</span><textarea value={scenario.description} readOnly /></label>
    </div>
    <aside className="observer-notes"><h3>Facilitator note: do not fix the process during discovery.</h3><ul><li>Capture the unofficial steps.</li><li>Ask what happens on a bad day.</li><li>Separate inconvenience from real risk.</li><li>Let unknowns stay unknown.</li></ul><div className="tape">Captured from synthetic workshop fixture</div></aside>
  </section>;
}

function MapView({ scenario }: { scenario: Scenario }) {
  return <section className="map-view" aria-labelledby="view-title">
    <div className="map-intro"><div><h2 id="view-title">See the work before changing it.</h2></div><p>{scenario.description}</p></div>
    <div className="process-lane before-lane" aria-label="Current workflow">
      <div className="lane-label"><span>Today</span><b>{scenario.before.reduce((sum, step) => sum + step.minutes, 0)} minutes</b></div>
      <ol>{scenario.before.map((step, index) => <li key={step.title}><span className="step-index">{index + 1}</span><div><b>{step.title}</b><small>{step.actor} · {step.minutes} min</small>{step.friction && <em>{step.friction}</em>}</div>{index < scenario.before.length - 1 && <Arrow />}</li>)}</ol>
    </div>
    <div className="bridge-line"><span>TaskBridge recommendation</span><strong>{scenario.recommendationLabel}</strong></div>
    <div className="process-lane after-lane" aria-label="Proposed pilot workflow">
      <div className="lane-label"><span>Pilot</span><b>Human checkpoints visible</b></div>
      <ol>{scenario.after.map((step, index) => <li key={step.title} data-mode={step.mode}><span className="step-index">{index + 1}</span><div><b>{step.title}</b><small>{step.actor}</small><em>{step.note}</em></div>{index < scenario.after.length - 1 && <Arrow />}</li>)}</ol>
    </div>
    <div className="map-legend"><span data-mode="rule">Rule</span><span data-mode="ai">AI suggestion</span><span data-mode="human">Human decision</span></div>
  </section>;
}

function DecideView({ scenario }: { scenario: Scenario }) {
  return <section className="decide-view" aria-labelledby="view-title">
    <div className="decision-stamp"><h3>Recommended approach</h3><strong>{scenario.recommendation}</strong><p>{scenario.recommendationLabel}</p></div>
    <div className="decision-copy"><h2 id="view-title">AI is one option, not the starting point.</h2><p>{scenario.reason}</p><div className="score-list">{scenario.scores.map((score) => <div key={score.label} data-selected={score.label.toUpperCase().startsWith(scenario.recommendation.split(" ")[0])}><span>{score.label}</span><div className="score-track"><i style={{ width: `${score.value}%` }}/></div><b>{score.value}</b><small>{score.note}</small></div>)}</div></div>
    <aside className="evidence-rail"><div className="rail-title"><h3>Evidence used</h3><b>{scenario.evidence.length} sources</b></div>{scenario.evidence.map((item) => <div className="evidence-row" key={item.id}><small>{item.id}</small><span>{item.label}</span><strong>{item.value}</strong></div>)}<div className="rail-foot">No salary, savings, or company outcome is inferred from these synthetic inputs.</div></aside>
  </section>;
}

function ExplainView({ scenario, audience, onAudience }: { scenario: Scenario; audience: AudienceKey; onAudience: (value: AudienceKey) => void }) {
  const explanation = scenario.explanations[audience];
  const audiences = Object.keys(audienceLabels) as AudienceKey[];
  const moveAudience = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const nextIndex = event.key === "Home" ? 0 : event.key === "End" ? audiences.length - 1 : (index + (event.key === "ArrowRight" ? 1 : -1) + audiences.length) % audiences.length;
    onAudience(audiences[nextIndex]);
    document.getElementById(`audience-tab-${audiences[nextIndex]}`)?.focus();
  };
  return <section className="explain-view" aria-labelledby="view-title">
    <div className="audience-tabs" role="tablist" aria-label="Explanation audience">{audiences.map((key, index) => <button id={`audience-tab-${key}`} role="tab" aria-controls="audience-panel" aria-selected={audience === key} tabIndex={audience === key ? 0 : -1} key={key} onKeyDown={(event) => moveAudience(event, index)} onClick={() => onAudience(key)}>{audienceLabels[key]}</button>)}</div>
    <div id="audience-panel" className="teachback-sheet" role="tabpanel" tabIndex={0} aria-labelledby={`audience-tab-${audience}`}><h2 id="view-title">{explanation.title}</h2><p className="audience-meta">For {audienceLabels[audience]}</p><p>{explanation.body}</p><div className="unchanged"><small>What does not change</small><strong>{explanation.keeps}</strong></div></div>
    <aside className="same-facts"><h3>Same facts, different language</h3><div>{scenario.evidence.map((item) => <p key={item.id}><small>{item.id}</small><b>{item.value}</b></p>)}</div><p className="plain-note">Every audience sees the same evidence. Only the explanation changes.</p></aside>
  </section>;
}

function SimulateView({ scenario, runStatus, onRun }: { scenario: Scenario; runStatus: "idle" | "running" | "complete"; onRun: () => void }) {
  const running = runStatus === "running";
  return <section className="simulate-view" aria-labelledby="view-title" aria-busy={running}>
    <div className="sim-head"><div><h2 id="view-title">Run the common path. Surface the exceptions.</h2></div><button className="run-button" onClick={onRun} disabled={running}>{running ? "Running synthetic records…" : runStatus === "complete" ? "Run again" : "Run synthetic pilot"}<Arrow /></button></div>
    <p className="sr-only" aria-live="polite">{running ? "Synthetic pilot is running." : runStatus === "complete" ? "Synthetic pilot completed. Results are ready." : "Synthetic pilot is ready."}</p>
    <div className="record-table" role="table" aria-label="Synthetic pilot decisions"><div role="row" className="table-head"><span role="columnheader">Record</span><span role="columnheader">Source</span><span role="columnheader">Decision</span><span role="columnheader">Reason</span></div>{scenario.records.map((record, index) => <div role="row" className={running && index > 0 ? "waiting" : ""} key={record.id}><b role="cell">{record.id}</b><span role="cell">{record.source}</span><strong role="cell" data-state={record.state}>{running && index > 0 ? "Waiting" : record.decision}</strong><span role="cell">{running && index > 0 ? "Queued behind current record" : record.why}</span></div>)}</div>
    <div className="authority-strip"><span>EXTERNAL ACTIONS</span><strong>DISABLED</strong><p>This demonstration prepares decisions but cannot send email, update a ticket, approve payment, or change a source system.</p></div>
  </section>;
}

function MeasureView({ scenario }: { scenario: Scenario }) {
  const reduction = Math.round((1 - scenario.measures.pilot / scenario.measures.baseline) * 100);
  return <section className="measure-view" aria-labelledby="view-title">
    <div className="measure-copy"><h2 id="view-title">Measure the workflow, not just the model.</h2><p>These figures describe the committed fixture run. They are demonstration data, not a forecast or a customer result.</p><div className="measure-bars"><div><span>Baseline touch time</span><i style={{ width: "100%" }}/><b>{scenario.measures.baseline} min</b></div><div><span>Synthetic pilot</span><i style={{ width: `${100 - reduction}%` }}/><b>{scenario.measures.pilot} min</b></div></div></div>
    <div className="result-ledger"><div><span>Fixture reduction</span><strong>{reduction}%</strong><small>Calculated from this run only</small></div><div><span>Human reviews</span><strong>{scenario.measures.reviewed}</strong><small>Exceptions kept visible</small></div><div><span>Unsupported claims</span><strong>{scenario.measures.unsupported}</strong><small>Required to remain zero</small></div></div>
    <aside className="continue-rule"><h3>Expansion rule: continue only when people trust the process and observed results improve.</h3><ul><li>Review override reasons</li><li>Compare real baseline data</li><li>Ask employees what became harder</li><li>Stop if error cost increases</li></ul></aside>
  </section>;
}

function HandoffView({ scenario }: { scenario: Scenario }) {
  const docs = [
    ["Pilot charter", "Purpose, owner, boundary, and stop conditions"],
    ["Updated SOP", "Common path, exceptions, and decision authority"],
    ["Measurement plan", "Baseline, adoption, overrides, and error cost"],
    ["Risk register", "Data, process, model, and operating risks"],
    ["Rollback checklist", "How to stop safely and preserve evidence"],
    ["Training guide", "What the system does and what people still decide"],
  ];
  return <section className="handoff-view" aria-labelledby="view-title"><div className="handoff-title"><h2 id="view-title">Leave the team with something they can run.</h2><p>{scenario.name} · v0.1 synthetic workshop package</p></div><div className="document-stack">{docs.map(([name, description], index) => <article key={name} style={{ transform: `translate(${index % 2 ? 8 : 0}px, ${index * -2}px)` }}><span>{String(index + 1).padStart(2, "0")}</span><div><h3>{name}</h3><p>{description}</p></div><b>READY</b></article>)}</div><aside className="handoff-note"><h3>Owner check</h3><p>Names, thresholds, integrations, retention, and live outcome measures must be confirmed before this package leaves a workshop.</p><button onClick={() => window.print()}>Print workshop summary</button></aside></section>;
}

export default function Page() {
  const [scenarioKey, setScenarioKey] = useState<ScenarioKey>("inbox");
  const [view, setView] = useState<ViewKey>("map");
  const [audience, setAudience] = useState<AudienceKey>("employee");
  const [runStatus, setRunStatus] = useState<"idle" | "running" | "complete">("idle");
  const scenario = scenarios[scenarioKey];
  const activeIndex = useMemo(() => views.findIndex((item) => item.key === view), [view]);
  const runPilot = () => { setRunStatus("running"); window.setTimeout(() => setRunStatus("complete"), 1200); };

  return <main>
    <a className="skip-link" href="#workshop">Skip to workshop</a>
    <header className="app-header"><a className="brand" href="#workshop" aria-label="TaskBridge AI home"><Mark /><span><h1>TaskBridge</h1><small>AI workflow workshop</small></span></a><div className="synthetic-banner"><span>SYNTHETIC DEMONSTRATION</span><small>No external actions or customer data</small></div><a className="repo-link" href="https://github.com/Jermaine-Anugwom/taskbridge-ai">View source<Arrow /></a></header>
    <div className="scenario-files" aria-label="Synthetic scenarios">{(Object.keys(scenarios) as ScenarioKey[]).map((key) => <button key={key} aria-pressed={scenarioKey === key} onClick={() => { setScenarioKey(key); setView("map"); }}><small>{scenarios[key].department}</small><strong>{scenarios[key].name}</strong></button>)}</div>
    <div className="workshop-shell">
      <nav className="stage-rail" aria-label="Workflow improvement stages">{views.map((item, index) => <button key={item.key} aria-current={view === item.key ? "step" : undefined} onClick={() => setView(item.key)}><span>{index + 1}</span><div><b>{item.verb}</b><small>{item.label}</small></div></button>)}</nav>
      <div className="workbench" id="workshop" data-view={view}>
        <div className="bench-topline"><span>WORKSHOP / {scenario.name.toUpperCase()}</span><div><b>{String(activeIndex + 1).padStart(2, "0")}</b><small>of 07</small></div></div>
        {view === "listen" && <ListenView scenario={scenario} />}
        {view === "map" && <MapView scenario={scenario} />}
        {view === "decide" && <DecideView scenario={scenario} />}
        {view === "explain" && <ExplainView scenario={scenario} audience={audience} onAudience={setAudience} />}
        {view === "simulate" && <SimulateView scenario={scenario} runStatus={runStatus} onRun={runPilot} />}
        {view === "measure" && <MeasureView scenario={scenario} />}
        {view === "handoff" && <HandoffView scenario={scenario} />}
        <div className="bench-nav"><button disabled={activeIndex === 0} onClick={() => setView(views[activeIndex - 1].key)}>Previous</button><p><strong>{views[activeIndex].verb}</strong> <span>→</span> {activeIndex < views.length - 1 ? views[activeIndex + 1].verb : "Complete"}</p><button disabled={activeIndex === views.length - 1} onClick={() => setView(views[activeIndex + 1].key)}>Next stage</button></div>
      </div>
    </div>
    <footer className="app-footer"><span>TaskBridge AI v0.1.0</span><span>Deterministic offline mode</span><span>All records and outcomes are synthetic</span></footer>
    <script type="application/json" data-impeccable-contract dangerouslySetInnerHTML={{ __html: JSON.stringify({ seed: "3bc2dcef", thesis: "Make the automation decision on the workshop table, not inside a black box.", world: "Bright operations workshop with movable process tiles, cobalt binder tabs, lime review marks, and cool paper surfaces.", story: "Listen, map, decide, explain, simulate, measure, and hand off one inspectable workflow.", first_viewport: "Scenario folders above a two-part workbench; a full-width before-and-after process map carries the initial view; stage rail remains visible.", form: "Grounded direction 4, operations workshop table.", finish: "unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance" }) }} />
  </main>;
}
