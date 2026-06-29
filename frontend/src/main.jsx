import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const navItems = [
  { id: "mission", label: "MISSION CONTROL", icon: "grid" },
  { id: "dataset", label: "DATASET ALPHA", icon: "table" },
  { id: "light", label: "LIGHT CURVES", icon: "wave" },
  { id: "ai", label: "AI PREDICTOR", icon: "spark" },
  { id: "metrics", label: "MODEL METRICS", icon: "trend" },
  { id: "settings", label: "PARAMETERS", icon: "sliders" },
];

function Icon({ type }) {
  return (
    <span className={`icon icon-${type}`} aria-hidden="true">
      <span />
    </span>
  );
}

function App() {
  const [activePage, setActivePage] = useState("mission");
  const pageTitle = useMemo(() => {
    const selected = navItems.find((item) => item.id === activePage);
    return selected?.label.replace("MISSION CONTROL", "DASHBOARD") ?? "DASHBOARD";
  }, [activePage]);

  return (
    <div className="app-shell">
      <TopBar pageTitle={pageTitle} />
      <SideBar activePage={activePage} onSelectPage={setActivePage} />
      <main className={`main-content page-${activePage}`}>
        {activePage === "mission" && <MissionControl />}
        {activePage === "dataset" && <DatasetBrowser />}
        {activePage === "light" && <LightCurveViewer />}
        {activePage === "ai" && <AiPredictor />}
        {activePage === "metrics" && <ModelMetrics />}
        {activePage === "settings" && <SettingsPage />}
      </main>
    </div>
  );
}

function TopBar({ pageTitle }) {
  return (
    <header className="topbar">
      <div className="brand-row">
        <strong>TRANSIT_HUNTER_v1.0</strong>
        <span className="divider" />
        <span className="status-dot" />
        <span className="mono active">MISSION ACTIVE</span>
      </div>
      <nav className="top-links" aria-label="Top navigation">
        <span className="top-link active">{pageTitle}</span>
        <span className="top-link">ANALYTICS</span>
        <span className="top-link">ARCHIVE</span>
        <span className="top-icon">⌁</span>
        <span className="top-icon">▣</span>
        <span className="user-pill">
          <span className="user-dot" />
          CMD_USER_01
        </span>
      </nav>
    </header>
  );
}

function SideBar({ activePage, onSelectPage }) {
  return (
    <aside className="sidebar">
      <div className="side-head">
        <h1>MISSION_CTRL</h1>
        <p>UTC 14:42:01</p>
      </div>
      <nav className="side-nav" aria-label="Primary navigation">
        {navItems.map((item) => (
          <button
            className={`side-link ${activePage === item.id ? "active" : ""}`}
            key={item.id}
            onClick={() => onSelectPage(item.id)}
            type="button"
          >
            <Icon type={item.icon} />
            {item.label}
          </button>
        ))}
      </nav>
      <div className="side-footer">
        <button className="side-link small" type="button">
          <Icon type="help" />
          HELP
        </button>
        <button className="side-link small" type="button">
          <Icon type="logs" />
          LOGS
        </button>
      </div>
    </aside>
  );
}

function Panel({ children, className = "" }) {
  return <section className={`panel ${className}`}>{children}</section>;
}

function SectionTitle({ children, meta }) {
  return (
    <div className="section-title">
      <span className="tiny-star" />
      <span>{children}</span>
      {meta && <small>{meta}</small>}
    </div>
  );
}

function MissionControl() {
  const metricCards = [
    ["STARS SCANNED", "1,248,392", "grid"],
    ["DETECTIONS", "4,812", "spark"],
    ["AI CONFIDENCE", "98.4%", "brain"],
    ["FALSE POSITIVES", "124", "warning"],
  ];
  const feed = [
    ["92% MATCH", "TH-921-A", "TRANSIT DEPTH: 0.04%", "14.2 LY DISTANCE", "FULL REPORT"],
    ["ANOMALY", "TH-921-B", "TRANSIT DEPTH: 0.12%", "208.5 LY DISTANCE", "FULL REPORT"],
    ["HABITABLE?", "TH-102-F", "TRANSIT DEPTH: 0.01%", "42.8 LY DISTANCE", "FULL REPORT"],
    ["SCANNING...", "TH-X-NULL", "TRANSIT DEPTH: --%", "PENDING CALIB", "PROCESSING"],
  ];

  return (
    <>
      <div className="hero-grid">
        <Panel className="mission-hero">
          <div>
            <p className="eyebrow">OBSERVATION SECTOR</p>
            <h2>
              Kepler-186 Star System <span>Targeted</span>
            </h2>
          </div>
          <div className="hero-bottom">
            <div className="coord-row">
              <DataPoint label="RA COORDINATE" value="19h 54m 31s" />
              <DataPoint label="DEC COORDINATE" value="+43° 57′ 18″" />
            </div>
            <button className="outline-button" type="button">RE-TARGET ARRAY</button>
          </div>
        </Panel>
        <Panel className="scan-card">
          <div className="radial">
            <span>75%</span>
          </div>
          <p className="eyebrow center">SCANNING PROGRESS</p>
          <small>ETA 02:14:45</small>
        </Panel>
      </div>

      <div className="metrics-row">
        {metricCards.map(([label, value, icon]) => (
          <Panel className="metric-card" key={label}>
            <Icon type={icon} />
            <div>
              <p className="eyebrow">{label}</p>
              <strong>{value}</strong>
            </div>
          </Panel>
        ))}
      </div>

      <div className="dashboard-grid">
        <section className="feed-area">
          <SectionTitle meta="REFRESHING IN 5S">LIVE DISCOVERY FEED</SectionTitle>
          <div className="discovery-grid">
            {feed.map(([tag, title, depth, distance, action], index) => (
              <Panel className="discovery-card" key={title}>
                <div className={`light-curve-strip strip-${index}`}>
                  <span>{tag}</span>
                </div>
                <div className="discovery-body">
                  <div>
                    <h3>{title}</h3>
                    <p>{depth}</p>
                    <p>{distance}</p>
                  </div>
                  <a>{action}</a>
                </div>
              </Panel>
            ))}
          </div>
        </section>
        <aside className="right-stack">
          <RecentActivity />
          <SystemHealth />
        </aside>
      </div>
    </>
  );
}

function DataPoint({ label, value }) {
  return (
    <div className="data-point">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function RecentActivity() {
  const events = [
    ["cyan", "Anomaly detected in Sector 7G", "0.4s ago • SYSTEM_AI"],
    ["purple", "New planet candidate TH-102-F", "12m ago • CMD_USER_01"],
    ["muted", "Calibrating spectral array", "45m ago • SYS_MAINT"],
    ["red", "Thermal spike in Node #4", "1h ago • SENSOR_NET"],
  ];
  return (
    <Panel className="activity-panel">
      <div className="panel-heading">
        <span>RECENT ACTIVITY</span>
        <span>↻</span>
      </div>
      {events.map(([tone, title, meta]) => (
        <div className="event-row" key={title}>
          <span className={`event-dot ${tone}`} />
          <div>
            <p>{title}</p>
            <small>{meta}</small>
          </div>
        </div>
      ))}
    </Panel>
  );
}

function SystemHealth() {
  return (
    <Panel className="health-panel">
      <div className="panel-heading">
        <span>SYSTEM HEALTH</span>
        <span className="good">● OPTIMAL</span>
      </div>
      <Progress label="CPU LOAD" value="42%" amount={42} />
      <Progress label="MEM USAGE" value="8.4 / 32 GB" amount={26} />
      <Progress label="LATENCY" value="24ms" amount={12} accent="purple" />
      <button className="ghost-button" type="button">RUN DIAGNOSTICS</button>
    </Panel>
  );
}

function Progress({ label, value, amount, accent = "cyan" }) {
  return (
    <div className="progress-line">
      <div>
        <span>{label}</span>
        <span>{value}</span>
      </div>
      <i>
        <b className={accent} style={{ width: `${amount}%` }} />
      </i>
    </div>
  );
}

function DatasetBrowser() {
  const rows = [
    ["#1001", "KEPLER-186", "05", "42.0", "14.62"],
    ["#2492", "KIC 8462852", "01", "88.0", "11.88"],
    ["#3115", "KEPLER-452", "03", "31.0", "13.42"],
    ["#4021", "KOI-3010", "02", "54.0", "15.10"],
    ["#5582", "KIC 12557593", "06", "12.0", "16.02"],
    ["#6112", "KEPLER-22", "04", "76.0", "11.66"],
    ["#7001", "TRAPPIST-1", "07", "92.0", "18.80"],
    ["#8221", "KEPLER-10", "02", "65.0", "10.96"],
    ["#9004", "KIC 9832227", "00", "22.0", "12.45"],
    ["#1042", "KOI-1843", "01", "48.0", "14.21"],
  ];
  return (
    <>
      <ScreenHeader
        eyebrow="STATUS: LIVE UPLINK"
        title="Dataset Alpha: Kepler Candidates"
        actions={["EXPORT CSV", "SYNC DATABASE"]}
      />
      <div className="dataset-layout">
        <Panel className="filter-panel">
          <h3>FILTER PARAMETERS</h3>
          <Field label="KEPLER ID / OBJECT NAME" value="Search ID..." muted />
          <Field label="MAGNITUDE RANGE" value="8.0 - 16.5" />
          <div className="two-col">
            <Field label="RA (DEG)" value="290.0" />
            <Field label="DEC (DEG)" value="40.0" />
          </div>
          <Toggle label="CONFIRMED ONLY" active />
          <Toggle label="HIGH S/N FILTER" />
          <div className="telemetry">
            <h4>UPLINK TELEMETRY</h4>
            <DataPoint label="DATA_PACKETS" value="82,491" />
            <DataPoint label="LATENCY" value="12ms" />
          </div>
        </Panel>
        <Panel className="table-panel">
          <div className="table-grid table-head">
            <span>ID</span><span>KEPLER NAME</span><span>CANDIDATES</span><span>SNR</span><span>MAGNITUDE</span><span>ACTION</span>
          </div>
          {rows.map((row) => (
            <div className="table-grid" key={row[0]}>
              <span>{row[0]}</span>
              <span><strong>{row[1]}</strong><small>REF: SECTOR_21A</small></span>
              <span>{row[2]}<small>CANDIDATES</small></span>
              <span>{row[3]}</span>
              <span>{row[4]}</span>
              <button type="button">VIEW</button>
            </div>
          ))}
        </Panel>
      </div>
    </>
  );
}

function LightCurveViewer() {
  return (
    <>
      <ScreenHeader
        eyebrow="TABBY'S STAR [KIC 8462852]"
        title="LIVE TELEMETRY FEED"
        subtitle="COORD: 20h 06m 15.457s, +44° 27′ 24.61″"
        actions={["MARK AS CANDIDATE", "FLAG AS NOISE"]}
      />
      <div className="curve-layout">
        <Panel className="curve-main">
          <div className="panel-heading">
            <span>FLUX VS. TIME (BJD)</span>
            <span>NORM_FLUX: 1.000</span>
          </div>
          <div className="chart-line large">
            <svg viewBox="0 0 760 340" role="img" aria-label="Flux chart">
              <path d="M0 176 C70 166 104 183 154 174 S260 168 312 174 S406 181 454 171 S552 166 612 176 S700 184 760 174" />
              <path className="dip" d="M475 170 C492 232 531 234 548 171" />
              <line x1="486" y1="30" x2="486" y2="320" />
              <line x1="548" y1="30" x2="548" y2="320" />
            </svg>
            <div className="axis-labels"><span>BJD 2454833</span><span>BJD 2456424</span></div>
          </div>
        </Panel>
        <div className="curve-side">
          <Panel>
            <h3>TRANSIT ZOOM ALPHA-1</h3>
            <div className="mini-curve" />
            <DataPoint label="DIP_DEPTH" value="-22%" />
          </Panel>
          <Panel>
            <h3>PHASE FOLDED ANALYSIS</h3>
            <DataPoint label="PERIOD" value="UNSTABLE/VARIABLE" />
            <DataPoint label="DURATION" value="4.82 DAYS" />
            <DataPoint label="L-CURVE NOISE" value="0.012 RMS" />
            <DataPoint label="S/N RATIO" value="42.1 [HIGH]" />
          </Panel>
        </div>
      </div>
      <div className="three-grid">
        <Panel><h3>STAR METADATA</h3><MetaList /></Panel>
        <Panel><h3>PARALLAX MAP</h3><div className="map-grid" /></Panel>
        <Panel><h3>SESSION LOGS</h3><LogList /></Panel>
      </div>
    </>
  );
}

function AiPredictor() {
  return (
    <>
      <ScreenHeader
        eyebrow="SYSTEMS / TIC-420951.01 / PREDICTION ANALYSIS"
        title="Target Candidate Analysis"
        actions={["SCANNING ACTIVE", "EXPORT RAW DATA"]}
      />
      <div className="ai-layout">
        <Panel className="probability-panel">
          <div className="big-prob">98.4<span>%</span></div>
          <p>DETECTION PROB.</p>
          <small>PRED_CONF_INDEX.v4</small>
          <DataPoint label="SIGMA-5.2" value="SIGNIFICANCE" />
          <DataPoint label="0.00012" value="FALSE POS. PROB" />
        </Panel>
        <Panel className="phase-panel">
          <div className="panel-heading">
            <span>PHASE-FOLDED LIGHT CURVE</span>
            <span>PERIOD: 14.322 DAYS | DEPTH: 1.2%</span>
          </div>
          <div className="chart-line predictor">
            <svg viewBox="0 0 680 300" role="img" aria-label="Phase folded curve">
              <path d="M0 150 C80 148 130 152 190 150 C230 150 250 215 284 216 C321 217 345 151 390 150 C475 146 572 154 680 150" />
              <path className="noise" d="M0 112 L48 100 L92 126 L141 107 L204 118 L268 92 L338 126 L420 96 L506 112 L610 94 L680 120" />
            </svg>
          </div>
        </Panel>
      </div>
      <div className="ai-bottom">
        <Panel>
          <h3>MODEL RATIONALE (XAI)</h3>
          <Rationale title="Transit Shape Symmetry" impact="0.42" />
          <Rationale title="Duration Consistency" impact="0.28" />
          <Rationale title="Limb Darkening" impact="0.19" />
        </Panel>
        <Panel>
          <h3>BENCHMARK COMPARISON</h3>
          <Progress label="KEPLER-186F" value="82% Correlation" amount={82} />
          <Progress label="CURRENT TARGET" value="98.4% Prob." amount={98} />
          <Progress label="EARTH-SIM" value="64% Correlation" amount={64} accent="purple" />
        </Panel>
        <Panel className="confirm-panel">
          <h2>Validated Candidate Identified</h2>
          <p>The prediction model has exceeded the discovery threshold. Confirming this target will register it to the Global Transit Archive and initiate high-resolution spectroscopic follow-up.</p>
          <button className="outline-button" type="button">CONFIRM DISCOVERY</button>
        </Panel>
      </div>
    </>
  );
}

function ModelMetrics() {
  return (
    <>
      <ScreenHeader
        eyebrow="PERFORMANCE_METRICS_V4"
        title="NEURAL NETWORK VALIDATION PIPELINE | STATUS: OPTIMIZING"
      />
      <div className="metrics-layout">
        <Panel className="score-panel"><DataPoint label="CURRENT PRECISION" value="0.9842" /></Panel>
        <Panel className="score-panel"><DataPoint label="CURRENT RECALL" value="0.9610" /></Panel>
        <Panel className="gpu-panel">
          <h3>GPU UTILIZATION</h3>
          <Progress label="NVIDIA H100_A" value="88%" amount={88} />
          <Progress label="VRAM Allocation" value="72.4 GB" amount={72} />
          <DataPoint label="TEMPERATURE" value="64°C" />
          <DataPoint label="POWER DRAW" value="310W" />
        </Panel>
        <Panel className="matrix-panel">
          <h3>CONFUSION MATRIX (NORMALIZED)</h3>
          <div className="matrix">
            {[".96",".02",".01",".01",".04",".94",".01",".01",".02",".01",".95",".02",".10",".05",".05",".80"].map((v, i) => <span key={`${v}-${i}`}>{v}</span>)}
          </div>
          <div className="matrix-labels">EXOPLANET STAR NOISE BINARY</div>
        </Panel>
        <Panel className="pr-panel">
          <div className="panel-heading"><span>PRECISION-RECALL TRAJECTORY</span><span>AUC: 0.9892</span></div>
          <div className="chart-line precision"><svg viewBox="0 0 460 260"><path d="M28 220 C104 136 178 88 260 58 C330 34 402 26 440 22" /></svg></div>
        </Panel>
        <Panel className="console-panel">
          <h3>CONSOLE_LOG</h3>
          <LogLines />
        </Panel>
      </div>
    </>
  );
}

function SettingsPage() {
  return (
    <>
      <ScreenHeader
        eyebrow="SYSTEM CONFIGURATION"
        title="Parameters & Mission Settings"
        subtitle={"Adjust mission-critical telemetry filters, account permissions, and orbital data synchronization protocols."}
      />
      <div className="settings-grid">
        <Panel>
          <h3>Mission Parameters</h3>
          <Toggle label="LIVE_LINK_ACTIVE" active />
          <Field label="PRIMARY DATA SOURCE" value="James Webb (JWST)" />
          <Field label="TESS (Transiting Exoplanet Survey Satellite)" value="SELECTED" />
          <Progress label="DETECTION SENSITIVITY" value="0.85 σ" amount={85} />
          <Progress label="CONFIDENCE_SCORE" value="92%" amount={92} />
        </Panel>
        <Panel className="profile-card">
          <div className="avatar">VK</div>
          <h3>Commander V. Kaelum</h3>
          <p>SECTOR LEAD // KEPLER-90 CLUSTER</p>
          <DataPoint label="DESIGNATION" value="CMD-2049-ALPHA" />
          <DataPoint label="AFFILIATION" value="ISA / EXODATA" />
          <button className="outline-button" type="button">UPDATE PROFILE</button>
          <span className="level">LVL 42</span>
        </Panel>
        <Panel className="hub-panel">
          <h3>External Intelligence Hub</h3>
          <Connector name="KEPLER_ARCHIVE" status="DISCONNECTED" action="CONNECT" />
          <Connector name="TESS_STREAM" status="ACTIVE" action="MANAGE" />
          <Connector name="GAIA_MAPPING" status="ACTIVE" action="MANAGE" />
        </Panel>
        <Panel>
          <h3>Interface & Comms</h3>
          <Toggle label="Candidate Proximity Alerts" active />
          <Toggle label="Dark Site Mode" active />
          <Field label="TELEMETRY REFRESH RATE" value="REAL_TIME (500ms)" />
          <Field label="DEFAULT COORDINATE SYSTEM" value="EQUATORIAL (J2000)" />
          <div className="button-row">
            <button className="ghost-button" type="button">DISCARD CHANGES</button>
            <button className="outline-button" type="button">COMMIT CONFIGURATION</button>
          </div>
        </Panel>
      </div>
      <footer className="telemetry-footer">UPLINK_STABLE&nbsp;&nbsp; LATENCY: 42ms&nbsp;&nbsp; PACKETS: 14,029,482&nbsp;&nbsp; DROPPED: 0.00%</footer>
    </>
  );
}

function ScreenHeader({ eyebrow, title, subtitle, actions = [] }) {
  return (
    <div className="screen-header">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        {subtitle && <p className="subtitle">{subtitle}</p>}
      </div>
      {actions.length > 0 && (
        <div className="button-row">
          {actions.map((action) => <button className="outline-button" type="button" key={action}>{action}</button>)}
        </div>
      )}
    </div>
  );
}

function Field({ label, value, muted = false }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input readOnly value={value} className={muted ? "muted" : ""} />
    </label>
  );
}

function Toggle({ label, active = false }) {
  return (
    <div className="toggle-row">
      <span>{label}</span>
      <i className={active ? "active" : ""}><b /></i>
    </div>
  );
}

function MetaList() {
  return (
    <div className="meta-list">
      <DataPoint label="TYPE" value="F3 V" />
      <DataPoint label="RADIUS (R☉)" value="1.58 ±0.05" />
      <DataPoint label="TEMPERATURE (K)" value="6750 ±140" />
      <DataPoint label="SURFACE GRAVITY (LOG G)" value="4.0 ±0.02" />
      <DataPoint label="DISTANCE (LY)" value="1,470" />
    </div>
  );
}

function LogList() {
  return (
    <div className="log-list">
      <p>14:40:02 // AUTOMATED_SCRUB</p>
      <small>DIP_DETECTION_ID: 8829 | SIGMA: 5.4</small>
      <p>14:38:15 // AI_CLASSIFIER</p>
      <small>PROBABILITY: 0.94 NON-PLANETARY</small>
      <p>14:30:00 // TELEMETRY_SYNC</p>
      <small>MAST_ARCHIVE_FETCH_SUCCESS</small>
    </div>
  );
}

function Rationale({ title, impact }) {
  return (
    <article className="rationale">
      <div><strong>{title}</strong><span>Impact: {impact}</span></div>
      <p>The profiles align with planetary occlusion models and remain inside validation tolerance.</p>
    </article>
  );
}

function Connector({ name, status, action }) {
  return (
    <div className="connector-row">
      <div>
        <strong>{name}</strong>
        <p>Direct access to orbital telemetry and archive synchronization.</p>
      </div>
      <span className={status === "ACTIVE" ? "good" : "warn"}>{status}</span>
      <button className="ghost-button" type="button">{action}</button>
    </div>
  );
}

function LogLines() {
  return (
    <div className="console-lines">
      <p>TRANSIT_HUNTER_SYSTEM_DAEMON_v4.2.1</p>
      <p>[14:42:01] INFO: Initializing epoch 842...</p>
      <p>[14:42:05] SUCCESS: Gradient descent converged at 1.4e-6</p>
      <p>[14:42:08] WARNING: Cluster node 12 reporting high latency (45ms)</p>
      <p>[14:42:12] INFO: Checkpoint saved at /models/v4.0/weights_epoch_842.pt</p>
      <p>[14:42:15] INFO: Validation accuracy improved +0.002%</p>
      <p>[14:42:20] ACTION: Re-balancing dataset alpha due to class drift...</p>
      <p>[14:42:25] INFO: Scanning next batch of 4,096 light curves...</p>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
