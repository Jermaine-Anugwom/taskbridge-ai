export type ScenarioKey = "inbox" | "status" | "invoice";
export type ViewKey = "listen" | "map" | "decide" | "explain" | "simulate" | "measure" | "handoff";
export type AudienceKey = "employee" | "manager" | "executive" | "it";

export type Scenario = {
  name: string;
  department: string;
  description: string;
  recommendation: "HYBRID" | "AI ASSIST" | "RULES";
  recommendationLabel: string;
  reason: string;
  evidence: Array<{ label: string; value: string; id: string }>;
  before: Array<{ title: string; actor: string; minutes: number; friction?: string }>;
  after: Array<{ title: string; actor: string; mode: "rule" | "ai" | "human"; note: string }>;
  scores: Array<{ label: string; value: number; note: string }>;
  measures: { baseline: number; pilot: number; reviewed: number; unsupported: number };
  explanations: Record<AudienceKey, { title: string; body: string; keeps: string }>;
  records: Array<{ id: string; source: string; decision: string; state: "auto" | "review" | "blocked"; why: string }>;
};

export const scenarios: Record<ScenarioKey, Scenario> = {
  inbox: {
    name: "Shared inbox triage",
    department: "Customer operations",
    description: "A coordinator reads every incoming request, finds the account, decides the topic, and copies the message into a service queue.",
    recommendation: "HYBRID",
    recommendationLabel: "Rules first. AI organizes the message. People own exceptions.",
    reason: "The account checks are stable, but the requests arrive in unpredictable language and incomplete messages can affect customers.",
    evidence: [
      { label: "Weekly volume", value: "180 requests", id: "EV-VOLUME" },
      { label: "Touch time", value: "8 min / request", id: "EV-EFFORT" },
      { label: "Unstructured input", value: "70%", id: "EV-STRUCTURE" },
      { label: "Error consequence", value: "Medium", id: "EV-RISK" },
    ],
    before: [
      { title: "Read request", actor: "Coordinator", minutes: 3 },
      { title: "Find account", actor: "Coordinator", minutes: 2, friction: "Missing in 14%" },
      { title: "Choose queue", actor: "Coordinator", minutes: 2 },
      { title: "Copy details", actor: "Coordinator", minutes: 1 },
    ],
    after: [
      { title: "Verify account", actor: "Rule", mode: "rule", note: "Exact match only" },
      { title: "Organize request", actor: "AI", mode: "ai", note: "Suggestion with evidence" },
      { title: "Review exceptions", actor: "Coordinator", mode: "human", note: "Authority stays here" },
      { title: "Prepare ticket", actor: "Rule", mode: "rule", note: "External write disabled" },
    ],
    scores: [
      { label: "Rules only", value: 64, note: "Language varies too much" },
      { label: "AI only", value: 58, note: "Too much decision authority" },
      { label: "Hybrid", value: 91, note: "Best control and usefulness" },
      { label: "No change", value: 29, note: "Volume justifies a pilot" },
    ],
    measures: { baseline: 96, pilot: 43, reviewed: 3, unsupported: 0 },
    explanations: {
      employee: { title: "You stop doing the same sorting twice.", body: "The pilot checks known fields and organizes each message before you see it. You still decide where uncertain requests go and you can see why the suggestion was made.", keeps: "You keep control of customer-impacting decisions." },
      manager: { title: "The common path becomes consistent.", body: "Known requests follow the same rules. Missing accounts, unusual language, and low-confidence cases go to a named review queue instead of disappearing inside the automation.", keeps: "You keep ownership of policy and exception thresholds." },
      executive: { title: "This is one bounded workflow, not an AI rollout.", body: "The pilot tests whether the team spends less time sorting requests without increasing routing errors. Expansion depends on observed use, overrides, and operating results.", keeps: "The business decides whether measured value justifies expansion." },
      it: { title: "The data path and authority are explicit.", body: "Inputs are treated as untrusted. Account validation is deterministic, model output is advisory, external writes are disabled, and every result carries source evidence.", keeps: "IT and security approve data boundaries before any live integration." },
    },
    records: [
      { id: "SYN-1042", source: "Email", decision: "Priority service", state: "auto", why: "Known account and outage language" },
      { id: "SYN-1043", source: "Email", decision: "Human review", state: "review", why: "Account identifier is missing" },
      { id: "SYN-1044", source: "Email", decision: "Standard service", state: "auto", why: "Known account and service topic" },
      { id: "SYN-1045", source: "Email", decision: "Blocked", state: "blocked", why: "Instruction directed at the processor" },
    ],
  },
  status: {
    name: "Weekly status report",
    department: "Program delivery",
    description: "A program lead collects updates from several spreadsheets, rewrites them into one format, and chases missing owners before Friday review.",
    recommendation: "AI ASSIST",
    recommendationLabel: "AI drafts the summary. Owners verify their facts.",
    reason: "The work is language-heavy, reversible, and low consequence when every statement retains an owner and source row.",
    evidence: [
      { label: "Weekly inputs", value: "42 updates", id: "EV-VOLUME" },
      { label: "Preparation", value: "5.5 hours", id: "EV-EFFORT" },
      { label: "Unstructured input", value: "85%", id: "EV-STRUCTURE" },
      { label: "Error consequence", value: "Low", id: "EV-RISK" },
    ],
    before: [
      { title: "Collect updates", actor: "Program lead", minutes: 75 },
      { title: "Rewrite formats", actor: "Program lead", minutes: 120, friction: "Seven source formats" },
      { title: "Chase owners", actor: "Program lead", minutes: 80 },
      { title: "Build report", actor: "Program lead", minutes: 55 },
    ],
    after: [
      { title: "Validate fields", actor: "Rule", mode: "rule", note: "Owner required" },
      { title: "Draft summary", actor: "AI", mode: "ai", note: "Source row attached" },
      { title: "Confirm facts", actor: "Update owner", mode: "human", note: "One-click accept or revise" },
      { title: "Assemble report", actor: "Rule", mode: "rule", note: "Approved text only" },
    ],
    scores: [
      { label: "Rules only", value: 48, note: "Cannot rewrite varied updates" },
      { label: "AI assist", value: 89, note: "Strong language task" },
      { label: "Hybrid", value: 84, note: "Also viable" },
      { label: "No change", value: 24, note: "Repeated weekly burden" },
    ],
    measures: { baseline: 330, pilot: 146, reviewed: 4, unsupported: 0 },
    explanations: {
      employee: { title: "You review a draft instead of rebuilding it.", body: "Your update stays connected to your source row. The system drafts a consistent summary, but it does not publish your information until you accept or revise it.", keeps: "You remain the owner of your facts." },
      manager: { title: "Missing ownership becomes visible earlier.", body: "Updates without an owner, status, or next action stop before the report is assembled. The team spends review time on risks rather than formatting.", keeps: "You keep the final editorial decision." },
      executive: { title: "The pilot tests reporting speed and trust together.", body: "Success requires less preparation time with no unsupported statements. A shorter report is not counted as progress if owners do not trust it.", keeps: "Leadership sets the reporting standard and expansion decision." },
      it: { title: "The model never becomes a source of record.", body: "Every drafted statement points back to a source row and owner. Missing or contradictory data is held, and the offline deterministic mode remains available.", keeps: "IT controls the approved model and retention policy." },
    },
    records: [
      { id: "SYN-2201", source: "Spreadsheet", decision: "Include", state: "auto", why: "Owner, status, and next action present" },
      { id: "SYN-2202", source: "Spreadsheet", decision: "Owner review", state: "review", why: "Next action is unclear" },
      { id: "SYN-2203", source: "Spreadsheet", decision: "Include", state: "auto", why: "At-risk status has source evidence" },
      { id: "SYN-2204", source: "Spreadsheet", decision: "Blocked", state: "blocked", why: "Embedded instruction attempted to change policy" },
    ],
  },
  invoice: {
    name: "Invoice exceptions",
    department: "Accounts payable",
    description: "An analyst compares invoice totals, purchase orders, and duplicate records before deciding which items need manual review.",
    recommendation: "RULES",
    recommendationLabel: "Use deterministic checks. Do not add AI to the decision.",
    reason: "The fields and tolerances are stable, the decision must be repeatable, and language generation would add risk without improving the result.",
    evidence: [
      { label: "Weekly volume", value: "310 invoices", id: "EV-VOLUME" },
      { label: "Touch time", value: "6 min / invoice", id: "EV-EFFORT" },
      { label: "Structured input", value: "96%", id: "EV-STRUCTURE" },
      { label: "Error consequence", value: "High", id: "EV-RISK" },
    ],
    before: [
      { title: "Open invoice", actor: "AP analyst", minutes: 1 },
      { title: "Find purchase order", actor: "AP analyst", minutes: 2 },
      { title: "Compare totals", actor: "AP analyst", minutes: 2, friction: "Same arithmetic each time" },
      { title: "Check duplicates", actor: "AP analyst", minutes: 1 },
    ],
    after: [
      { title: "Match identifiers", actor: "Rule", mode: "rule", note: "Exact source fields" },
      { title: "Compare tolerance", actor: "Rule", mode: "rule", note: "$25 fixture threshold" },
      { title: "Review holds", actor: "AP analyst", mode: "human", note: "Payment authority stays here" },
      { title: "Record decision", actor: "Rule", mode: "rule", note: "Evidence retained" },
    ],
    scores: [
      { label: "Rules only", value: 96, note: "Stable and inspectable" },
      { label: "AI assist", value: 31, note: "Adds unnecessary uncertainty" },
      { label: "Hybrid", value: 62, note: "Useful only for future notes" },
      { label: "No change", value: 38, note: "Volume supports automation" },
    ],
    measures: { baseline: 72, pilot: 28, reviewed: 3, unsupported: 0 },
    explanations: {
      employee: { title: "The computer handles the comparison, not the judgment.", body: "Exact matching and tolerance checks happen automatically. You investigate every hold and remain the only person who can approve an exception.", keeps: "You keep payment and exception authority." },
      manager: { title: "The same rule is applied every time.", body: "The pilot removes repeated arithmetic and exposes each hold reason. Thresholds are versioned and cannot be changed by invoice text.", keeps: "You approve the policy and review control performance." },
      executive: { title: "The right answer here is less AI.", body: "A deterministic workflow is cheaper to inspect and easier to control. The pilot measures processing time and exception accuracy without introducing model uncertainty.", keeps: "Finance owns every threshold and expansion decision." },
      it: { title: "No model is needed in the payment path.", body: "Typed fields, versioned tolerances, duplicate checks, and immutable evidence are enough. Untrusted invoice text cannot modify the rules.", keeps: "IT controls access, audit retention, and integrations." },
    },
    records: [
      { id: "SYN-3301", source: "AP queue", decision: "Clear", state: "auto", why: "PO match and zero variance" },
      { id: "SYN-3302", source: "AP queue", decision: "Hold", state: "review", why: "Amount variance exceeds fixture threshold" },
      { id: "SYN-3303", source: "AP queue", decision: "Hold", state: "review", why: "Possible duplicate invoice" },
      { id: "SYN-3304", source: "AP queue", decision: "Blocked", state: "blocked", why: "Invoice note attempted to override the rule" },
    ],
  },
};

export const views: Array<{ key: ViewKey; label: string; verb: string }> = [
  { key: "listen", label: "Interview", verb: "Listen" },
  { key: "map", label: "Workflow map", verb: "Map" },
  { key: "decide", label: "Decision", verb: "Decide" },
  { key: "explain", label: "Teach it back", verb: "Explain" },
  { key: "simulate", label: "Pilot studio", verb: "Simulate" },
  { key: "measure", label: "Results", verb: "Measure" },
  { key: "handoff", label: "Handoff", verb: "Hand off" },
];
