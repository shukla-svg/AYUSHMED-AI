import { useState } from "react";
import "./App.css";

type Page = "home" | "assessment" | "auth";

function App() {
  const [page, setPage] = useState<Page>("home");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");

  if (page === "auth") {
    return (
      <div className="app auth-page">
        <header className="navbar">
          <div className="brand">
            <div className="brand-logo">A</div>

            <div>
              <h1>AYUSHMED AI</h1>
              <p>AI Health Screening Assistant</p>
            </div>
          </div>

          <button
            className="nav-link-btn"
            onClick={() => setPage("home")}
          >
            Home
          </button>
        </header>

        <main className="auth-container">
          <section className="auth-card">
            <div className="assessment-icon">✦</div>

            <span className="badge">
              {authMode === "login" ? "WELCOME BACK" : "CREATE ACCOUNT"}
            </span>

            <h2>
              {authMode === "login"
                ? "Welcome back."
                : "Create your account."}
            </h2>

            <p className="auth-description">
              {authMode === "login"
                ? "Sign in to access your assessments and health history."
                : "Create an account to securely keep your assessments and personal history."}
            </p>

            {authMode === "register" && (
              <div className="form-group">
                <label htmlFor="name">Full Name</label>

                <input
                  id="name"
                  type="text"
                  placeholder="Enter your full name"
                />
              </div>
            )}

            <div className="form-group">
              <label htmlFor="email">Email Address</label>

              <input
                id="email"
                type="email"
                placeholder="Enter your email"
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>

              <input
                id="password"
                type="password"
                placeholder="Enter your password"
              />
            </div>

            {authMode === "register" && (
              <div className="form-group">
                <label htmlFor="confirm-password">
                  Confirm Password
                </label>

                <input
                  id="confirm-password"
                  type="password"
                  placeholder="Confirm your password"
                />
              </div>
            )}

            <button className="primary-btn auth-btn">
              {authMode === "login" ? "Sign In →" : "Create Account →"}
            </button>

            <div className="auth-switch">
              <span>
                {authMode === "login"
                  ? "Don't have an account?"
                  : "Already have an account?"}
              </span>

              <button
                onClick={() =>
                  setAuthMode(
                    authMode === "login" ? "register" : "login"
                  )
                }
              >
                {authMode === "login" ? "Create account" : "Sign in"}
              </button>
            </div>

            <div className="disclaimer">
              <span>🔒</span>
              Your health information will require secure access.
            </div>
          </section>
        </main>
      </div>
    );
  }

  if (page === "assessment") {
    return (
      <div className="app">
        <header className="navbar">
          <div className="brand">
            <div className="brand-logo">A</div>

            <div>
              <h1>AYUSHMED AI</h1>
              <p>AI Health Screening Assistant</p>
            </div>
          </div>

          <button
            className="nav-link-btn"
            onClick={() => setPage("home")}
          >
            Home
          </button>
        </header>

        <main className="assessment-page">
          <button
            className="back-btn"
            onClick={() => setPage("home")}
          >
            ← Back to Home
          </button>

          <section className="assessment-card">
            <div className="assessment-icon">✦</div>

            <span className="badge">
              AI HEALTH ASSESSMENT
            </span>

            <h2>Tell us what you're feeling.</h2>

            <p>
              Describe your symptoms naturally in any language
              supported by AYUSHMED AI. Explain your problem just
              like you would talk to a doctor.
            </p>

            <textarea
              className="symptom-input"
              placeholder="Example: Mujhe 3 din se fever hai aur raat ko khansi hoti hai..."
              rows={6}
            />

            <div className="input-info">
              <span>🌐 Multilingual input</span>
              <span>🔒 Private assessment</span>
            </div>

            <button className="primary-btn assessment-btn">
              Continue Assessment →
            </button>

            <div className="disclaimer">
              <span>✓</span>
              Preliminary screening support only — not a medical
              diagnosis.
            </div>
          </section>
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      {/* Navbar */}
      <header className="navbar">
        <div className="brand">
          <div className="brand-logo">A</div>

          <div>
            <h1>AYUSHMED AI</h1>
            <p>AI Health Screening Assistant</p>
          </div>
        </div>

        <nav className="nav-links">
          <a href="#features">Features</a>
          <a href="#how-it-works">How it works</a>

          <button
            className="nav-login-btn"
            onClick={() => {
              setAuthMode("login");
              setPage("auth");
            }}
          >
            Login
          </button>
        </nav>
      </header>

      {/* Hero */}
      <main className="hero">
        <section className="hero-content">
          <div className="badge">
            <span className="pulse"></span>
            AI-POWERED HEALTH SCREENING
          </div>

          <h2>
            Your symptoms.
            <br />
            <span>Understood naturally.</span>
          </h2>

          <p className="hero-description">
            Describe what you're experiencing in your own words
            and in a supported language. AYUSHMED AI is designed
            to understand symptoms, ask relevant follow-up
            questions and provide preliminary screening support.
          </p>

          <div className="hero-buttons">
            <button
              className="primary-btn"
              onClick={() => setPage("assessment")}
            >
              Start Health Assessment →
            </button>

            <a className="text-btn" href="#how-it-works">
              See how it works
            </a>
          </div>

          <div className="trust-row">
            <div>
              <strong>🌐</strong>
              <span>Multilingual</span>
            </div>

            <div>
              <strong>🧠</strong>
              <span>AI-assisted</span>
            </div>

            <div>
              <strong>🛡️</strong>
              <span>Safety-first</span>
            </div>
          </div>
        </section>

        {/* AI Preview */}
        <section className="ai-preview">
          <div className="preview-glow"></div>

          <div className="chat-card">
            <div className="chat-top">
              <div className="ai-avatar">✦</div>

              <div>
                <strong>AYUSHMED AI</strong>
                <p>Health Assistant • Online</p>
              </div>

              <div className="online-dot"></div>
            </div>

            <div className="chat-status">
              <span>AI is ready to understand your symptoms</span>
            </div>

            <div className="chat-messages">
              <div className="message ai">
                Hello! 👋
                <br />
                Tell me what you're experiencing.
              </div>

              <div className="message user">
                Mujhe 3 din se bukhar hai aur raat ko bahut khansi
                hoti hai.
              </div>

              <div className="message ai">
                I understand. When did the fever start, and are
                you experiencing any breathing difficulty?
              </div>
            </div>

            <div className="chat-input">
              <span>Describe your symptoms...</span>

              <button
                onClick={() => setPage("assessment")}
              >
                ➤
              </button>
            </div>

            <div className="chat-footer">
              <span>🌐 Any supported language</span>
              <span>🔐 Secure</span>
            </div>
          </div>
        </section>
      </main>

      {/* Quick Features */}
      <section className="quick-features" id="features">
        <div className="quick-feature">
          <span>01</span>

          <div>
            <strong>Natural Conversation</strong>
            <p>
              Talk normally instead of selecting symptoms from
              lists.
            </p>
          </div>
        </div>

        <div className="quick-feature">
          <span>02</span>

          <div>
            <strong>Smart Follow-ups</strong>
            <p>
              Relevant questions based on what you tell the
              system.
            </p>
          </div>
        </div>

        <div className="quick-feature">
          <span>03</span>

          <div>
            <strong>Safety Layer</strong>
            <p>
              Potential red flags are considered before
              screening.
            </p>
          </div>
        </div>

        <div className="quick-feature">
          <span>04</span>

          <div>
            <strong>Personal History</strong>
            <p>
              Previous assessments can be available to your
              account.
            </p>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="features-section">
        <div className="section-heading">
          <span>ONE PLATFORM</span>

          <h2>More than a symptom checker.</h2>

          <p>
            AYUSHMED AI combines conversational interaction,
            screening, mental-health assessment and personal
            health history.
          </p>
        </div>

        <div className="features">
          <div className="feature-card featured-card">
            <div className="feature-icon">💬</div>

            <h3>Conversational Symptoms</h3>

            <p>
              Explain your symptoms naturally. The system is
              designed to extract symptoms, duration, severity
              and context.
            </p>

            <span className="feature-link">
              Explore assessment →
            </span>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🧠</div>

            <h3>Mental Health</h3>

            <p>
              Dedicated PHQ-9 and GAD-7 assessment modules can
              support structured mental-health screening.
            </p>

            <span className="feature-link">
              Mental assessment →
            </span>
          </div>

          <div className="feature-card">
            <div className="feature-icon">📋</div>

            <h3>Assessment History</h3>

            <p>
              Logged-in users can view previous conversations
              and assessment results in one place.
            </p>

            <span className="feature-link">
              View history →
            </span>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🔐</div>

            <h3>Privacy & Security</h3>

            <p>
              User accounts and health information will be
              designed with privacy and secure access in mind.
            </p>

            <span className="feature-link">
              Learn about safety →
            </span>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="how-section" id="how-it-works">
        <div className="section-heading">
          <span>HOW IT WORKS</span>

          <h2>From conversation to screening support.</h2>
        </div>

        <div className="steps">
          <div className="step">
            <div className="step-number">01</div>

            <h3>Describe</h3>

            <p>
              Tell AYUSHMED AI what you're experiencing in
              natural language.
            </p>
          </div>

          <div className="step">
            <div className="step-number">02</div>

            <h3>Understand</h3>

            <p>
              NLP can identify symptoms, duration, severity and
              relevant context.
            </p>
          </div>

          <div className="step">
            <div className="step-number">03</div>

            <h3>Check Safety</h3>

            <p>
              Red-flag information is considered before
              ordinary screening.
            </p>
          </div>

          <div className="step">
            <div className="step-number">04</div>

            <h3>Screen</h3>

            <p>
              A medically evaluated model can provide
              preliminary screening support.
            </p>
          </div>
        </div>
      </section>

      {/* Safety */}
      <section className="safety-section">
        <div className="safety-content">
          <span className="safety-label">RESPONSIBLE AI</span>

          <h2>
            Technology can assist.
            <br />
            Doctors make decisions.
          </h2>

          <p>
            AYUSHMED AI is designed for preliminary screening
            support. It does not replace qualified healthcare
            professionals, provide emergency care or
            independently prescribe medicines.
          </p>
        </div>

        <div className="safety-card">
          <div className="safety-icon">🛡️</div>

          <h3>Safety-first architecture</h3>

          <div className="safety-item">
            <span>✓</span>
            <p>Red-flag screening</p>
          </div>

          <div className="safety-item">
            <span>✓</span>
            <p>Transparent limitations</p>
          </div>

          <div className="safety-item">
            <span>✓</span>
            <p>Human professional oversight</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div>
          <strong>AYUSHMED AI</strong>

          <p>
            AI-Based Medical Symptom Analyzer and Mental Health
            Assessment System
          </p>
        </div>

        <div className="footer-meta">
          <span>Academic Project • 2026</span>
          <span>Screening support only</span>
        </div>
      </footer>
    </div>
  );
}

export default App;